# Implementation Plan — Milestone 5: Bidirectional Matchmaking & Look Collections

**Goal:** Provide an architecture and execution strategy for grouping individual clothing assets together into bidirectional recommendations (matching items) and unified outfit collections ("Looks"), while ensuring multi-tenancy security and data consistency.

---

## 🏗️ Architectural Overview & Guidelines

1. **Layered Architecture:** Adhere strictly to the established Clean Layered Architecture (`routers/` -> `services/` / `repositories/` -> `db_models.py`). Routers must handle HTTP serialization/validation via Pydantic, delegating business and data logic to the repository or service layers.
2. **User Isolation & Security:** All queries fetching, creating, linking, or deleting records must validate that every involved clothing item and look collection belongs to the currently authenticated user (`user_id == current_user.id`).
3. **No Code Rule:** The AI agent must follow these explicit directives to generate implementation logic without deviating from established project conventions.

---

## 📋 Execution Steps

### Phase 1: Automatic Bidirectional Matchmaking (Step 5.1)

#### 1. Database Association Table (`db_models.py`)

* **Objective:** Establish a self-referential many-to-many relationship for clothing items.
* **Association Table Schema (`matching_clothes`):**
* `cloth_id`: Foreign Key pointing to `clothes.id` (Primary Key component, On Delete CASCADE).
* `matched_cloth_id`: Foreign Key pointing to `clothes.id` (Primary Key component, On Delete CASCADE).


* **Model Configuration:**
* Define a self-referential relationship on `ClothModel` using the `matching_clothes` secondary table.
* Ensure cascading behaviors do not orphan association records when a cloth item is deleted.



#### 2. Schema Updates (`schemas.py`)

* **Objective:** Expand request and response schemas to handle matching relationships.
* **Schema Modifications:**
* **`ClothMatchRequest`:** Pydantic model accepting a list of target clothing IDs (`matched_cloth_ids: List[int]`).
* **`ClothResponse`:** Update the output payload to include a list of simplified matching clothing items or IDs (`matching_clothes: List[...]`) so clients can render paired items instantly.



#### 3. Repository Layer Logic (`repositories.py` / `sqlite_repositories.py`)

* **Objective:** Enforce automatic bidirectional symmetry at the data layer.
* **Symmetry Algorithm:**
* When linking `Cloth A` to `Cloth B`:
1. Verify both `Cloth A` and `Cloth B` exist, are not soft-deleted (`is_deleted == False`), and belong to the authenticated user.
2. Add the relationship pair (`Cloth A` $\rightarrow$ `Cloth B`).
3. Automatically write the reciprocal link (`Cloth B` $\rightarrow$ `Cloth A`) in the same database transaction.
4. Avoid duplicate pairs if the link already exists.


* When unlinking items, ensure reciprocal removal is handled symmetrically.



#### 4. API Route Execution (`routers/clothes.py` / `routers/wardrobe.py`)

* **Objective:** Expose the matchmaking endpoint over HTTP POST.
* **Endpoint Details:**
* **HTTP Route:** `POST /clothes/{cloth_id}/match`
* **Authentication:** Protected by `get_current_user` dependency.
* **Request Body:** `ClothMatchRequest`
* **Behavior:**
* Validate that the target `cloth_id` in the URL path belongs to the active user.
* Reject operations attempting to link an item to itself.
* Delegate symmetrical link creation to the repository layer.
* Return an updated `ClothResponse` showing the refreshed list of matches.





---

### Phase 2: Look Collections Management (Step 5.2)

#### 1. Database Schema & Join Table (`db_models.py`)

* **Objective:** Model outfit combinations consisting of multiple clothing items.
* **Join Table (`look_items`):**
* `look_id`: Foreign Key pointing to `looks.id` (Primary Key component, On Delete CASCADE).
* `cloth_id`: Foreign Key pointing to `clothes.id` (Primary Key component, On Delete CASCADE).


* **Look Table (`looks`):**
* `id`: Integer, Primary Key, indexed.
* `user_id`: Foreign Key pointing to `users.id`, indexed, non-nullable.
* `name`: String, non-nullable (e.g., "Official Winter Set").
* `created_at`: DateTime, defaults to current UTC time.
* **Relationships:**
* `owner`: Many-to-One pointing back to `UserModel`.
* `clothes`: Many-to-Many relationship linked via `look_items`.





#### 2. Request & Response Schemas (`schemas.py`)

* **Objective:** Define payload structures for creating and fetching Look collections.
* **Schema Declarations:**
* **`LookCreate`:** Accepts `name` (string) and `cloth_ids` (List of integers, minimum 1 item).
* **`LookResponse`:** Serializes `id`, `name`, `created_at`, and a nested list of full `ClothResponse` objects representing all items in the outfit.



#### 3. Repository Layer Implementation (`repositories.py` / `sqlite_repositories.py`)

* **Objective:** Handle transactional CRUD operations for Look collections.
* **Repository Methods:**
* **`create_look`:**
1. Accept user ID, look name, and list of target `cloth_ids`.
2. Query database to verify all provided `cloth_ids` belong to the user and are not soft-deleted.
3. Raise a validation error if any requested clothing ID is invalid, deleted, or owned by another user.
4. Construct `LookModel`, attach verified `ClothModel` instances, and commit transaction.


* **`get_user_looks`:**
1. Fetch all `LookModel` records matching `user_id == current_user.id`.
2. Ensure associated clothes in each look exclude items flagged as `is_deleted == True`.





#### 4. API Router Endpoints (`routers/looks.py`)

* **Objective:** Expose endpoints for creating and viewing Look outfits.
* **Endpoints:**
* **`POST /looks/`**
* **Summary:** Bundle independent clothing items into a single named Look object.
* **Payload:** `LookCreate`
* **Response:** `LookResponse` (HTTP 201 Created)


* **`GET /looks/`**
* **Summary:** Retrieve all saved Look collections for the authenticated user.
* **Response:** `List[LookResponse]` (HTTP 200 OK)





---

## 🧪 Quality Assurance & Acceptance Criteria

1. **Bidirectional Symmetry Verification:**
* Linking Item A to Item B via `POST /clothes/A/match` must automatically cause Item B's detailed GET payload (`GET /clothes/B`) to display Item A in its matching list without needing a separate manual link call for B.


2. **Multi-Tenancy Security Guard:**
* Attempting to link a clothing item owned by User 1 to an item owned by User 2 must return an HTTP 404/403 error.
* Creating a Look containing clothing IDs belonging to another user must be rejected entirely.


3. **Soft-Delete Resilience:**
* Soft-deleted clothing items (`is_deleted == True`) must automatically be excluded from reciprocal match results and nested Look payloads.


4. **Self-Linking Prohibition:**
* Linking an item to itself (`cloth_id == matched_cloth_id`) must trigger a validation error (HTTP 400 Bad Request).


5. **OpenAPI / Documentation Verification:**
* Validate that `/docs` correctly displays endpoints under the designated tags, with full schema models for `LookCreate`, `LookResponse`, and `ClothMatchRequest`.