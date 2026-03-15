import json
from pathlib import Path

from app.config import ProfileConfig
from app.db import SessionLocal, init_db
from app.models import Batch, BatchStatus, Profile, Track, TrackStatus
from app.services.execution_engine import parse_download_lines
from app.services.exclusion_engine import run_exclusion
from app.services.playlist_exporter import export_batch_m3u8
from app.services.reconciler import LibraryReconciler
from app.utils.ansi import strip_ansi


def test_profile_config_write_to_file(tmp_path: Path):
    config = ProfileConfig(filter_results=False, cookie_file="cookies.txt")
    out = tmp_path / "config.json"
    config.write_to_file(out)

    parsed = json.loads(out.read_text(encoding="utf-8"))
    assert parsed["dont_filter_results"] is True
    assert parsed["cookie_file"] == "cookies.txt"


def test_ansi_strip_and_download_parse():
    raw = [
        "\x1b[32mDownloaded \"Artist - Song\"\x1b[0m\n",
        "Failed to download Artist - Bad\n",
    ]
    assert strip_ansi(raw[0]).startswith("Downloaded")
    parsed = parse_download_lines(raw)
    assert parsed == [
        ("Artist - Song", True, ""),
        ("Artist - Bad", False, "Failed to download Artist - Bad"),
    ]


def test_exclusion_engine(tmp_path: Path):
    save_file = tmp_path / "batch.spotdl"
    songs = [
        {"artist": "The Beatles", "name": "Hey Jude", "song_id": "spotify:track:1", "isrc": "ABC"},
        {"artist": "Daft Punk", "name": "Around the World", "song_id": "spotify:track:2", "isrc": "DEF"},
    ]
    save_file.write_text(json.dumps(songs), encoding="utf-8")

    kept, excluded = run_exclusion(save_file, [], ["Beatles - Hey Jude"])
    assert len(kept) == 1
    assert len(excluded) == 1


def test_reconciler_marks_missing_and_exports_m3u(tmp_path: Path):
    init_db()
    with SessionLocal() as session:
        batch = Batch(
            source_url="https://open.spotify.com/track/test",
            profile_name="Standard",
            config_json="{}",
            output_dir=str(tmp_path),
            status=BatchStatus.COMPLETE,
        )
        session.add(batch)
        session.flush()

        missing_track = Track(
            batch_id=batch.id,
            title="Missing",
            artist="Artist",
            status=TrackStatus.COMPLETE,
            file_path=str(tmp_path / "missing.m4a"),
            duration_s=123,
        )
        good_file = tmp_path / "good.m4a"
        good_file.write_text("x", encoding="utf-8")
        good_track = Track(
            batch_id=batch.id,
            title="Good",
            artist="Artist",
            status=TrackStatus.COMPLETE,
            file_path=str(good_file),
            duration_s=222,
        )
        session.add_all([missing_track, good_track])
        session.commit()

        reconciler = LibraryReconciler(session)
        degraded = reconciler.scan_recent(20)
        assert batch.id in degraded

        session.refresh(batch)
        session.refresh(missing_track)
        assert batch.status == BatchStatus.DEGRADED
        assert missing_track.status == TrackStatus.MISSING

        out = tmp_path / "playlist.m3u8"
        export_batch_m3u8(batch, [missing_track, good_track], out)

    content = (tmp_path / "playlist.m3u8").read_text(encoding="utf-8")
    assert "#EXTINF:222,Artist - Good" in content


def test_default_profile_inserted():
    init_db()
    with SessionLocal() as session:
        profiles = session.query(Profile).filter(Profile.name == "Standard").all()
        assert profiles
        assert profiles[0].is_default is True
