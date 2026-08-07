# Implementation Plan — Milestone 4: Multi-Criteria Query Filtering

**Goal:** Provide an architecture and execution strategy for allowing users to dynamically filter and sweep through their digital wardrobe based on concrete property matrices (`color`, `season`, `is_oversize`, and `category`).

---

## 🏗️ Architectural Overview

```
[ HTTP Client / Frontend ]
          │  (GET /clothes/search?color=...&category=...&is_oversize=...)
          ▼
┌────────────────────────────────────────────────────────┐
│ FastAPI Router (routers/clothes.py)                   │
│  - Captures optional query string parameters           │
│  - Validates security token (current user)             │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ Pydantic Validation Schemas (schemas.py)               │
│  - Validates parameter inputs & structures response    │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ Repository Layer (sqlite_repositories.py)              │
│  - Constructs dynamic SQLAlchemy query chain           │
│  - Filters by authenticated user_id & active status    │
│  - Conditionally appends criteria filters              │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ Database Table (ClothModel in db_models.py)            │
│  - Extended with: color, season, is_oversize           │
└────────────────────────────────────────────────────────┘

```

---

## 📋 Execution Steps

### Phase 1: Database & Schema Enhancements (`Step 4.1`)

#### 1. Database Model (`db_models.py`)

* **Objective:** Expand the `ClothModel` entity to store granular item attributes.
* **Fields to Add:**
* `color` (*String, indexed, nullable*): Primary color tag for quick lookups.
* `season` (*String, indexed, nullable*): Seasonal category (e.g., Summer, Winter, All-Season).
* `is_oversize` (*Boolean, nullable, default=False*): Fit characteristic flag.


* **Indexing Strategy:** Add database indexes to `color`, `season`, and `category` columns to optimize dynamic filtering queries.

#### 2. Request & Response Schemas (`schemas.py`)

* **Objective:** Ensure incoming data and outgoing responses validate the new fields.
* **Schema Updates:**
* **`ClothCreate`**: Include optional `color`, `season`, and `is_oversize` parameters for newly created items.
* **`ClothUpdate`**: Allow individual updating of these filterable traits.
* **`ClothResponse`**: Ensure output payloads serialize `color`, `season`, and `is_oversize` attributes back to the client.



---

### Phase 2: Dynamic Repository Queries & API Layer (`Step 4.2`)

#### 1. Repository Filter Engine (`sqlite_repositories.py`)

* **Objective:** Create a reusable repository method for dynamic multi-criteria search.
* **Logic Flow:**
1. Base query initializes with mandatory safety filters: `ClothModel.user_id == user_id` and `ClothModel.is_deleted == False`.
2. Dynamically append filter clauses only for criteria provided in the request payload:
* If `category` provided → append `ClothModel.category == category`
* If `color` provided → append `ClothModel.color == color`
* If `season` provided → append `ClothModel.season == season`
* If `is_oversize` provided (not `None`) → append `ClothModel.is_oversize == is_oversize`


3. Execute query execution (`.all()`) and return matching record lists.



#### 2. FastAPI Endpoint Routing (`routers/clothes.py` / `main.py`)

* **Objective:** Expose the search functionality over HTTP GET.
* **Endpoint Details:**
* **HTTP Method & Route:** `GET /clothes/search`
* **Authentication:** Require user token (`get_current_user` dependency).
* **Query Inputs:**
* `category` (*Optional[str]*)
* `color` (*Optional[str]*)
* `season` (*Optional[str]*)
* `is_oversize` (*Optional[bool]*)


* **Output Model:** `List[ClothResponse]`



---

## 🧪 Quality Assurance & Acceptance Criteria

1. **Parameter Isolation Tests:** * Searching by a single field (e.g., only `color=black`) should return all non-deleted black items belonging to the active user.
2. **Combination Matrix Tests:** * Combining parameters (e.g., `category=pants`, `color=black`, `is_oversize=true`) must apply a logical **AND** condition across all criteria.
3. **Empty Result Handling:** * Querying non-matching criteria combinations should return an empty JSON list (`[]`) with an HTTP 200 status code.
4. **Multi-Tenancy Security:** * Search results must never contain items belonging to another user, even if non-owned items match the search filters.
5. **Soft-Deletion Exclusion:** * Deleted items (`is_deleted = True`) must be excluded from search results regardless of filter parameters.