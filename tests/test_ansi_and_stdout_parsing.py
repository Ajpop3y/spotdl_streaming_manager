from __future__ import annotations

import re

import pytest

from conftest import get_symbol


@pytest.fixture
def strip_ansi():
    return get_symbol(
        [
            "spotdl_streaming_manager.utils.ansi",
            "app.utils.ansi",
            "src.utils.ansi",
        ],
        "strip_ansi",
    )


@pytest.fixture
def progress_regex():
    module = get_symbol(
        [
            "spotdl_streaming_manager.execution",
            "app.execution",
            "src.execution",
        ],
        "PROGRESS_RE",
    )
    return module


def test_strip_ansi_removes_rich_escape_codes(strip_ansi):
    raw = "\x1b[32mDownloading\x1b[0m 55% | Artist - Song"
    cleaned = strip_ansi(raw)

    assert "\x1b[32m" not in cleaned
    assert cleaned == "Downloading 55% | Artist - Song"


def test_stdout_progress_regex_parses_cleaned_line(strip_ansi, progress_regex):
    line = "\x1b[36m⠸\x1b[0m 88.5% - Artist Name - Track Name"
    cleaned = strip_ansi(line)

    match = re.search(progress_regex, cleaned)
    assert match is not None
    assert float(match.group("percent")) == pytest.approx(88.5)
    assert "Artist Name" in match.group("track")
