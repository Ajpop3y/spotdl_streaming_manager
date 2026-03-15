**SOURCE DOCUMENT FOR AUTONOMOUS AGENT: Implementation of spotDL-Based Music Discovery & Library Management Desktop App**

**Version:** 1.0 (March 15, 2026)  
**Purpose:** This is your complete reference blueprint. It incorporates exhaustive research across spotDL internals, current ecosystem constraints, dependencies, GUI frameworks, metadata tools, and systems-level risks. Use it as the single source of truth for architecture, tech choices, workflows, and mitigations. The app must remain **local-first**, **batch-centric**, and **fully configurable** per the user's RAW WISHES while delivering "precisely perfect" metadata and exclusion filtering.

### 1. Research Findings on spotDL & Ecosystem (March 2026 Snapshot)

**Core Project Status**  
- Official repo: https://github.com/spotDL/spotify-downloader (24k+ stars).  
- Latest stable: **v4.4.3** (Oct 8, 2025). Pipeline exactly matches the provided FEATURE OVERVIEW (Phase 1: Spotify metadata via API → Phase 2: YouTube/YouTube Music matching → Phase 3: yt-dlp download → Phase 4: FFmpeg conversion + tagging).  
- `.spotdl` save files are JSON-like metadata dumps (title, artist, album, year, ISRC, URI, cover URL, duration) — perfect for pre-flight exclusion and fuzzy matching.  
- Flags fully documented and exhaustive (see usage section below).  
- **Critical Breaking Change (Feb 2026 Spotify Web API Dev Mode Update):** Public/embedded client credentials and shared tokens are now restricted (Premium account required for dev mode, 1 Client ID per developer, max 5 authorized users per app, reduced endpoints). Issues #2617, #2605, #2621 are open with no maintainer roadmap. Community fixes (PR #2610) allow user-provided `client_id`/`client_secret` + `--user-auth` via config.json, but this limits the app to personal use only. Rate-limit errors and auth failures are now common.

**Programmatic Usage**  
- No stable public Python API in v4 (old v2 `Spotdl` class is gone). Reliable path: `subprocess.Popen` with `python -m spotdl` or direct `spotdl` executable, capturing stdout/stderr in real-time for progress parsing (e.g., "Downloading...", percentage, errors).  
- Web UI (`spotdl web`) exists but is limited to single tracks — ignore for this GUI app.

**Dependencies & Installation (Critical for Bundling)**  
- Python 3.9+ (3.12 recommended).  
- FFmpeg 4.2+ (mandatory; app must auto-run `spotdl --download-ffmpeg` or bundle binaries).  
- yt-dlp (auto-installed via pip; version conflicts common — pin or let user upgrade).  
- Other: syncedlyrics (lyrics), mutagen-compatible tagging.  
- Cross-platform install: `pip install spotdl`; app must guide or auto-install FFmpeg + Visual C++ Redist (Windows).

**Alternatives & Fallbacks (Post-API Era)**  
- CSV metadata export (Exportify or chosic.com) + yt-dlp direct (community fork CaptSolo/spotify-downloader-csv).  
- Emerging tools: SomeDL (pip install somedl) — pulls from Genius/MusicBrainz/Deezer for richer metadata.  
- Pure yt-dlp + MusicBrainz Picard for tagging.  
- Deezer API/downloader (kmille/deezer-downloader) as full replacement.  
Your app must implement a **hybrid mode** (spotDL primary → CSV/yt-dlp fallback) with migration wizard.

**Full Flag Matrix (Exposed in GUI "Engine Settings")**  
Group exactly as in the document + extras from official usage:  
- Phase 1: `--user-auth`, `--client-id`, `--client-secret`, `--auth-token`, `--save` (metadata-only).  
- Phase 2: `--audio [youtube|youtube-music|...]`, `--dont-filter-results`, `--only-verified-results`.  
- Phase 3: `--threads`, `--cookie-file`, `--sponsor-block`, `--yt-dlp-args`.  
- Phase 4: `--format [mp3|m4a|flac|opus|ogg|wav]`, `--bitrate [auto|disable|320k|...]`, `--output "{artist}/{album}/{track-number} - {title}.{output-ext}"`.  
Extras: `--generate-lrc`, `--skip-explicit`, `--ignore-albums`, `--preload`, `--archive` (dupe prevention).

**Metadata & Tagging**  
- spotDL embeds via FFmpeg (ID3v2.4). Post-process with **mutagen** (quodlibet/mutagen) for verification/normalization (album art, genre, explicit flags, lyrics .lrc). Handles MP3, FLAC, M4A perfectly.

**GUI Framework Research (2026)**  
PySide6 (Qt6) is the clear winner for professional desktop music apps: native look/feel, QThread + signals for async progress, QTableView for library, QMediaPlayer for preview, cross-platform (Win/Mac/Linux), PyInstaller bundling support. Alternatives (Tkinter too basic; CustomTkinter limited; Kivy mobile-focused) are inferior for sophisticated batch/library UI.

### 2. Systems-Thinking Architecture (Expanded Blueprint)

**Core Entities**  
- **Batch Collection** (immutable): ID, source URL, timestamp, config profile snapshot, status (Success/Degraded/Failed), 1-to-many Tracks.  
- **Track**: Spotify URI/ISRC (deterministic key), file path, metadata JSON mirror, blacklist flag.  
- **Profile**: Saved JSON of all phase flags (e.g., "Hi-Res Archive", "Quick Listen").  
- **Blacklist**: Global DB table of ISRC/URI + fuzzy string list (Artist - Track).

**Database**  
SQLite + SQLAlchemy (ORM). On-app-start "Library Reconciliation" job scans file paths and flags missing files as "Degraded".

**File System Integration**  
- Output templates drive folder structure.  
- Auto-generate per-batch `.m3u` playlist (relative paths) for export to Musicolet/etc.  
- CRUD scoped to batches only (copy/move/delete/archive entire collection).

**Exclusion Engine (Pre-Phase 2)**  
1. Run `spotdl save` → parse `.spotdl` JSON.  
2. Fuzzy match (rapidfuzz Levenshtein >85% threshold) on "Artist - Track".  
3. If match → cull using ISRC/URI (store in blacklist DB for future-proofing).  
4. Feed sanitized list back to download.

**Execution Engine**  
- QThread worker (not raw asyncio for Qt integration).  
- Real-time stdout parsing → progress bar + live log pane.  
- Cancellation support.  
- Parallel threads configurable per-batch.

**Post-Processing**  
- mutagen verification loop: confirm art, normalize tags, fix ID3v2.4.  
- Generate .lrc if enabled.

### 3. Recommended Tech Stack (Practical & Maintainable)

- **Language:** Python 3.12 (uv for fast envs).  
- **GUI:** PySide6 (Qt Designer for rapid prototyping).  
- **DB:** SQLAlchemy + SQLite (alembic for migrations).  
- **Execution:** `subprocess.Popen` inside QThread + `QProcess` alternative for stdout.  
- **Metadata:** mutagen (full ID3/FLAC/Opus support).  
- **Fuzzy:** rapidfuzz (fast, no deps).  
- **File Watching:** watchdog (detect external deletions).  
- **Bundling:** PyInstaller (one-click exe; include FFmpeg binaries per platform).  
- **Extras:** requests (Spotify fallback if needed), pillow (cover preview).

### 4. Detailed Implementation Workflows

1. **New Batch** → Drag-drop URL or paste → Select Profile → Pre-flight save + exclusion → Async download → Post-tag + DB insert + .m3u.  
2. **Library View** → Tabular batches + expandable tracks → Search/filter → Batch-level CRUD.  
3. **Engine Settings** → Tabbed UI per phase with all flags + profile save/load.  
4. **Reconciliation** → Startup + manual trigger.  
5. **Export** → Zip batch or generate playlists.

### 5. Proactive Blindspot Mitigations (Systems-Level)

- **Spotify API Death:** Hybrid mode + credentials wizard + CSV import + MusicBrainz enrichment fallback. Detect auth failures and offer "Switch to yt-dlp + external metadata" path.  
- **Subprocess Blocking:** QThread + signal-slot for UI updates (progress, errors, cancel).  
- **File Desync:** watchdog + periodic SHA256 checks on tracks.  
- **Metadata Drift:** Post-download mutagen audit + manual tag editor.  
- **Rate Limits / Premium:** Cookie selector + threads throttle + user auth per profile.  
- **Large Libraries:** Virtualized QTableView + pagination.  
- **Cross-Platform Paths:** Use `pathlib` + platform-specific FFmpeg detection.  
- **Legal/UX:** Splash disclaimer ("Personal use only"); no cloud sync.  
- **Quality Loss:** `--bitrate disable` + opus/m4a default option.  
- **Dupe Prevention:** Leverage spotDL `--archive` + DB uniqueness on ISRC.

### 6. UI/UX Blueprint (Sophisticated Yet Simple)

- Modern dark/light theme (Qt stylesheets).  
- Sidebar: Library | New Batch | Settings | Blacklist.  
- Live download pane with log + cancel.  
- Drag-drop Spotify URLs anywhere.  
- Preview player (QMediaPlayer).  
- Statistics dashboard per batch (success %, total size).

### 7. Implementation Guidelines for You (the Agent)

**Start Here**  
1. Set up PySide6 + SQLAlchemy skeleton with sample Batch/Track models.  
2. Implement QThread wrapper that runs `subprocess` for `spotdl save` then full download, parsing output for progress (regex for % / track name).  
3. Build exclusion engine with rapidfuzz + ISRC blacklist.  
4. Add mutagen post-verification.  
5. Wire Engine Settings to dynamic flag dict → subprocess args.  

**Grey Areas — Research & Update Continuously**  
- **As you code Phase 1:** Immediately check https://github.com/spotDL/spotify-downloader/issues and Discord (https://discord.gg/xCa23pwJWY) for latest auth fixes/PRs. Test with your own Spotify app credentials. If still broken, prototype CSV + MusicBrainz fallback using `musicbrainzngs` library.  
- **GUI Phase:** Research PySide6 best practices for large QTableView + QProgressBar in threads (signals, not polling). Test QtMultimedia playback on Win/Mac/Linux.  
- **Bundling:** Research PyInstaller + FFmpeg embedding per platform (include `--download-ffmpeg` logic or static binaries).  
- **Alternatives Depth:** Clone and evaluate SomeDL, deezer-downloader, and yt-dlp + MusicBrainz workflows. Add as selectable "Download Engine" in settings.  
- **Performance/Scaling:** Profile large playlists (500+ tracks) — optimize threads and DB commits.  
- **Edge Cases:** Test explicit songs, live versions, unavailable tracks, YouTube Premium cookies, SponsorBlock.  
- **Sophistication Boost:** Add optional local AI tag correction (e.g., tiny MusicBrainz lookup) or auto .m3u playlist export to common players.  

**Quality Gates**  
- 100% flag coverage from CLI.  
- Zero UI freeze during downloads.  
- Batch integrity preserved even if files moved externally.  
- Graceful degradation on API failure.  
- Full cross-platform testing (Win/Mac/Linux VMs).  

**Deliverables Expectation**  
Produce a polished, production-ready desktop app that feels like a native music manager (think foobar2000 + spotDL superpowers). Prioritize metadata perfection and batch immutability. Update this document inline with new research findings.

You now have everything. Begin implementation. If a grey area blocks you, research it first — the goal is a truly sophisticated, future-proof tool. Proceed.