# README_dev.md — Technical Notes for Maintainers

This document is for the author/maintainers and assumes familiarity with Python desktop apps, Qt threading, and subprocess orchestration.

---

## 1) Project state assessment (as of current repo)

### Code maturity

The repository is in a **pre-implementation scaffold phase**:

- Nearly all functional modules are stubs (single docstring placeholders).
- Existing tests are also stubs and contain no assertions.
- `main.py` is not wired to any app package code.

### What this means

The primary source of truth is currently documentation, not runtime behavior.
You should treat the codebase as a clean foundation for implementing the architecture in `spotdl_manager_authoritative_spec.md`.

---

## 2) Source-of-truth hierarchy

When ambiguity appears, apply this precedence:

1. `spotdl_manager_authoritative_spec.md` (explicitly supersedes prior docs).
2. `research_guidance.md` (useful context but contains known corrections overridden by authoritative spec).
3. `sdd_for_spotdl_downloader.md` (historical ideation and requirements narrative).

In particular, preserve the authoritative corrections:

- Use `spotdl` via subprocess (not internal Python API coupling).
- Remove invalid CLI assumptions from earlier docs.
- Strip ANSI output before parsing status lines.
- Keep clear distinction between immutable batch manifest vs mutable file state.
- Prefer profile-driven config file usage over brittle per-flag CLI string composition.

---

## 3) Current repository anatomy

```text
main.py                       # placeholder hello-world entry
app/
  __init__.py
  config.py                   # stub
  db.py                       # stub
  models.py                   # stub
  gui/
    *.py                      # all stubs
  services/
    *.py                      # all stubs
  utils/
    *.py                      # all stubs
tests/
  test_*.py                   # stubs; no tests collected
pyproject.toml                # dependencies pinned for intended architecture
setup.sh / setup.ps1          # placeholders
alembic.ini                   # placeholder
```

---

## 4) Implementation strategy (recommended order)

### Phase A — Foundation

1. **Application entrypoint**
   - Replace `main.py` with real bootstrap that initializes config paths, DB, and Qt application.
2. **Config and path contracts**
   - Create deterministic app dirs (config/database/logs/temp batches).
3. **Database models + migrations**
   - Implement schema for Batch, Track, Profile, BlacklistEntry, FileOperation.
   - Generate initial Alembic revision.

### Phase B — Core services

4. **ExecutionEngine**
   - Implement subprocess wrapper with streamed stdout/stderr.
   - Ensure environment guards: `PYTHONUNBUFFERED=1`, `TERM=dumb`.
   - Add robust ANSI stripping helper in `app/utils/ansi.py`.
5. **ConfigWriter/Profile service**
   - Serialize selected profile to temp config JSON for batch runs.
6. **ExclusionEngine**
   - Parse `.spotdl` JSON, run fuzzy + deterministic ID matching, emit pruned list + stats.
7. **MetadataVerifier**
   - Post-run mutagen checks (tags, embedded art, normalization).
8. **PlaylistExporter**
   - Generate relative `.m3u` bound to batch output.
9. **Reconciler**
   - On startup/manual trigger: verify file existence and update mutable state.

### Phase C — UI composition

10. **Main window shell**
    - Navigation and service injection.
11. **New batch wizard + live download pane**
    - URL input → profile select → run → real-time status.
12. **Library view and blacklist manager**
    - Table models, filters, batch drill-down, manual blacklist controls.
13. **Engine settings screen**
    - Profile CRUD and validation against supported config schema.

### Phase D — Hardening

14. **Automated tests**
    - Unit: exclusion matching, ansi stripping, config writing.
    - Integration: subprocess mock transcript parsing.
    - DB tests for manifest immutability + file-op mutation logging.
15. **Operational checks**
    - Logging policy, recoverable errors, user-safe messaging.

---

## 5) Non-negotiable engineering constraints

### A. Manifest immutability model

Batch execution metadata is write-once. Post-run file operations do not alter manifest identity; they append mutation records.

### B. UI responsiveness

Never run blocking subprocess or heavy filesystem scans on GUI thread.
Use workers (QThread/QRunnable) with queued signal updates.

### C. Deterministic matching keys

Prefer `spotify_uri`, then `isrc`; fuzzy text is only a helper for initial identification.

### D. Observability

Persist enough structured state to replay/debug:

- Config snapshot used for each batch.
- Raw execution logs (or normalized summaries).
- Per-track status transitions and errors.

---

## 6) Testing plan upgrade (needed)

Current tests are placeholders, so add a minimal but effective suite:

1. `tests/test_ansi.py`
   - Validate ANSI stripping on rich-like sequences.
2. `tests/test_config_writer.py`
   - Profile → JSON serialization parity checks.
3. `tests/test_exclusion_engine.py`
   - Fuzzy threshold behavior and ID precedence.
4. `tests/test_execution_engine.py`
   - Parse sample stdout transcript into progress events.
5. `tests/test_reconciler.py`
   - Missing-file detection and degraded status updates.

Use fixtures and temp dirs. Mock subprocess boundaries to keep tests deterministic.

---

## 7) Packaging/deployment reality

Given current architecture goals and dependency complexity:

- Prioritize reproducible source-based setup first (`venv` + `pip install -e .`).
- Defer binary bundling until runtime paths and FFmpeg discovery are stable.
- If/when packaging is attempted, validate with an end-to-end smoke matrix before claiming “one-click install”.

---

## 8) Suggested immediate tasks for the author

- [ ] Replace placeholders in `setup.sh` and `setup.ps1` with deterministic bootstrap logic.
- [ ] Implement real `app/config.py` + `app/utils/paths.py`.
- [ ] Create SQLAlchemy models and initial migration.
- [ ] Build minimal CLI-free internal service tests before GUI work expands.
- [ ] Add CI to run `python -m compileall -q .` and `pytest`.

---

## 9) Developer commands

```bash
# install editable package
pip install -e .

# static sanity check
python -m compileall -q .

# run tests
pytest -q
```

If `pytest -q` returns “no tests ran”, that is currently expected until real tests are implemented.

