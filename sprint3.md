# Sprint 3 – Hardening & Release
**Duration:** 2 weeks
**Goal:** Polish the service for submission: auth, docs, packaging, release.

---

## Tickets

### 🔒 Security & Auth
- [ ] **SP3‑01** Rate‑limit AI endpoint (Flask‑Limiter).
- [ ] **SP3‑02** Rotate API key via env; document in README.

### 📈 Observability
- [ ] **SP3‑03** Structured JSON logs toggle via env.
- [ ] **SP3‑04** Add Prometheus metrics route `/metrics`.

### 🚀 Packaging
- [ ] **SP3‑05** Build standalone executable with shiv for Windows.
- [ ] **SP3‑06** Write `scripts/run_server.ps1` helper.

### 🧑‍🏫 Documentation
- [ ] **SP3‑07** Finish MkDocs site (`/site`).
- [ ] **SP3‑08** Record demo screencast (≤ 5 min) and link from README.

### 💡 Quality Gates
- [ ] **SP3‑09** Mutation tests with mutmut; threshold ≥ 60 % survival.
- [ ] **SP3‑10** Static security scan with Bandit & Safety in CI.

### 🚢 Release
- [ ] **SP3‑11** Tag `v1.0.0` and publish GitHub release with binary asset.
- [ ] **SP3‑12** Prepare submission bundle for school (ZIP with code, docs, demo).

---

## Definition of Done
* Binary build runs on clean Windows VM and successfully generates a PSADT script.
* CI green; metrics endpoint visible; docs complete.
