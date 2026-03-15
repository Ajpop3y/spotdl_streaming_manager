from __future__ import annotations

import json

from conftest import get_symbol


def test_spotdl_exclusion_filtering_and_sanitized_output(tmp_path):
    run_exclusion = get_symbol(
        [
            "spotdl_streaming_manager.exclusion_engine",
            "app.exclusion_engine",
            "src.exclusion_engine",
        ],
        "run_exclusion",
    )

    source = [
        {"name": "Song Keep", "artist": "Artist Keep", "song_id": "spotify:track:1", "isrc": "ISRC1"},
        {"name": "Song Remove", "artist": "Artist Remove", "song_id": "spotify:track:2", "isrc": "ISRC2"},
    ]

    spotdl_path = tmp_path / "batch.spotdl"
    spotdl_path.write_text(json.dumps(source), encoding="utf-8")

    result = run_exclusion(
        spotdl_path=spotdl_path,
        blacklist_uris={"spotify:track:2"},
        blacklist_isrcs=set(),
        text_exclusion_list=["Artist Remove - Song Remove"],
        fuzzy_threshold=90,
    )

    sanitized = json.loads(spotdl_path.read_text(encoding="utf-8"))

    assert len(sanitized) == 1
    assert sanitized[0]["song_id"] == "spotify:track:1"
    assert result.excluded_count == 1
    assert result.kept_count == 1
