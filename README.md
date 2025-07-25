# FastDRF
FastDRF: Migrating from Django Rest Framework to FastAPI template with even more flexibility.

**FastDRF** is a clean and powerful FastAPI project template for developers migrating from Django REST Framework (DRF) to FastAPI. It provides:

- ✅ JWT authentication fully compatible with Django
- ✅ DRF-style `ViewSet` classes with automatic routing
- ✅ Modular permissions via `BasePermission` subclasses
- ✅ Automatic Pydantic schema generation from SQLAlchemy models
- ✅ PostgreSQL support
- ✅ Auto-generated Swagger and ReDoc API docs

---

## 🚀 Features

- 🔐 **JWT Auth (Access + Refresh)**: Shared token structure between Django and FastAPI. Users created in Django can log in via FastAPI and vice versa.
- ⚙️ **Custom ViewSets**: Automatically handle `GET`, `POST`, `PATCH`, `DELETE` with just a target query.
- 🛡️ **Permissions**: Create powerful and composable permissions just like in DRF.
- 📦 **Modular Structure**: Easily extensible and production-ready base architecture.
- 📄 **OpenAPI Docs**: Fully documented API via Swagger (`/docs`) and ReDoc (`/redoc`).

---

## 🧱 Requirements

- Python 3.10+
- PostgreSQL
- `.env` file (see below)

Dependencies are listed in [`requirements.txt`](./requirements.txt), including:

- `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `asyncpg`
- `alembic`, `python-dotenv`, `passlib[bcrypt]`, etc.

---

## ⚙️ Installation

### 1. Clone and enter the project:

```bash
git clone https://github.com/hooshemadhoosh/FastDRF.git
cd FastDRF
```

### 2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # or venv/Scripts/activate on Windows
```

### 3. Install dependencies:

```bash
pip install -r requirements.txt
```

### 4. Set up `.env` file:

Create a `.env` file in the root with:

```env
DB_USER=postgres
DB_PASS=your_db_password
DB_HOST=localhost
DB_PORT=5432 #Or your custom port
DB_NAME=dbname
SECRET_KEY=your_super_secret_key_in_django_project
```

### 5. Start PostgreSQL and create your database (if not done).

### 6. Run the development server:

You can easily run the server via main.py file just like a normal python program.

```bash
python main.py
```

---

## 🔑 Authentication

- `POST /auth/login`: Login using username/password
- `POST /auth/refresh`: Get new access token using refresh token
- `POST /auth/logout`: Blacklist a refresh token
- `GET /me`: Get current user info

Tokens and password hashing are fully compatible with Django:

- Uses Django-compatible hashers (`pbkdf2_sha256`)
- Auth tokens created in one framework work in the other

---

## 🧠 Usage

### Create a new ViewSet

```python
# views/product.py
class ProductViewSet(BaseViewSet):
    target_query = select(Product)
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at"]
    default_ordering = ["-created_at"]
    protect_by = IsAuthenticated & AllowAll
```

Then add it to your `views` list in `config.py`:

```python
views = [
    UserViewSet('/user',tags=["User Views"]),
    ProductViewSet('/product',tags=["Product management"])
]
```

### Define permissions

```python
class IsAdmin(BasePermission):
    @classmethod
    async def has_permission(self, user, method, **kwargs):
        return user and user.is_staff
```

Use it like:

```python
protect_by = IsAuthenticated & IsAdmin
```

---

## 🔍 API Docs

- Swagger: [http://localhost:8080/docs](http://localhost:8080/docs)
- ReDoc: [http://localhost:8080/redoc](http://localhost:8080/redoc)

---

## 🧪 Example Endpoints

| Method | Path            | Description              |
| ------ | --------------- | ------------------------ |
| GET    | `/user`         | List users               |
| GET    | `/user/{id}`    | Retrieve single user     |
| PUT    | `/user`         | Create new user          |
| PATCH  | `/user/{id}`    | Update user              |
| DELETE | `/user/{id}`    | Delete user              |
| POST   | `/auth/login`   | Login with credentials   |
| POST   | `/auth/refresh` | Refresh access token     |
| POST   | `/auth/logout`  | Logout / blacklist token |

---

## ✨ Project Structure

```
.
├── config.py          # App config & FastAPI app instance
├── database.py        # Async SQLAlchemy setup
├── models/            # SQLAlchemy models
├── permissions/       # DRF-style permission classes
├── routers/           # Auth routes, test routes
├── schemas/           # Pydantic schemas
├── views/             # DRF-like ViewSets
├── utils/             # Reusable helpers
└── requirements.txt
```

---

## 💠 Contributing

Pull requests are welcome! Feel free to fork and improve the template.
