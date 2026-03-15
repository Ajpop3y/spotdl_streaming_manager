from __future__ import annotations

import os

import pytest


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_SPOTDL_V01_SMOKE") != "1",
    reason="Set RUN_SPOTDL_V01_SMOKE=1 with Spotify credentials and spotdl installed",
)
def test_v0_1_success_flow_smoke(v01_smoke_runner):
    """Exact v0.1 flow: URL -> filter -> download -> tag verify -> m3u8 -> LibraryView."""
    report = v01_smoke_runner.run_full_flow()

    assert report["save_phase_ok"] is True
    assert report["exclusion_phase_ok"] is True
    assert report["download_phase_ok"] is True
    assert report["mutagen_verify_ok"] is True
    assert report["m3u8_export_ok"] is True
    assert report["library_view_visible"] is True
