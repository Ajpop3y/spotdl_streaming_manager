# AUTHORITATIVE SPECIFICATION: spotDL Music Discovery & Library Manager
**Version:** 2.0 — Supersedes all prior documents  
**Authority:** Senior Architect Review (March 15, 2026)  
**For:** Autonomous Agent Implementation  

> **Mandate:** The prior documents (SDD + Research Guidance) establish a sound conceptual foundation but contain specific technical errors, one critical semantic confusion, and several scope traps that will derail implementation. This document corrects, augments, and governs. Where this document conflicts with prior documents, this document wins.

---

## PART 0: CRITICAL CORRECTIONS

The following errors in prior documents must be overridden before any implementation begins.

### Correction 1 — spotDL Python API Status (WRONG in Research Guidance §1)

**Prior claim:** "No stable public Python API in v4 (old v2 Spotdl class is gone)."  
**Correct status:** The `Spotdl` class exists in v4 at `spotdl.Spotdl` and `spotdl.types.song.Song`. It is not gone — it is undocumented and unstable. Using it directly risks breakage on any minor version bump.  
**Authoritative decision:** Use `subprocess.Popen` with the spotdl executable. Do not import spotdl as a library. This is the only upgrade-resilient path.

### Correction 2 — Non-Existent CLI Flag (WRONG in Research Guidance §1)

**Prior document lists:** `--auth-token` as a Phase 1 flag.  
**Reality:** This flag does not exist in spotDL v4. Remove it from the flag matrix.  
**Correct Phase 1 flags:** `--client-id`, `--client-secret`, `--user-auth`, `--save-file` (not `--save`).

### Correction 3 — spotDL stdout Contains ANSI Escape Codes (BLINDSPOT in Research Guidance §2)

**Prior plan:** "Parse stdout with regex for progress (e.g., %, track name)."  
**Reality:** spotDL uses the `rich` library for terminal output, which injects ANSI escape codes (e.g., `\x1b[32m`, `\x1b[0m`) into stdout. A naive regex will produce garbage matches or zero matches.  
**Fix:** All subprocess stdout must be stripped of ANSI codes before regex parsing:
```python
import re
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub('', text)
```
Additionally, always launch the subprocess with `PYTHONUNBUFFERED=1` and `TERM=dumb` in the environment to suppress rich's full formatting.

### Correction 4 — "Immutable Batch" Semantic Confusion (BLINDSPOT in all prior docs)

**Prior documents state:** Batches are "immutable" entities that also support CRUD file operations (Copy, Move, Delete). These two properties are in direct logical conflict.  
**Correct semantic model:**
- The **Batch Manifest** is immutable: the source URL, execution timestamp, config snapshot, and original track list are write-once records. They describe what was *intended and executed*.
- The **Batch File State** is mutable: files can be copied, moved, deleted. Each file operation is recorded as a mutation log entry against the immutable manifest.
- The UI should make this distinction visible: a badge like `[Manifest: Complete | Files: 2 Deleted]` conveys the difference.
- A Batch with all files deleted is **Archived**, not deleted. Its manifest persists in the database for provenance.

### Correction 5 — PyInstaller "One-Click EXE" Is False (BLINDSPOT in Research Guidance §3)

**Prior claim:** "PyInstaller (one-click exe)" for bundling.  
**Reality:** PyInstaller + PySide6 on Windows is notoriously fragile. `--onefile` mode is especially prone to DLL resolution failures and Windows Defender false positives. FFmpeg binary embedding adds further complexity.  
**Authoritative decision for MVP:** Do not bundle. The app runs from a Python environment. Provide a `setup.ps1` / `setup.sh` install script. Bundling is a post-v1.0 task. If bundling is pursued, use **Nuitka** with `--standalone` instead of PyInstaller — it produces a proper compiled package.

### Correction 6 — Config Profile Should Use spotDL's config.json (MISSED OPTIMIZATION)

**Prior plan:** Build a "Configuration Matrix" GUI that translates toggles into subprocess CLI args.  
**Better approach:** spotDL natively reads `~/.spotdl/config.json` for persistent settings. Before each batch run, the app writes a **temporary config file** from the selected Profile to `--config [path]`, then passes only `--config [path]` to the subprocess. This:
1. Eliminates the fragile "flag dict → CLI string" serialization layer.
2. Means the app always has a stored, inspectable record of exactly what config ran each batch (store the JSON in the DB).
3. Keeps CLI arg construction to just: `spotdl [url] --config [batch_config.json] --save-file [batch.spotdl]`.

The app must maintain its own config schema that maps 1:1 to spotDL's `config.json` format.

---

## PART 1: DEFINITIVE ARCHITECTURE

### 1.1 System Topology

```
┌─────────────────────────────────────────────────────────────────┐
│  GUI Layer (PySide6)                                             │
│  MainWindow → LibraryView | NewBatchWizard | EngineSettings     │
│              BlacklistManager | ReconciliationDialog            │
└────────────────────────────┬────────────────────────────────────┘
                             │ signals/slots (Qt)
┌────────────────────────────▼────────────────────────────────────┐
│  Service Layer (Python, runs on QThread workers)                 │
│  BatchService | ExclusionEngine | ExecutionEngine               │
│  MetadataVerifier | LibraryReconciler | PlaylistExporter        │
└────────────────────────────┬────────────────────────────────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
┌──────▼──────┐   ┌──────────▼───────┐   ┌────────▼────────┐
│  SQLite DB  │   │  File System     │   │  spotDL process │
│ (SQLAlchemy)│   │  (pathlib)       │   │  (subprocess)   │
└─────────────┘   └──────────────────┘   └─────────────────┘
```

### 1.2 Authoritative Tech Stack

| Layer | Technology | Version Constraint | Rationale |
|---|---|---|---|
| Language | Python | 3.12 | Latest stable, best perf |
| Env Management | uv | latest | Fast installs, lockfile |
| GUI | PySide6 | ^6.7 | Qt6, native look, QThread |
| DB ORM | SQLAlchemy | ^2.0 | Modern async-capable ORM |
| DB Engine | SQLite | bundled | Local-first, zero config |
| Migrations | Alembic | ^1.13 | Schema versioning |
| Metadata R/W | mutagen | ^1.47 | MP3/FLAC/M4A/Opus all supported |
| Fuzzy Match | rapidfuzz | ^3.9 | Fastest, Levenshtein + token sort |
| File Watch | watchdog | ^4.0 | Reconciliation trigger |
| ANSI Strip | built-in re | — | No dep needed |
| Downloader | spotDL | ==4.4.3 | **Pin this. Do not let uv float it.** |
| yt-dlp | yt-dlp | pin to spotDL's requirement | Version conflicts are real |

> **Critical:** Pin `spotDL==4.4.3` in `pyproject.toml`. The flag schema, stdout format, and `.spotdl` JSON schema are all version-dependent. Any version bump must be a deliberate, tested upgrade.

---

## PART 2: DATA ARCHITECTURE

### 2.1 SQLAlchemy Models (Authoritative Schema)

```python
# models.py — This is the ground truth. Do not deviate.
import json
from datetime import datetime
from pathlib import Path
from sqlalchemy import (
    String, Integer, DateTime, Boolean, Text, ForeignKey, Enum
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum

class Base(DeclarativeBase):
    pass

class BatchStatus(str, enum.Enum):
    PENDING     = "pending"      # Created, not yet run
    RUNNING     = "running"      # Subprocess active
    COMPLETE    = "complete"     # All tracks succeeded
    PARTIAL     = "partial"      # Some tracks failed
    FAILED      = "failed"       # All tracks failed or fatal error
    DEGRADED    = "degraded"     # Files missing post-run (reconciliation result)
    ARCHIVED    = "archived"     # All files deleted; manifest retained

class TrackStatus(str, enum.Enum):
    QUEUED      = "queued"
    EXCLUDED    = "excluded"     # Filtered by exclusion engine pre-download
    DOWNLOADING = "downloading"
    TAGGING     = "tagging"
    COMPLETE    = "complete"
    FAILED      = "failed"
    MISSING     = "missing"      # File was present, now gone (reconciliation)

class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int]             = mapped_column(Integer, primary_key=True)
    source_url: Mapped[str]     = mapped_column(String, nullable=False)
    created_at: Mapped[datetime]= mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[BatchStatus] = mapped_column(Enum(BatchStatus), default=BatchStatus.PENDING)
    
    # Immutable manifest fields (write-once at batch creation)
    profile_name: Mapped[str]   = mapped_column(String, nullable=False)
    config_json: Mapped[str]    = mapped_column(Text, nullable=False)  # JSON snapshot of config used
    spotdl_save_path: Mapped[str | None] = mapped_column(String, nullable=True)  # Path to .spotdl metadata file
    
    # Output
    output_dir: Mapped[str]     = mapped_column(String, nullable=False)
    m3u_path: Mapped[str | None]= mapped_column(String, nullable=True)
    
    # Stats (computed post-run)
    total_tracks: Mapped[int]   = mapped_column(Integer, default=0)
    succeeded: Mapped[int]      = mapped_column(Integer, default=0)
    excluded: Mapped[int]       = mapped_column(Integer, default=0)
    failed: Mapped[int]         = mapped_column(Integer, default=0)
    
    tracks: Mapped[list["Track"]] = relationship("Track", back_populates="batch", cascade="all, delete-orphan")
    file_ops: Mapped[list["FileOperation"]] = relationship("FileOperation", back_populates="batch")

class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int]               = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int]         = mapped_column(ForeignKey("batches.id"), nullable=False)
    
    # Deterministic identity keys (from Phase 1 Spotify metadata)
    spotify_uri: Mapped[str | None] = mapped_column(String, nullable=True, index=True)  # Always present
    isrc: Mapped[str | None]        = mapped_column(String, nullable=True, index=True)   # Sometimes absent
    
    # Metadata mirror (from .spotdl JSON — see §2.2 for field mapping)
    title: Mapped[str]              = mapped_column(String, nullable=False)
    artist: Mapped[str]             = mapped_column(String, nullable=False)
    album: Mapped[str | None]       = mapped_column(String, nullable=True)
    year: Mapped[int | None]        = mapped_column(Integer, nullable=True)
    duration_s: Mapped[int | None]  = mapped_column(Integer, nullable=True)
    explicit: Mapped[bool]          = mapped_column(Boolean, default=False)
    cover_url: Mapped[str | None]   = mapped_column(String, nullable=True)
    
    # File state (mutable)
    file_path: Mapped[str | None]   = mapped_column(String, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[TrackStatus]     = mapped_column(Enum(TrackStatus), default=TrackStatus.QUEUED)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Verification (post-mutagen audit)
    tags_verified: Mapped[bool]     = mapped_column(Boolean, default=False)
    art_embedded: Mapped[bool]      = mapped_column(Boolean, default=False)
    
    batch: Mapped["Batch"]          = relationship("Batch", back_populates="tracks")

class BlacklistEntry(Base):
    __tablename__ = "blacklist"

    id: Mapped[int]             = mapped_column(Integer, primary_key=True)
    # Primary key for matching — prefer spotify_uri, fallback to isrc
    spotify_uri: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    isrc: Mapped[str | None]        = mapped_column(String, nullable=True)
    # Human-readable display (for UI)
    display_name: Mapped[str]       = mapped_column(String, nullable=False)  # "Artist - Title"
    added_at: Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow)
    source: Mapped[str]             = mapped_column(String, default="manual")  # "manual" | "exclusion_engine"

class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int]             = mapped_column(Integer, primary_key=True)
    name: Mapped[str]           = mapped_column(String, nullable=False, unique=True)
    config_json: Mapped[str]    = mapped_column(Text, nullable=False)  # Serialized ProfileConfig
    is_default: Mapped[bool]    = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime]= mapped_column(DateTime, default=datetime.utcnow)

class FileOperation(Base):
    __tablename__ = "file_operations"
    # Mutation log against the immutable batch manifest
    id: Mapped[int]             = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int]       = mapped_column(ForeignKey("batches.id"), nullable=False)
    track_id: Mapped[int | None]= mapped_column(ForeignKey("tracks.id"), nullable=True)
    op_type: Mapped[str]        = mapped_column(String, nullable=False)  # "copy"|"move"|"delete"|"archive"
    source_path: Mapped[str | None] = mapped_column(String, nullable=True)
    dest_path: Mapped[str | None]   = mapped_column(String, nullable=True)
    performed_at: Mapped[datetime]  = mapped_column(DateTime, default=datetime.utcnow)
    batch: Mapped["Batch"]          = relationship("Batch", back_populates="file_ops")
```

### 2.2 The `.spotdl` JSON Schema (spotDL v4.4.3)

The save file is a JSON array of Song objects. This is the field mapping used by the ExclusionEngine and Track model population:

```python
# Field mapping: .spotdl JSON → Track model
SPOTDL_FIELD_MAP = {
    "name":       "title",
    "artist":     "artist",        # Primary artist string
    "album":      "album",
    "year":       "year",
    "duration":   "duration_s",    # In seconds (float → cast to int)
    "isrc":       "isrc",          # May be None
    "song_id":    "spotify_uri",   # Always present, e.g. "spotify:track:6rqhFgbbKwnb9MLmUQDhG6"
    "explicit":   "explicit",
    "cover_url":  "cover_url",
}
# "artists" (list) also available for multi-artist tracks — join with ", " for display
```

> **Version Guard:** At startup, run `spotdl --version` and assert `== "4.4.3"`. If version mismatch, warn the user with a non-blocking dialog: "spotDL version X detected. This app is tested against 4.4.3. Proceed with caution."

---

## PART 3: PROJECT STRUCTURE

```
spotdl_manager/
├── pyproject.toml          # uv managed; pins spotDL==4.4.3
├── uv.lock                 # Committed lockfile
├── setup.ps1               # Windows install script (python env + ffmpeg)
├── setup.sh                # Unix install script
├── alembic.ini
├── alembic/
│   └── versions/
├── main.py                 # Entry point: creates QApplication, launches MainWindow
├── app/
│   ├── __init__.py
│   ├── config.py           # AppConfig dataclass + ProfileConfig dataclass
│   ├── db.py               # SQLAlchemy engine + Session factory + init_db()
│   ├── models.py           # All ORM models (see §2.1)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── batch_service.py        # CRUD on batches; orchestrates workflow
│   │   ├── execution_engine.py     # QThread wrapper for subprocess; emits signals
│   │   ├── exclusion_engine.py     # Phase 1 save → fuzzy match → cull → ISRC blacklist
│   │   ├── metadata_verifier.py    # Post-download mutagen audit loop
│   │   ├── playlist_exporter.py    # Generates .m3u8 per batch
│   │   ├── reconciler.py           # File system vs DB diff; flags degraded tracks
│   │   └── config_writer.py        # Serializes ProfileConfig → spotDL config.json
│   │
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py          # Shell: sidebar + stacked content area
│   │   ├── library_view.py         # QTableView of batches; expandable tracks
│   │   ├── new_batch_wizard.py     # URL input → profile select → exclusion preview → confirm
│   │   ├── engine_settings.py      # Tabbed flag editor; profile save/load
│   │   ├── blacklist_manager.py    # View/add/remove blacklist entries
│   │   ├── download_pane.py        # Live progress for active batch (log + bar + cancel)
│   │   ├── reconciliation_dialog.py
│   │   └── widgets/
│   │       ├── batch_card.py
│   │       └── track_row.py
│   │
│   └── utils/
│       ├── ansi.py                 # strip_ansi() utility
│       ├── m3u.py                  # M3U8 write helpers
│       └── paths.py                # Platform-safe path resolution
│
└── tests/
    ├── test_exclusion_engine.py
    ├── test_execution_engine.py
    └── test_metadata_verifier.py
```

---

## PART 4: SCOPE GATES — MANDATORY

The prior research document lists features that span months of work without prioritization. The following gates are non-negotiable. The agent must not implement v0.2 features during v0.1 work.

### v0.1 — MVP (Agent Target)

Core loop functional, no polish:

- [ ] DB schema + Alembic migrations
- [ ] ProfileConfig ↔ spotDL config.json writer
- [ ] ExecutionEngine: subprocess with ANSI-stripped stdout → progress signals
- [ ] Phase 1 save flow: `spotdl save [url] --config [profile.json] --save-file [batch.spotdl]`
- [ ] ExclusionEngine: parse .spotdl JSON → rapidfuzz match → cull → write sanitized .spotdl
- [ ] Phase 2-4 download flow: `spotdl [sanitized.spotdl] --config [profile.json]`
- [ ] Track → DB population from .spotdl parse
- [ ] MetadataVerifier: mutagen read → verify art + ID3v2.4 → update Track.tags_verified
- [ ] PlaylistExporter: per-batch .m3u8 with `#EXTINF` duration + relative paths
- [ ] LibraryReconciler: startup scan of most recent 20 batches
- [ ] GUI: NewBatchWizard (URL + profile), DownloadPane (log + progress + cancel), LibraryView (batch list + track expand)

### v0.2

- [ ] EngineSettings full flag editor with profile CRUD
- [ ] BlacklistManager UI
- [ ] FileOperation CRUD (copy/move/delete batches/tracks from UI)
- [ ] Batch status badge (Manifest: Complete | Files: N Deleted)
- [ ] Preview player (QMediaPlayer, single track)
- [ ] watchdog-based real-time reconciliation
- [ ] Manual tag editor per track

### v1.0

- [ ] Hybrid fallback mode (CSV + yt-dlp when Spotify auth fails) — **not before v1.0**
- [ ] Statistics dashboard per batch
- [ ] Batch export (zip archive)
- [ ] Bundling investigation (Nuitka)
- [ ] Alternative download engine selector (SomeDL, Deezer)

---

## PART 5: KEY IMPLEMENTATION CONTRACTS

### 5.1 ExecutionEngine (The Hardest Module)

```python
# execution_engine.py — key signal contract
from PySide6.QtCore import QThread, Signal

class ExecutionWorker(QThread):
    # Signals — ALL UI updates must go through these
    progress_updated  = Signal(int, int)          # (completed_tracks, total_tracks)
    track_started     = Signal(str)               # track display name
    track_finished    = Signal(str, bool, str)    # (spotify_uri, success, error_msg)
    log_line          = Signal(str)               # stripped log line for DownloadPane
    phase_changed     = Signal(str)               # "saving_metadata"|"filtering"|"downloading"|"tagging"
    finished          = Signal(bool)              # success flag
    
    def __init__(self, url: str, profile_config: "ProfileConfig", 
                 exclusion_list: list[str], output_dir: str):
        ...
    
    def run(self):
        # Step 1: Write profile to temp config.json
        # Step 2: Run spotdl save → emit phase_changed("saving_metadata")
        # Step 3: Parse .spotdl JSON → run ExclusionEngine → emit phase_changed("filtering")
        # Step 4: Run spotdl [sanitized.spotdl] → stream stdout, emit progress/track signals
        # Step 5: Run MetadataVerifier → emit phase_changed("tagging")
        # Step 6: Run PlaylistExporter
        # Step 7: emit finished(success)
    
    def request_cancel(self):
        # Sets a flag; run() checks it between phases.
        # For mid-download cancel: self._process.terminate() then cleanup.
        self._cancel_requested = True
```

**stdout parsing contract — use this exact pattern:**

```python
# In run(), reading spotdl download progress:
# spotDL v4 outputs lines like:
# "Downloaded \"Artist - Track\"" on success
# "Skipping Artist - Track (not found on YouTube)" on skip
# "Failed to download Artist - Track" on failure
# Percentage is NOT reliably printed per-track; count "Downloaded" lines instead.

DOWNLOAD_SUCCESS = re.compile(r'Downloaded\s+"(.+)"')
DOWNLOAD_SKIP    = re.compile(r'Skipping\s+(.+)')
DOWNLOAD_FAIL    = re.compile(r'Failed to download\s+(.+)')

for raw_line in iter(self._process.stdout.readline, ''):
    if self._cancel_requested:
        break
    line = strip_ansi(raw_line)
    self.log_line.emit(line.strip())
    
    if m := DOWNLOAD_SUCCESS.search(line):
        self.track_finished.emit(m.group(1), True, "")
    elif m := DOWNLOAD_FAIL.search(line):
        self.track_finished.emit(m.group(1), False, line.strip())
```

> **Note:** These regex patterns are tested against spotDL 4.4.3. Validate them on first run; spotDL's output wording can change. Add a "raw log" toggle in the DownloadPane so the user can always inspect unfiltered output.

### 5.2 ExclusionEngine

```python
# exclusion_engine.py
import json
from rapidfuzz import fuzz
from pathlib import Path

FUZZY_THRESHOLD = 85  # Levenshtein token sort ratio; tunable in settings

def load_spotdl_file(path: Path) -> list[dict]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)  # List of Song dicts

def build_display_name(song: dict) -> str:
    # Canonical form used for matching
    return f"{song['artist']} - {song['name']}"

def run_exclusion(
    spotdl_path: Path,
    blacklist_db_entries: list["BlacklistEntry"],  # ISRC/URI from DB
    text_exclusion_list: list[str],                # "Artist - Track" strings from user
) -> tuple[list[dict], list[dict]]:
    """
    Returns (keep_list, excluded_list).
    Writes sanitized .spotdl file back to spotdl_path.
    """
    songs = load_spotdl_file(spotdl_path)
    keep, excluded = [], []
    
    # Build fast-lookup sets for DB-backed exclusions
    blacklist_uris  = {e.spotify_uri for e in blacklist_db_entries if e.spotify_uri}
    blacklist_isrcs = {e.isrc for e in blacklist_db_entries if e.isrc}
    
    for song in songs:
        uri  = song.get('song_id')
        isrc = song.get('isrc')
        
        # 1. Deterministic DB match (fastest, most accurate)
        if uri in blacklist_uris or (isrc and isrc in blacklist_isrcs):
            excluded.append(song)
            continue
        
        # 2. Fuzzy text match against user's exclusion list
        display = build_display_name(song)
        is_excluded = any(
            fuzz.token_sort_ratio(display.lower(), entry.lower()) >= FUZZY_THRESHOLD
            for entry in text_exclusion_list
        )
        if is_excluded:
            excluded.append(song)
            continue
        
        keep.append(song)
    
    # Write sanitized file back
    with open(spotdl_path, 'w', encoding='utf-8') as f:
        json.dump(keep, f, ensure_ascii=False, indent=2)
    
    return keep, excluded
```

> **After exclusion:** For every excluded track identified via fuzzy text match (not yet in DB), extract its `song_id` (Spotify URI) and `isrc` and insert into `BlacklistEntry` with `source="exclusion_engine"`. This converts the one-time fuzzy match into a permanent, deterministic blacklist entry.

### 5.3 MetadataVerifier

```python
# metadata_verifier.py
from mutagen import File as MutagenFile
from mutagen.id3 import ID3NoHeaderError
from pathlib import Path

class VerificationResult:
    has_art: bool
    has_title: bool
    has_artist: bool
    id3_version: tuple  # e.g. (2, 4, 0)
    issues: list[str]

def verify_track(file_path: Path) -> VerificationResult:
    """
    Reads the finalized file with mutagen and checks:
    1. Album art is embedded (not just a URL reference)
    2. ID3 version is 2.4.x (not 2.3 which some FFmpeg versions produce)
    3. Title, Artist, Album fields are present
    Returns a result object; does NOT auto-fix (caller decides repair strategy).
    """
    ...

def normalize_id3_version(file_path: Path) -> bool:
    """
    If ID3 version is 2.3, upgrades to 2.4 in-place.
    Musicolet handles both, but 2.4 is canonical.
    Returns True if normalization was performed.
    """
    ...
```

### 5.4 PlaylistExporter (Musicolet-Compatible)

```python
# playlist_exporter.py
# Generates M3U8 (UTF-8) with EXTINF metadata
# Uses RELATIVE paths — allows the batch folder to be moved

def export_batch_m3u8(batch: "Batch", tracks: list["Track"], output_path: Path):
    """
    Writes a Musicolet-compatible M3U8.
    Relative paths calculated from output_path.parent.
    """
    lines = ["#EXTM3U", ""]
    for track in tracks:
        if track.status != TrackStatus.COMPLETE or not track.file_path:
            continue
        file_path = Path(track.file_path)
        rel_path  = file_path.relative_to(output_path.parent)
        duration  = track.duration_s or -1
        artist_title = f"{track.artist} - {track.title}"
        lines.append(f"#EXTINF:{duration},{artist_title}")
        lines.append(str(rel_path))
    
    output_path.write_text('\n'.join(lines), encoding='utf-8')
```

### 5.5 ProfileConfig (spotDL config.json mapping)

```python
# config.py
from dataclasses import dataclass, field, asdict
import json
from pathlib import Path

@dataclass
class ProfileConfig:
    # Phase 1
    client_id: str     = ""
    client_secret: str = ""
    user_auth: bool    = False
    
    # Phase 2
    audio_provider: str  = "youtube-music"   # "youtube" | "youtube-music"
    filter_results: bool = True               # False = --dont-filter-results
    
    # Phase 3
    threads: int           = 4
    cookie_file: str       = ""
    sponsor_block: bool    = False
    yt_dlp_args: str       = ""
    
    # Phase 4
    format: str    = "m4a"        # mp3|m4a|flac|opus|ogg|wav
    bitrate: str   = "disable"    # "disable"|"auto"|"320k"|"192k" etc.
    output: str    = "{artist}/{album}/{track-number} - {title}.{output-ext}"
    
    # Extras
    generate_lrc: bool    = False
    skip_explicit: bool   = False
    save_errors: str      = ""    # Path for spotDL's error log
    archive: str          = ""    # Path for spotDL's archive file (dupe prevention)
    
    def to_spotdl_config(self) -> dict:
        """Converts to spotDL config.json format."""
        cfg = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "user_auth": self.user_auth,
            "audio_provider": self.audio_provider,
            "threads": self.threads,
            "format": self.format,
            "bitrate": self.bitrate,
            "output": self.output,
            "generate_lrc": self.generate_lrc,
            "skip_explicit": self.skip_explicit,
        }
        if not self.filter_results:
            cfg["dont_filter_results"] = True
        if self.cookie_file:
            cfg["cookie_file"] = self.cookie_file
        if self.sponsor_block:
            cfg["sponsor_block"] = True
        if self.yt_dlp_args:
            cfg["yt_dlp_args"] = self.yt_dlp_args
        if self.archive:
            cfg["archive"] = self.archive
        return cfg
    
    def write_to_file(self, path: Path):
        path.write_text(json.dumps(self.to_spotdl_config(), indent=2), encoding='utf-8')
```

---

## PART 6: FAILURE MODE REGISTRY

Every known failure mode, its detection method, and its mitigation:

| ID | Failure | Detection | Mitigation |
|----|---------|-----------|------------|
| F-01 | Spotify API auth failure (Feb 2026 Dev Mode restrictions) | stderr: "SpotifyAuthorizationError" or "401" | Show credential wizard dialog; surface `--client-id` / `--client-secret` inputs; link to Spotify Developer dashboard |
| F-02 | spotDL version mismatch | Startup version check | Non-blocking warning dialog; do not abort |
| F-03 | FFmpeg not found | stderr: "FFmpeg not found" | Auto-run `spotdl --download-ffmpeg` on first launch; show installation progress |
| F-04 | No YouTube match found | stdout: "Skipping..." | Log to track.error_message; mark TrackStatus.FAILED; surface in UI as filterable |
| F-05 | ANSI codes breaking regex | Blank progress bar, no track events | strip_ansi() is always applied; add raw log toggle for user debug |
| F-06 | .spotdl JSON schema change (version bump) | JSONDecodeError or KeyError on parse | Version guard at startup; catch parse errors per-Song and skip with warning |
| F-07 | Files moved outside app | Startup reconciler finds missing paths | Flag batch as DEGRADED; show reconciliation dialog with "Locate File" and "Remove from Library" options |
| F-08 | Duplicate track download | Same ISRC/URI already in DB | Leverage spotDL's `--archive` flag + DB uniqueness check on spotify_uri |
| F-09 | Subprocess hangs (no stdout) | QThread timeout (60s no output) | Kill process after timeout; mark batch FAILED; show error |
| F-10 | Quality loss from transcoding | User using --bitrate with lossy source | Default profile sets `--bitrate disable` + `m4a`; warn in UI when user sets bitrate on already-lossy format |
| F-11 | mutagen can't read file | MutagenFile returns None | Log to track.error_message as "tag verification failed"; do not abort batch |
| F-12 | Fuzzy match false positive | User-reported wrong exclusion | Expose exclusion preview step in NewBatchWizard; let user uncheck tracks before confirming |
| F-13 | Private playlist (no --user-auth) | stderr: "403" or empty playlist | Detect in stderr; prompt user to enable user_auth in profile |

---

## PART 7: AGENT EXECUTION ORDER

Execute in this exact order. Do not proceed to next step until current step has passing tests.

**Step 1 — Foundation (no GUI)**
1. Initialize project with `uv init`, add all deps to `pyproject.toml`
2. Write `models.py` exactly as defined in §2.1
3. Write `db.py` with `init_db()`, `get_session()`, `SessionLocal`
4. Run `alembic init alembic` and generate initial migration
5. Write tests for model creation + basic queries

**Step 2 — Config System**
1. Implement `ProfileConfig` dataclass + `to_spotdl_config()` + `write_to_file()`
2. Write `config_writer.py` service wrapper
3. Insert default "Standard" profile into DB at `init_db()` time
4. Test: instantiate ProfileConfig → write to temp file → assert JSON structure valid

**Step 3 — Execution Engine (headless, no GUI)**
1. Implement `strip_ansi()` in `utils/ansi.py`
2. Implement `ExecutionWorker` as a plain class (not QThread yet — test logic first)
3. Implement stdout parsing + all regex patterns from §5.1
4. Test with a real `spotdl save` run against a known Spotify track URL
5. Verify .spotdl JSON is produced and parseable
6. Test full download of a single track; verify file produced + stdout parsed correctly
7. Wrap in QThread; connect signals

**Step 4 — Exclusion Engine**
1. Implement `ExclusionEngine` from §5.2 exactly
2. Test with a .spotdl file and a text exclusion list — verify fuzzy match catches "The Beatles" vs "Beatles"
3. Test ISRC/URI DB lookup path
4. Test sanitized .spotdl JSON is written correctly and re-passable to spotdl

**Step 5 — Metadata Verifier + Playlist Exporter**
1. Implement `MetadataVerifier` — verify, normalize_id3_version
2. Implement `PlaylistExporter` — relative paths, EXTINF format
3. Test M3U8 output manually in Musicolet (smoke test)

**Step 6 — Reconciler**
1. Implement `LibraryReconciler.scan_recent(n=20)` — checks file_path existence for last N batches
2. Marks missing tracks as TrackStatus.MISSING; marks batch as BatchStatus.DEGRADED
3. Run on `app_startup` signal

**Step 7 — GUI Shell (v0.1 minimum)**
1. Implement `MainWindow` with sidebar nav + stacked widget
2. Implement `NewBatchWizard` (URL input → profile dropdown → exclusion preview → confirm)
3. Implement `DownloadPane` with QProgressBar + QTextEdit log + Cancel button
4. Implement `LibraryView` with QTableView showing batches (virtualized; use QAbstractTableModel)
5. Wire `ExecutionWorker` signals → DownloadPane updates
6. Wire batch completion → DB update → LibraryView refresh

**Step 8 — Integration Test**
1. Run full workflow: URL → exclusion → download → tag verify → m3u export → library view
2. Trigger F-03 (delete FFmpeg, verify auto-install prompt)
3. Trigger F-07 (manually delete a downloaded file, restart app, verify DEGRADED badge)
4. Trigger F-12 (add a track to text exclusion list, verify it appears in exclusion preview)

---

## PART 8: DEFERRED DECISIONS (Do Not Resolve in v0.1)

The following questions were raised in prior documents but are explicitly deferred. Do not architect around them now.

1. **Hybrid fallback mode (spotDL → CSV/yt-dlp):** Architecture change; v1.0 only. For now, when Spotify auth fails, show the credential wizard (F-01) and stop.

2. **Bundling/packaging:** Post-v1.0. Do not spend any time on PyInstaller or Nuitka during v0.1/v0.2.

3. **Preview player (QMediaPlayer):** v0.2. Not in MVP critical path.

4. **SomeDL / Deezer alternative engine:** v1.0. The abstraction point is `ExecutionEngine` — a future `DeezerExecutionWorker` would implement the same signal interface.

5. **Local AI tag correction / MusicBrainz lookup:** Nice-to-have. Only if metadata verifier shows systemic gaps.

6. **Cloud sync:** Explicitly out of scope forever. This is a local-first tool.

---

## APPENDIX A: SUBPROCESS LAUNCH CONTRACT

```python
import subprocess
import os

def build_env() -> dict:
    """Environment for all spotdl subprocess calls."""
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    env['TERM'] = 'dumb'        # Suppresses rich's full ANSI formatting
    env['NO_COLOR'] = '1'       # Belt-and-suspenders for ANSI suppression
    return env

def launch_spotdl_save(url: str, config_path: str, save_file_path: str) -> subprocess.Popen:
    return subprocess.Popen(
        ['spotdl', 'save', url, '--config', config_path, '--save-file', save_file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,   # Merge stderr into stdout for unified log stream
        text=True,
        encoding='utf-8',
        errors='replace',           # Don't crash on encoding edge cases
        env=build_env(),
    )

def launch_spotdl_download(spotdl_file: str, config_path: str) -> subprocess.Popen:
    return subprocess.Popen(
        ['spotdl', spotdl_file, '--config', config_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        env=build_env(),
    )
```

---

## APPENDIX B: DEFAULT PROFILE (Insert at init_db)

```json
{
  "name": "Standard",
  "audio_provider": "youtube-music",
  "threads": 4,
  "format": "m4a",
  "bitrate": "disable",
  "output": "{artist}/{album}/{track-number} - {title}.{output-ext}",
  "filter_results": true,
  "generate_lrc": false,
  "skip_explicit": false
}
```

**Rationale for defaults:**
- `m4a` + `bitrate: disable` = no re-encoding; preserves original YouTube stream quality (AAC 256kbps if YouTube Premium cookie present, 128kbps otherwise)
- `youtube-music` = better metadata match fidelity than `youtube` for music
- `filter_results: true` = prevents live versions / covers from slipping through
- `generate_lrc` off = reduces match failures on less-indexed tracks

---

*End of Authoritative Specification v2.0*  
*This document should be committed to the project repository as `SPEC.md` and referenced by the agent at every implementation decision point.*
