from __future__ import annotations

import json


def test_model_creation_and_basic_queries(session_factory):
    """Create Batch/Track rows and assert minimal query behavior."""
    Batch = session_factory["Batch"]
    Track = session_factory["Track"]
    SessionLocal = session_factory["SessionLocal"]

    with SessionLocal() as session:
        batch = Batch(
            source_url="https://open.spotify.com/playlist/test",
            profile_name="default",
            config_json=json.dumps({"format": "mp3"}),
            output_dir="/tmp/output",
        )
        session.add(batch)
        session.flush()

        session.add_all(
            [
                Track(batch_id=batch.id, title="Song A", artist="Artist A", status="QUEUED"),
                Track(batch_id=batch.id, title="Song B", artist="Artist B", status="FAILED"),
            ]
        )
        session.commit()

    with SessionLocal() as session:
        found = session.query(Batch).filter(Batch.source_url.like("%spotify.com%"))
        assert found.count() == 1

        queued = session.query(Track).filter(Track.status == "QUEUED").all()
        assert len(queued) == 1
        assert queued[0].title == "Song A"


def test_profile_json_write_read_shape(profile_config_cls, tmp_path):
    profile = profile_config_cls(audio={"format": "mp3", "bitrate": "320k"}, downloader={"threads": 4})
    out = tmp_path / "config.json"
    profile.write_to_file(out)

    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert "audio" in loaded
    assert "downloader" in loaded
    assert loaded["audio"]["format"] == "mp3"
    assert loaded["downloader"]["threads"] == 4
