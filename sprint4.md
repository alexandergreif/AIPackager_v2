# Sprint 4 – Structured Generation & Switch KB
**Duration:** 2 weeks
**Start:** 2025-06-18
**Goal:** Deterministic PSADT generation that always uses the toolkit’s template, backed by a silent‑switch knowledge‑base.

---

## Tickets

| ID | Description | Acceptance Hint |
|----|-------------|-----------------|
| **SP4‑02** | **Chroma importer & query util**: load YAML plus docs to in‑proc Chroma; expose `find_switches(product_name, exe)` helper. | `find_switches` returns list ≠ ∅ for fixture apps. |
| **SP4‑03** | **Pydantic schema + OpenAI function‑call**: define `Command`, `Section`, `PSADTScript`; call GPT‑4o with `function_call` and validate JSON. | Unit test validates JSON → Pydantic without error. |
| **SP4‑04** | **Jinja renderer + unit tests**: inject validated JSON into Deploy‑Application.ps1 stub (template lives in `templates/Deploy-Application.ps1.j2`). | Rendered script passes compliance linter for MSI & Inno fixtures. I have not the final template yet. Just pass the commands you would use for installation in a empty file called deploy-application.ps1. |

---

## Definition of Done
* `script_generator.py` produces a validated PSADT script for three fixture installers (MSI, Inno, Chrome EXE).
* All new unit tests pass; CI green.
