# Sprint 5 – UI, History, Resume, Dark Mode
**Duration:** 2 weeks
**Start:** 2025-07-02
**Goal:** Provide a minimalist web UI (HTMX + Tailwind) with dark‑mode toggle, history browsing, and resumable jobs; add JSON logging & Windows smoke‑test.

---

## Tickets

| ID | Description | Acceptance Hint |
|----|-------------|-----------------|
| **SP5‑01** | **Upload page**: HTMX form (`accept=".msi,.exe"`, textarea). POST `/v1/packages`. | Page returns 201 & redirects. |
| **SP5‑02** | **Progress page**: SSE endpoint `/v1/progress/<id>` + Tailwind progress bar. | Live bar reaches 100 %. |
| **SP5‑03** | **History table**: `/history?page=n` paginated, newest first. **Details** accordion shows metadata & re‑download button. | Pagination works; script downloads. |
| **SP5‑04** | **Dark‑mode toggle** using Tailwind’s `dark:` selector strategy. | Toggle persists via cookie. |
| **SP5‑05** | **UUID + status enum + resume loop**: add `package_id`, `status`, `stage` columns; worker resumes on app start. | Kill + restart → job continues. |
| **SP5‑06** | **Loguru JSON + PSADT log path**: centralised logs correlate `package_id`. | `logs/api.json` lines include id & path. |
| **SP5‑07** | **Windows smoke‑test**: GitHub Actions job downloads `psadt.exe`, runs on `windows-latest`, lints generated script. | Workflow passes. |

---

## Definition of Done
* Upload → Progress → Finish flow works end‑to‑end.
* History page lists previous packages; scripts view & download.
* Dark‑mode toggle persists.
* Job restarts correctly after simulated crash.
* Windows smoke‑test CI green.
