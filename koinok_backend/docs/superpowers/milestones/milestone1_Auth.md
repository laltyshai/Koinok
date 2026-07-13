Here is the highly explicit, file-by-file execution plan for **Milestone 1**.

Since you plan to migrate to Firebase in the future, this plan is structured to keep authentication strictly isolated within `security.py` and `routers/auth.py`. When you eventually switch to Firebase Auth, you will only need to swap out the logic inside those two files—your database models, repositories, and other routers won't need to change at all.

---

# 📑 Superpowers Plan: Milestone 1 Execution Blueprint

## 📂 Phase 1: Environment & File Scaffolding (Step 1.1)

Create the base files with their foundational configurations.

### 1. `database.py`

* Initialize the SQLAlchemy SQLite URL: `sqlite:///./wardrobe.db`.
* Create the engine passing `connect_args={"check_same_thread": False}`.
* Configure `sessionmaker(autocommit=False, autoflush=False, bind=engine)`.
* Define the declarative `Base = declarative_base()`.
* Write the `get_db()` dependency wrapper yielding the database session context.

### 2. `main.py`

* Initialize the core `FastAPI()` application instance.
* Include basic middleware configuration (CORS settings so your Flutter app can connect locally via IP).
* Add a global health check endpoint (`GET /health`).

---

## 🗄️ Phase 2: Core Database Modeling (Step 1.2)

Translate your foundational domain entities into SQLAlchemy schemas.

### 1. `db_models.py`

* **`UserModel` Table (`users`):**
* `id`: Integer, primary key, index.
* `name`: String, nullable=False.
* `email`: String, unique=True, index=True, nullable=False.
* `hashed_password`: String, nullable=False.
* `created_at`: DateTime, default=datetime.utcnow.
* *Relationship:* `clothes = relationship("ClothModel", back_populates="owner")`.


* **`ClothModel` Table (`clothes`):**
* `id`: Integer, primary key, index.
* `user_id`: Integer, ForeignKey("users.id"), nullable=False.
* `name`: String, nullable=False.
* `category`: String, nullable=False (validated via application layer enums).
* `is_deleted`: Boolean, default=False.
* `created_at`: DateTime, default=datetime.utcnow.
* *Relationship:* `owner = relationship("UserModel", back_populates="clothes")`.



### 2. `schemas.py`

* Create data validation shapes using Pydantic v2:
* `UserRegister` (name, email, password).
* `UserLogin` (email, password).
* `UserResponse` (id, name, email, created_at).
* `Token` (access_token, token_type).



---

## 🔐 Phase 3: Cryptography & Local Auth Isolation (Step 1.3)

Implement the JWT-based security barrier. Keep this logic tightly encapsulated so it can be swapped for a Firebase token verifier later.

### 1. `security.py`

* **Password Utility:** Set up `CryptContext(schemes=["bcrypt"], deprecated="auto")`. Write `hash_password(password)` and `verify_password(plain, hashed)`.
* **Token Management:** Define token constants (`SECRET_KEY`, `ALGORITHM = "HS256"`, `ACCESS_TOKEN_EXPIRE_MINUTES`). Write `create_access_token(data: dict)`.
* **Dependency Injection (`get_current_user`):** * Use FastAPI's `OAuth2PasswordBearer(tokenUrl="auth/login")`.
* Decode incoming JWTs. If signature fails or expiration hits, raise `HTTPException(401)`.
* Query the user from the database by the email/ID stored in the payload. Return the `UserModel` object.



### 2. `routers/auth.py`

* **`POST /auth/register`**:
* Check if the email already exists in the database. If yes, raise `HTTPException(400, detail="Email already registered")`.
* Hash the password, save the new `UserModel` to the database, and return the `UserResponse` payload.


* **`POST /auth/login`**:
* Authenticate user credentials.
* If valid, generate a signed JWT access token and return the `Token` schema.


* **Architecture Integration:** Import this router into `main.py` under the `/auth` prefix.

---

## 🛠️ Verification Checklist for the AI Agent

Before marking Milestone 1 complete, the agent must perform the following validation tasks:

1. Run a script invocation creating all tables in `wardrobe.db` via `Base.metadata.create_all(bind=engine)`.
2. Boot up the local webserver using `uvicorn main:app --reload`.
3. Open the interactive Swagger UI panel at `http://127.0.0.1:8000/docs`.
4. Run a test registration via `POST /auth/register`, copy the output, and log in via `POST /auth/login` to confirm a valid JWT token is successfully issued.