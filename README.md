# spotdl_streaming_manager

A **desktop-first music discovery and download management app** built around `spotDL`, with an emphasis on:

- Batch-based library organization.
- Metadata quality and verification.
- Exclusion/blacklist workflows.
- Durable provenance (what was requested, how it was processed, and what files changed later).

> ⚠️ **Project status:** This repository is currently an **architecture scaffold + product specification**, not a feature-complete application. Most runtime modules are placeholders at this time.

---

## Why this project exists

`spotDL` is powerful but CLI-centric. This project aims to make it practical for long-lived library curation by adding a GUI, database-backed tracking, and safety workflows (reconciliation, file mutation logs, profile snapshots).

The guiding design intent in this repository is documented in:

- `spotdl_manager_authoritative_spec.md` (current governing architecture).
- `research_guidance.md` (prior broader research record).
- `sdd_for_spotdl_downloader.md` (earlier product/system ideation).

---

## Current implementation reality (critical review)

If you are evaluating this repo today, here is the candid status:

### What exists

- Python package layout for app, GUI, services, utilities, tests.
- Project metadata (`pyproject.toml`) with intended dependencies (PySide6, SQLAlchemy, Alembic, mutagen, rapidfuzz, watchdog, spotdl).
- Placeholder setup scripts and docs.

### What does **not** exist yet

- No working GUI screens.
- No database models or migrations.
- No execution engine around `spotdl` subprocess.
- No exclusion engine, metadata verifier, reconciliation logic, or playlist exporter.
- No meaningful automated tests.

### Operational implications

- You cannot currently run this as a usable app.
- The package should be treated as a **blueprint repository** awaiting implementation.
- The architectural docs are presently more complete than the codebase.

---

## Planned feature set (target product)

The intended MVP/v1 behavior, based on the authoritative specification:

1. **Batch-centric downloads**
   - Each run is tracked as a batch manifest (source URL, profile snapshot, created/completed timestamps, outcomes).
2. **Profile-driven engine settings**
   - Persisted config profiles mapped to `spotDL` config structure.
3. **Pre-download exclusion pipeline**
   - `spotdl save` metadata pass → fuzzy + ID matching → pruned execution set.
4. **Robust execution engine**
   - Background worker(s), non-blocking UI, log/progress streaming, cancellation.
5. **Post-download metadata verification**
   - `mutagen` audit for tags/art embedding consistency.
6. **Library reconciliation**
   - Detect moved/deleted files and mark degraded/archive state appropriately.
7. **Batch export artifacts**
   - `.m3u` generation and repeatable output handling.

---

## Tech stack (intended)

- **Language/runtime:** Python 3.12+
- **GUI:** PySide6
- **ORM/DB:** SQLAlchemy + SQLite (+ Alembic migrations)
- **Downloader backend:** `spotdl` via subprocess invocation
- **Metadata verification:** mutagen
- **Fuzzy matching:** rapidfuzz
- **Filesystem monitoring:** watchdog

---

## Quick start (for contributors evaluating current repo)

### 1) Clone and enter repository

```bash
git clone <repo-url>
cd spotdl_streaming_manager
```

### 2) Create environment and install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

### 3) Run available checks

```bash
python -m compileall -q .
pytest -q
```

> Note: `pytest` currently reports no runnable tests (placeholder test modules).

---

## Repository layout

```text
app/
  config.py                  # planned runtime configuration handling (stub)
  db.py                      # planned DB session/bootstrap (stub)
  models.py                  # planned ORM schema (stub)
  gui/                       # planned PySide6 presentation layer (stubs)
  services/                  # planned orchestration/business logic (stubs)
  utils/                     # planned helper utilities (stubs)
tests/                       # test module placeholders
spotdl_manager_authoritative_spec.md
research_guidance.md
sdd_for_spotdl_downloader.md
README_dev.md                # technical implementation notes for maintainers
```

---

## Roadmap (pragmatic next steps)

1. Implement real `main.py` app bootstrap (Qt app + main window lifecycle).
2. Define SQLAlchemy models and create initial Alembic migration.
3. Build execution service around `spotdl` subprocess (`save` + full run).
4. Implement exclusion engine from `.spotdl` JSON and blacklist persistence.
5. Add metadata verifier and batch playlist generation.
6. Add integration tests for core services with subprocess mocking.
7. Implement GUI flows (new batch, library, settings, blacklist, reconciliation).

---

## Legal & responsibility

- This project is MIT licensed.
- Users are responsible for complying with local laws, platform terms of service, and copyright rules.
- The intended use is personal library management and metadata organization.

