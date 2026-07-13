Here is your fully updated, production-grade MVP Backend Milestone Plan for **E-Wardrobe**.

This plan integrates your core requirements with the advanced UX enhancements (Soft Deletes, Bidirectional Matching, Batch Wear Logging) into a clean **FastAPI + SQLAlchemy + Repository Pattern** architecture.

---

# 👕 E-Wardrobe: Complete MVP Backend Milestone Plan

## 🏁 Milestone 1: Foundations, Database & Auth

**Goal:** Establish the project layout, configure the SQLite engine, design core schemas, and secure the system.

### Step 1.1: Environment & Project Setup

* Initialize the repository layout matching your pet project structure (`main.py`, `database.py`, `security.py`, etc.).
* Configure the SQLAlchemy SQLite engine with `check_same_thread=False` to handle asynchronous FastAPI requests safely.

### Step 1.2: Base Database Entities (`db_models.py`)

* **User Model:** `id`, `name`, `email`, `hashed_password`, `created_at`.
* **Cloth Model:** `id`, `user_id` (FK), `name`, `category` (string/enum), `created_at`, **`is_deleted` (Boolean, default=False)** *[UX Soft Delete]*.
* *Note:* Keep the clothing attributes minimal here; structural fields will be expanded during the filtering milestone.

### Step 1.3: Authentication Routing (`routers/auth.py`)

* Implement password hashing using `passlib` with `bcrypt`.
* Expose `POST /auth/register` to onboard new profiles.
* Expose `POST /auth/login` to verify credentials and return a signed JWT token (`python-jose`).
* Write the `get_current_user` dependency to protect user data isolation across all subsequent milestones.

---

## 👗 Milestone 2: Closet Management & Resilient CRUD

**Goal:** Implement robust clothing management endpoints that protect users from accidental data loss.

### Step 2.1: Repository Layer Implementation (`repositories.py`)

* Build the `ClothRepository` interface and its concrete SQLite implementation.
* **Soft Delete Logic:** Ensure all retrieval queries implicitly filter out items where `is_deleted == True`.

### Step 2.2: Schemas & Validation (`schemas.py`)

* Define `ClothCreate` (validating required fields like `name` and `category`) and `ClothResponse` Pydantic models.

### Step 2.3: API Routing (`routers/wardrobe.py`)

* `POST /clothes/` – Upload a new clothing asset.
* `GET /clothes/` – Fetch all active clothes belonging to the authenticated user.
* **`DELETE /clothes/{cloth_id}` [UX Enhanced]** – Flip the `is_deleted` flag to `True` instead of a hard database purge.
* **`POST /clothes/{cloth_id}/restore` [UX New]** – Simple endpoint to flip `is_deleted` back to `False` to empower a quick "Undo" option in Flutter.

---

## 🗓️ Milestone 3: Efficient Tracking & The 14-Day Rotation Engine

**Goal:** Track daily outfits without network overhead and calculate forgotten wardrobe inventory.

### Step 3.1: Wear History Modeling (`db_models.py`)

* Create a `WearLog` model: `id`, `cloth_id` (FK to Cloth), `worn_date` (SQLAlchemy `Date`).
* Configure the relationship so a `Cloth` document maps directly to an array of its historical logs.

### Step 3.2: Batch Tracking Endpoints (`routers/calendar.py`)

* **`POST /calendar/log-day` [UX Enhanced]** – Multi-item logger. Accepts a list of `cloth_ids` and a single `date` string (`"YYYY-MM-DD"`). Inserts multiple entries in a single transaction so the Flutter app doesn't have to cycle parallel calls for an outfit.
* `GET /calendar` – Returns a dictionary mapping historical dates to arrays of clothing objects worn on those days (e.g., `{"2026-07-13": [ClothA, ClothB]}`).

### Step 3.3: Rotation Logic & Split Statuses (`services.py`)

* Write a service algorithm `get_suggested_clothes(user_id)`.
* **The Business Logic:** Query clothes belonging to the user where:
* The most recent associated `WearLog.worn_date` is older than **(Today - 14 days)**.
* *OR* the cloth has exactly zero `WearLog` records.


* **`GET /clothes/suggested` [UX Enhanced]** – Exposes the suggestion payload to Flutter, dividing the array into two explicit sub-lists: `forgotten_favorites` (had history, but ignored) and `hidden_gems` (never worn once) to create a clean visual dashboard layout.

---

## 🔍 Milestone 4: Multi-Criteria Query Filtering

**Goal:** Allow users to instantly sweep through their closets using concrete property matrices.

### Step 4.1: Characteristics Expansion (`db_models.py`)

* Add the tracking characteristics to the `Cloth` database table: `color` (string), `season` (string), `is_oversize` (Boolean).
* Update corresponding Pydantic validation schemas to accept these traits as optional parameters.

### Step 4.2: Dynamic Repository Queries (`sqlite_repositories.py`)

* Formulate a dynamic generative query block utilizing SQLAlchemy's conditional filtering chain:
```python
query = session.query(ClothModel).filter(ClothModel.user_id == user_id, ClothModel.is_deleted == False)
if category: query = query.filter(ClothModel.category == category)
if color: query = query.filter(ClothModel.color == color)
if is_oversize is not None: query = query.filter(ClothModel.is_oversize == is_oversize)

```


* `GET /clothes/search` – Expose the multi-criteria search engine via standard FastAPI query string inputs.

---

## 🤝 Milestone 5: Bidirectional Matchmaking & Look Collections

**Goal:** Create relational structures grouping individual clothing assets together into looks or recommendations.

### Step 5.1: Automatic Bidirectional Links

* Define an association table `matching_clothes` containing `cloth_id` and `matched_cloth_id`.
* **`POST /clothes/{cloth_id}/match` [UX Enhanced]** – Accepts an array of targets. The repository layer inserts symmetric reciprocal matches automatically. *(If you pair Pink Shorts to a Pink Shirt, the system automatically writes the back-link so both items recognize each other instantly).*
* Update `ClothResponse` to automatically map out the list of matching clothing entity details.

### Step 5.2: Look Collections Management (`routers/looks.py`)

* Create a `Look` database table: `id`, `user_id` (FK), `name`, `created_at`.
* Create a join table `look_items`: `look_id` (FK to Look), `cloth_id` (FK to Cloth).
* `POST /looks/` – Bundle independent `cloth_ids` together into a single named look entity (e.g., *"Official Winter Set"*).
* `GET /looks/` – Fetch all saved look combinations complete with the nested data objects of the clothes contained inside them.

---

## 🛠️ Verification & Data Seeding

* Establish a standalone `seed.py` utility script.
* Inject 1 test profile and a mockup closet containing 15+ varied items of clothing (pre-populating some items with historical wear logs dating weeks back, some logged today, and some with completely blank histories).
* Spin up the local ecosystem via `uvicorn main:app --reload` and visit `[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)` to verify your endpoints before starting on the Flutter client UI!