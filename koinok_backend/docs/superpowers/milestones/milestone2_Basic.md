Here is the updated, code-free execution plan for **Milestone 2**, formatted specifically for an AI Agent to implement file-by-file with clear architectural guidance and soft-delete/restore mechanics.

---

# 📑 Superpowers Plan: Milestone 2 Execution Blueprint

## 📂 Phase 1: Schemas & Validation Layer (Step 2.1)

Define strict Pydantic v2 data models for request inputs, query results, and JSON responses.

### 1. `schemas.py` (Extensions)

* **Category Enumeration (`ClothCategory`):**
* String-based enum covering standard categories: `top`, `bottom`, `footwear`, `outerwear`, `accessory`, `other`.


* **`ClothBase` Schema:**
* Shared attributes: `name` (string, required, length constrained between 1 and 100 characters) and `category` (enum, defaults to `other`).


* **`ClothCreate` Schema:**
* Inherits directly from `ClothBase` without modifications.


* **`ClothUpdate` Schema:**
* Supports partial updates with optional fields: `name` (optional string) and `category` (optional enum).


* **`ClothResponse` Schema:**
* Output shape representing database state: `id` (integer), `user_id` (integer), `name` (string), `category` (enum/string), `is_deleted` (boolean), and `created_at` (datetime).
* Enable ORM compatibility configuration (`from_attributes = True`).



---

## 🗄️ Phase 2: Data Access & Repository Isolation (Step 2.2)

Encapsulate all database interaction logic within a dedicated repository layer to keep HTTP routes thin and isolate soft-delete behavior.

### 1. `repositories.py` (New File)

* **Class `ClothRepository`:**
* Accepts a SQLAlchemy `Session` instance upon initialization.


* **`create(cloth_in, user_id)`:**
* Instantiates a new `ClothModel` record attached to `user_id` with default `is_deleted=False`.
* Persists, commits, refreshes, and returns the entity.


* **`get_by_id(cloth_id, user_id, include_deleted=False)`:**
* Queries a single clothing item scoped to `user_id`.
* Conditionally filters out soft-deleted items (`is_deleted == False`) unless `include_deleted` is explicitly set to `True`.


* **`get_all_by_user(user_id, include_deleted=False)`:**
* Retrieves all items belonging to `user_id`, ordered by newest first (`created_at` descending).
* Implicity filters out soft-deleted items (`is_deleted == False`) by default.


* **`soft_delete(cloth)`:**
* Sets the target `ClothModel`'s `is_deleted` flag to `True`.
* Commits changes, refreshes, and returns the modified object.


* **`restore(cloth)`:**
* Reverts the target `ClothModel`'s `is_deleted` flag back to `False`.
* Commits changes, refreshes, and returns the restored object.



---

## 👗 Phase 3: API Routing & User Isolation (Step 2.3)

Build protected API endpoints for closet management using FastAPI dependencies for authorization and database session lifecycle.

### 1. `routers/wardrobe.py` (New File)

* **Router Configuration:**
* Define an `APIRouter` with prefix `/clothes` and tag `Wardrobe`.


* **`POST /clothes/` (Create Item):**
* Protected by `get_current_user` dependency.
* Accepts a `ClothCreate` payload.
* Delegates creation to `ClothRepository` using `current_user.id` and returns `ClothResponse` with HTTP status `201 Created`.


* **`GET /clothes/` (List Closet):**
* Protected by `get_current_user` dependency.
* Fetches all active (non-deleted) items belonging to the authenticated user.
* Returns a list of `ClothResponse` objects.


* **`GET /clothes/{cloth_id}` (Get Specific Item):**
* Protected by `get_current_user` dependency.
* Fetches the item by ID. Raises `HTTPException(404)` if the item doesn't exist or is soft-deleted.


* **`DELETE /clothes/{cloth_id}` (Soft Delete Item):**
* Protected by `get_current_user` dependency.
* Fetches the active item. Raises `HTTPException(404)` if not found or already deleted.
* Invokes `soft_delete()` on the repository and returns the updated item showing `is_deleted=True`.


* **`POST /clothes/{cloth_id}/restore` (Restore Deleted Item):**
* Protected by `get_current_user` dependency.
* Queries `ClothRepository` with `include_deleted=True`. Raises `HTTPException(404)` if not found.
* Raises `HTTPException(400)` if the item is already active (not deleted).
* Invokes `restore()` on the repository and returns the updated item showing `is_deleted=False`.



### 2. `main.py` (Update)

* Import `wardrobe` router from `routers`.
* Register `wardrobe.router` on the main application instance (`app.include_router(...)`).

---

## 🛠️ Verification Checklist for the AI Agent

Before marking Milestone 2 complete, the agent must perform the following validation tasks:

1. Create a script named `smoke_test_m2.py` (or extend the existing runner) that executes the complete lifecycle using built-in Python standard libraries (`urllib`):
* Authenticate as a registered user and extract the JWT token.
* Send a `POST /clothes/` request with a JSON payload to create a new item. Confirm HTTP `201`.
* Send a `GET /clothes/` request with the `Authorization: Bearer <token>` header to verify the item appears in the user's active list.
* Send a `DELETE /clothes/{id}` request and confirm the response status is `200` with `is_deleted: true`.
* Send another `GET /clothes/` request and confirm the soft-deleted item is no longer returned in the active list.
* Send a `POST /clothes/{id}/restore` request and confirm the response returns `is_deleted: false`.
* Send a final `GET /clothes/` request to confirm the restored item is visible again.


2. Confirm that attempting to access or modify another user's items returns an appropriate authorization error or HTTP `404 Not Found`.