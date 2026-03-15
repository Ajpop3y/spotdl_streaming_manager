from __future__ import annotations

from pathlib import Path

from conftest import get_symbol


def test_metadata_verification_marks_verified(monkeypatch, tmp_path):
    verify_track_tags = get_symbol(
        [
            "spotdl_streaming_manager.metadata_verifier",
            "app.metadata_verifier",
            "src.metadata_verifier",
        ],
        "verify_track_tags",
    )

    audio_file = tmp_path / "ok.mp3"
    audio_file.write_bytes(b"fake-mp3")

    class FakeAudio:
        tags = {"TIT2": "Song", "TPE1": "Artist", "APIC:": b"img"}

    monkeypatch.setattr("mutagen.File", lambda *_args, **_kwargs: FakeAudio())
    result = verify_track_tags(Path(audio_file))

    assert result.tags_verified is True
    assert result.art_embedded is True


def test_playlist_export_formatting(tmp_path):
    export_batch_m3u8 = get_symbol(
        [
            "spotdl_streaming_manager.playlist_export",
            "app.playlist_export",
            "src.playlist_export",
        ],
        "export_batch_m3u8",
    )

    out = tmp_path / "batch.m3u8"
    batch = type("Batch", (), {"id": 17, "source_url": "https://open.spotify.com/playlist/x"})()
    tracks = [
        type("Track", (), {"artist": "A", "title": "Song A", "duration_s": 201, "file_path": "/music/a.mp3"})(),
        type("Track", (), {"artist": "B", "title": "Song B", "duration_s": 99, "file_path": "/music/b.mp3"})(),
    ]

    export_batch_m3u8(batch=batch, tracks=tracks, output_path=out)
    content = out.read_text(encoding="utf-8").splitlines()

    assert content[0] == "#EXTM3U"
    assert any(line.startswith("#EXTINF:201,A - Song A") for line in content)
    assert any(line == "/music/a.mp3" for line in content)
    assert any("Batch 17" in line for line in content if line.startswith("#"))
