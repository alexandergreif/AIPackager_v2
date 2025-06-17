# Sprint 1 – Foundation & CRUD
**Duration:** 2 weeks  
**Goal:** Ship a working Flask backend with SQLite persistence and full CRUD for the `Package` resource.

---

## Tickets

### 🗂️ Repository & Tooling
- [ ] **SP1‑01** Initialise git repo & `.gitignore`.
- [ ] **SP1‑02** Create `requirements.in` / `requirements-dev.in`; lock with `pip-compile`.
- [ ] **SP1‑03** Add pre‑commit hooks (Ruff + Mypy).
- [ ] **SP1‑04** Add GitHub Actions CI with pip caching.

### 🏗️ Backend Skeleton
- [ ] **SP1‑05** Scaffold `api/` with `create_app()` factory and `/healthz` route.
- [ ] **SP1‑06** Configure Flask‑CORS and logging via Loguru.

### 🗄️ Database
- [ ] **SP1‑07** Define SQLAlchemy `Package` model (id, name, version, installer_path, script_text, created_at, updated_at).
- [ ] **SP1‑08** Add Alembic migration env; generate initial migration.
- [ ] **SP1‑09** Implement `infrastructure/db/session.py` context manager.

### 🔄 CRUD Endpoints
- [ ] **SP1‑10** Implement Blueprint `/v1/packages` with POST, GET(id), PUT(id), DELETE(id), LIST.
- [ ] **SP1‑11** Pydantic schemas for request/response; automatic validation.

### 🧪 Tests
- [ ] **SP1‑12** Unit tests for model serialization & DB round‑trip.
- [ ] **SP1‑13** API tests using Flask test client covering all CRUD routes.

### 📃 Docs
- [ ] **SP1‑14** Auto‑generate OpenAPI via Flask‑Pydantic; expose `/docs`.
- [ ] **SP1‑15** Update README with setup & example curl requests.

---

## Definition of Done
* All CRUD endpoints return 2xx and hit SQLite DB.
* CI pipeline (Ruff, Mypy, Pytest) passes on GitHub.
* OpenAPI available at `/docs`.
