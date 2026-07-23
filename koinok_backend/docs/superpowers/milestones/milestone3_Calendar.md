# 📑 Superpowers Plan: Milestone 3 Execution Blueprint

## 🎯 Strategic Overview & Future Expansion Considerations

Milestone 3 establishes the **Wear Analytics Engine** for E-Wardrobe. Beyond tracking what was worn on a given date, this layer sets up the foundational data structures needed for future AI features (e.g., outfit recommendations, wear frequency metrics, cost-per-wear analytics, and seasonal rotation warnings).

### 🚀 Future-Proofing Architecture Rules:

1. **Timezone Safety:** All dates must be normalized to standard ISO calendar format (`YYYY-MM-DD`) at the application layer to prevent timezone shifts between Flutter clients and SQLite/PostgreSQL storage.
2. **De-duplication Policy:** The system must prevent duplicate logs for the same clothing item on the exact same date (an item cannot be logged twice on `2026-07-23`).
3. **Database Performance Strategy:** `WearLog` records grow linearly over time. Proper composite indexing on `(cloth_id, worn_date)` and `worn_date` must be configured early to keep query performance high as log volume scales.
4. **Soft-Delete Resilience:** Wear history queries must strictly respect the `is_deleted` flag on parent `Cloth` records to ensure deleted items do not appear in calendar views or rotation suggestions.

---

## 📂 Phase 1: Core Database Modeling & Schema Expansion (Step 3.1)

Translate wear tracking domain entities into SQLAlchemy schemas and update Pydantic validation shapes.

### 1. `db_models.py` (Extensions)

* **`WearLogModel` Table (`wear_logs`):**
* `id`: Integer, primary key, index.
* `cloth_id`: Integer, ForeignKey(`clothes.id`, ondelete="CASCADE"), nullable=False, indexed.
* `worn_date`: Date, nullable=False, indexed.
* `created_at`: DateTime, default=datetime.utcnow.
* *Composite Index:* Unique constraint on `(cloth_id, worn_date)` to prevent duplicate log entries for the same item on a single date.
* *Relationships:*
* `cloth`: Relationship back to `ClothModel`, configured with `back_populates="wear_logs"`.




* **`ClothModel` Table Updates:**
* Add relationship `wear_logs`: Relationship to `WearLogModel`, configured with `back_populates="cloth"`, `cascade="all, delete-orphan"`, and ordered by `worn_date` descending.



### 2. `schemas.py` (Extensions)

* **`WearLogBase` Schema:**
* Shared attributes: `worn_date` (Pydantic `date` object).


* **`BatchLogCreate` Schema:**
* Input payload for multi-item logging: `cloth_ids` (List of integers, minimum length 1) and `worn_date` (Pydantic `date` object).


* **`WearLogResponse` Schema:**
* Output shape: `id` (integer), `cloth_id` (integer), `worn_date` (date), `created_at` (datetime).
* Enable ORM compatibility configuration (`from_attributes = True`).


* **`CalendarDayResponse` Schema:**
* Mapping shape representing an outfit on a specific date: `date` (date) and `items` (List of `ClothResponse`).


* **`RotationSuggestionsResponse` Schema:**
* Output structure for the 14-day rotation dashboard split into two distinct sub-lists:
* `forgotten_favorites`: List of `ClothResponse` (items worn in the past, but not within the last 14 days).
* `hidden_gems`: List of `ClothResponse` (items with zero wear logs).





---

## 🗄️ Phase 2: Data Access & Business Logic Isolation (Step 3.2 & 3.3)

Implement dedicated repository methods and isolated service functions to process wear history and rotation analytics.

### 1. `repositories.py` (Extensions)

* **Class `WearLogRepository`:**
* Accepts a SQLAlchemy `Session` instance upon initialization.


* **`batch_log_day(cloth_ids, user_id, worn_date)`:**
* Validates that all supplied `cloth_ids` exist, belong to `user_id`, and are active (`is_deleted == False`).
* Fetches existing logs for those items on `worn_date` to prevent duplicate insertions.
* Performs bulk insertion of new `WearLogModel` instances within a single database transaction.
* Commits, refreshes, and returns the newly created wear log entities.


* **`get_calendar_logs(user_id, start_date=None, end_date=None)`:**
* Fetches all wear logs belonging to active `ClothModel` records for the target `user_id`.
* Accepts optional `start_date` and `end_date` filters to support month/week range queries in Flutter.
* Returns logs joined with their associated `Cloth` data, grouped or sorted chronologically by `worn_date`.


* **`get_clothes_with_latest_wear(user_id)`:**
* Executes an aggregated query that joins active user clothes with their most recent `WearLog.worn_date` (e.g., using `func.max(WearLog.worn_date)`).
* Returns a structure pairing each active `Cloth` entity with its max `worn_date` (or `None` if never worn).



### 2. `services.py` (New File - Business Logic Layer)

* **Class `RotationService`:**
* Accepts a SQLAlchemy `Session` instance upon initialization.


* **`get_suggested_clothes(user_id, threshold_days=14)`:**
* Calculates the cutoff date (`today - threshold_days`).
* Fetches all active clothes with their latest wear dates from `WearLogRepository`.
* Categorizes items into two explicit buckets:
1. **`hidden_gems`**: Active items where latest wear date is `None` (never logged).
2. **`forgotten_favorites`**: Active items where latest wear date is older than the cutoff date (`latest_wear < cutoff_date`).


* Returns a dictionary or object matching the `RotationSuggestionsResponse` schema structure.



---

## 👗 Phase 3: API Routing & API Gateway Integration (Step 3.2 & 3.3)

Expose protected API endpoints for daily outfit logging, calendar retrieval, and rotation suggestions.

### 1. `routers/calendar.py` (New File)

* **Router Configuration:**
* Define an `APIRouter` with prefix `/calendar` and tag `Calendar & Wear History`.


* **`POST /calendar/log-day` (Batch Wear Logger):**
* Protected by `get_current_user` dependency.
* Summary: "Log multiple items worn on a specific date".
* Accepts a `BatchLogCreate` payload (`cloth_ids` list and `worn_date`).
* Invokes `batch_log_day()` on `WearLogRepository`. Returns a status message and list of created `WearLogResponse` objects with HTTP status `201 Created`.


* **`GET /calendar` (Fetch Calendar Wear History):**
* Protected by `get_current_user` dependency.
* Summary: "Get historical wear logs grouped by date".
* Accepts optional query parameters `start_date` and `end_date` for client-side date range filtering.
* Constructs and returns a structured calendar map (e.g., `{"2026-07-23": [ClothA, ClothB]}`).



### 2. `routers/wardrobe.py` (Extensions)

* **`GET /clothes/suggested` (Fetch 14-Day Rotation Suggestions):**
* Protected by `get_current_user` dependency.
* Summary: "Get suggested unworn and forgotten clothes".
* Delegates analysis to `RotationService.get_suggested_clothes(current_user.id)`.
* Returns a payload matching `RotationSuggestionsResponse` containing `forgotten_favorites` and `hidden_gems`.



### 3. `main.py` (Update)

* Import `calendar` router from `routers`.
* Register `calendar.router` on the main application instance (`app.include_router(...)`).

---

## 🛠️ Verification Checklist for the AI Agent

Before marking Milestone 3 complete, the agent must perform the following validation tasks:

1. Create a script named `smoke_test_m3.py` that validates the complete wear tracking and rotation lifecycle:
* Authenticate as a registered user and obtain a JWT token.
* Ensure the user has at least 3 active clothing items created (e.g., Item A, Item B, Item C).
* **Test Batch Logging (`POST /calendar/log-day`):**
* Log Item A and Item B on today's date (`2026-07-23`). Confirm HTTP `201`.
* Log Item A on a date older than 14 days ago (e.g., `2026-07-01`). Confirm HTTP `201`.


* **Test Calendar Retrieval (`GET /calendar`):**
* Query `/calendar` and verify today's entry contains Item A and Item B.


* **Test Rotation Engine (`GET /clothes/suggested`):**
* Verify Item C (never logged) appears inside the `hidden_gems` list.
* Verify an item whose only wear log is older than 14 days appears inside the `forgotten_favorites` list.
* Verify items logged within the last 14 days do **not** appear in either list.


* **Test Soft-Delete Resilience:**
* Soft-delete Item C via `DELETE /clothes/{id}`.
* Query `/clothes/suggested` again and confirm Item C no longer appears anywhere in the suggestion lists.