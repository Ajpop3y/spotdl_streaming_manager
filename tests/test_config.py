from __future__ import annotations

import json

from app.config import ProfileConfig


def test_profile_config_write_to_file_emits_spotdl_compatible_json(tmp_path) -> None:
    config = ProfileConfig(
        client_id="cid",
        client_secret="secret",
        user_auth=True,
        filter_results=False,
        threads=8,
        sponsor_block=True,
        yt_dlp_args="--extractor-retries 5",
        archive="/tmp/archive.txt",
    )

    target = tmp_path / "profile.json"
    config.write_to_file(target)

    loaded = json.loads(target.read_text(encoding="utf-8"))

    assert loaded["client_id"] == "cid"
    assert loaded["client_secret"] == "secret"
    assert loaded["user_auth"] is True
    assert loaded["audio_provider"] == "youtube-music"
    assert loaded["threads"] == 8
    assert loaded["dont_filter_results"] is True
    assert loaded["sponsor_block"] is True
    assert loaded["yt_dlp_args"] == "--extractor-retries 5"
    assert loaded["archive"] == "/tmp/archive.txt"
    assert "output" in loaded
