# 👕 E-Wardrobe Backend Plan

FastAPI-based backend for a digital wardrobe organization and smart outfit suggestion system with an SQLite database.

## Features

* ✅ **JWT Authentication** - Secure token-based registration and login for users.
* ✅ **Wardrobe Management (CRUD)** - Add, view, update, and delete clothing items with specific metadata (category, color, season, temperature, tags).
* ✅ **Image Payload Handling** - Secure endpoints for handling compressed image uploads linked to specific clothing assets.
* ✅ **Smart "Suggested" Mechanic** - Dynamic calculations tracking clothes not worn in 10+ days to bring them back to rotation.
* ✅ **Randomized Outfit Recommendations** - Algorithm-based outfit generator blending suggested items and user metadata.
* ✅ **Advanced Query Filtering** - High-performance filtering across multiple tags (color, category, temperature, activity, date last worn).
* ✅ **Look/Collection Assembly** - Group separate clothing assets into a unified "Look" object (e.g., Casual Summer Set).
* ✅ **Manual Linkage System** - Explicit relational mapping allowing items to be manually paired as "matching items" (e.g., specific shorts matching a specific shirt).
* ✅ **Wear Tracking History** - Dynamic tracking calendar logging exactly when items were worn to feed the suggestion engine.
* ✅ **Personal Annotation System** - Interactive note logging and favoriting features (`isLiked`) mapped per asset.

---

## Technology Stack

* **Python:** 3.10+
* **Framework:** FastAPI
* **Database:** SQLite
* **ORM:** SQLAlchemy (with foreign key constraints for relationships)
* **Data Validation:** Pydantic v2
* **Authentication:** JWT (`python-jose`, `passlib` with bcrypt)
* **API Documentation:** OpenAPI / Swagger UI

---

## Project Structure

```text
fastapi_wardrobe/
├── main.py                     # FastAPI app setup, exception handlers & global routers
├── routers/                    # API endpoints split by domain
│   ├── auth.py                 # Registration, Login, Token generation
│   ├── wardrobe.py             # Clothes CRUD, liking, notes, matching linkages
│   ├── looks.py                # Collection management and outfit grouping
│   └── calendar.py             # Wear tracking logs and calendar queries
├── services.py                 # Core business logic (10-day logic, randomized algorithms)
├── db_models.py                # SQLAlchemy models (Users, Clothes, Looks, WearLogs)
├── schemas.py                  # Pydantic request/response validation schemas
├── repositories.py             # Data access abstraction layers (Repository pattern)
├── sqlite_repositories.py      # Concrete SQLite data manipulation implementations
├── database.py                 # SQLAlchemy engine and session dependency configurations
├── security.py                 # JWT decoding, token verification, and password hashing
├── seed.py                     # Seed script to inject basic starter clothes/categories
└── wardrobe.db                 # Local SQLite database instance

```

---

## Key Database Relationships to Implement

* **User ➡️ Clothes / Looks:** One-to-Many. Securely isolates your data from your mom's data.
* **Looks ➡️ Clothes:** Many-to-Many connection table (`look_clothes`), grouping separate clothing rows into one layout.
* **Clothes ➡️ Clothes (Matching items):** A self-referential Many-to-Many association table (`matching_clothes`) to link `cloth_id_a` to `cloth_id_b` manually.
* **Clothes ➡️ WearLogs:** One-to-Many tracking historical timestamps whenever an item is marked as worn.