from __future__ import annotations

from conftest import get_symbol


def test_reconciler_state_transitions_for_missing_and_restored_file(tmp_path):
    reconcile_batch = get_symbol(
        [
            "spotdl_streaming_manager.reconciler",
            "app.reconciler",
            "src.reconciler",
        ],
        "reconcile_batch",
    )

    file_path = tmp_path / "track.mp3"
    file_path.write_bytes(b"ok")

    track = type("Track", (), {"file_path": str(file_path), "status": "SUCCEEDED", "error_message": None})()
    batch = type("Batch", (), {"status": "COMPLETE", "tracks": [track]})()

    first = reconcile_batch(batch)
    assert first.batch_status in {"COMPLETE", "HEALTHY"}

    file_path.unlink()
    second = reconcile_batch(batch)
    assert second.batch_status in {"DEGRADED", "ARCHIVED"}

    file_path.write_bytes(b"ok")
    third = reconcile_batch(batch)
    assert third.batch_status in {"COMPLETE", "HEALTHY", "RECOVERED"}
