# Project Plan – PSADT AI Agent (Backend‑First Rewrite)

**Document ID:** project_plan.md
**Last updated:** 2025-06-17

---

## 1 &nbsp;Purpose & Vision
Build a lean **backend service** that accepts text prompts describing Windows installers and returns production‑ready **PowerShell App Deployment Toolkit (PSADT v3.9+) scripts**.
The MVP must satisfy four school‑mandated pillars:

1. **Backend**: HTTP API running on Flask 3.x.
2. **Database**: Persistent store using **SQLite** (ORM: SQLAlchemy 2.x).
3. **CRUD**: Create/Read/Update/Delete endpoints for a `Package` resource that stores installer metadata and generated scripts.
4. **AI features**: Endpoint that accepts free‑form text input and responds with AI‑generated text (the PSADT script).

## 2 &nbsp;Objectives & Success Metrics

| ID | Objective | KPI |
|----|-----------|-----|
| O1 | CRUD API for `Package` resource | 100 % unit‑test coverage; POST/GET/PUT/DELETE all return 2xx |
| O2 | AI script generation endpoint (`/v1/generate`) | ≥ 95 % of returned scripts pass compliance linter |
| O3 | Persistence layer | Data survives server restart; ACID via SQLite |
| O4 | CI quality gates | Ruff + mypy + pytest all green on `main` |
| O5 | Documentation | Auto‑generated OpenAPI docs reachable at `/docs` |

## 3 &nbsp;Project Scope

### In‑Scope
* Flask backend (WSGI) with application‑factory pattern.
* SQLite DB via SQLAlchemy; Alembic for migrations.
* LLM integration (OpenAI / Anthropic) via pluggable client.
* Simple token authentication (e.g. API key header).
* GitHub Actions CI; Dependabot for dependency updates.

### Out‑of‑Scope
* Front‑end UI (CLI remains primary client).
* Multi‑tenant account system.
* Non‑SQLite RDBMS.

## 4 &nbsp;Architecture Overview

```
ai_psadt_agent/
├─ api/                    # Flask Blueprints + main create_app()
│   └─ routes/
├─ services/               # Business & AI logic (no Flask)
├─ domain_models/          # Pydantic + SQLAlchemy models
├─ infrastructure/
│   ├─ db/                 # session manager & migrations
│   └─ logging/
├─ cli/                    # Typer commands (optional client)
└─ tests/
```

* Both **CLI** and **API** import from `services/`, ensuring single‑source business rules.
* AI generation service wraps the LLM API; swap providers via env variable.

## 5 &nbsp;Technology Stack

| Layer | Choice |
|-------|--------|
| Web framework | **Flask 3.1** |
| ORM | **SQLAlchemy 2.0** + **Alembic** |
| Database | **SQLite 3** (file‑based) |
| AI | OpenAI GPT‑4o (default) behind adapter |
| Env & deps | `requirements*.txt` locked with **pip‑tools** |
| Lint/Format | **Ruff** (`ruff` + `ruff format`) |
| Type checker | **mypy --strict** |
| Testing | Pytest 8 + pytest‑cov |
| Docs | Flask‑Pydantic OpenAPI & MkDocs for dev docs |
| CI/CD | GitHub Actions, Dependabot |

## 6 &nbsp;Timeline

| Sprint | Length | Theme | Milestones |
|--------|--------|-------|------------|
| 1 | 2 wks | Foundation & CRUD | Repo scaffold, DB models, CRUD endpoints pass tests |
| 2 | 2 wks | AI Integration | `/v1/generate` endpoint produces compliant PSADT scripts |
| 3 | 2 wks | Hardening & Release | Auth, docs, packaging, v1.0 tag |

## 7 &nbsp;Risk Register

| Risk | Mitigation |
|------|------------|
| LLM hallucinations | Retrieval‑Augmented Generation & compliance tests |
| DB locking under high load | Use WAL mode & connection pooling |
| API key leakage | Read keys from env and GitHub Actions secrets |

## 8 &nbsp;Acceptance Criteria

* All CRUD actions succeed and persist.
* `/v1/generate` returns a PSADT script passing automated linter.
* `pytest -q` returns 0; coverage ≥ 85 %.
* `ruff check .` and `mypy --strict` return 0.
* OpenAPI docs auto‑generated at `/docs`.
