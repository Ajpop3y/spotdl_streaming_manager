import os
import re
import subprocess
from collections.abc import Callable, Iterable

from app.utils.ansi import strip_ansi

DOWNLOAD_SUCCESS = re.compile(r'Downloaded\s+"(.+)"')
DOWNLOAD_SKIP = re.compile(r'Skipping\s+(.+)')
DOWNLOAD_FAIL = re.compile(r'Failed to download\s+(.+)')


def build_env() -> dict:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["TERM"] = "dumb"
    env["NO_COLOR"] = "1"
    return env


def launch_spotdl_save(url: str, config_path: str, save_file_path: str) -> subprocess.Popen:
    return subprocess.Popen(
        ["spotdl", "save", url, "--config", config_path, "--save-file", save_file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=build_env(),
    )


def launch_spotdl_download(spotdl_file: str, config_path: str) -> subprocess.Popen:
    return subprocess.Popen(
        ["spotdl", spotdl_file, "--config", config_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=build_env(),
    )


class ExecutionEngine:
    """Headless subprocess stream parser for spotDL output."""

    def stream_download_output(
        self,
        process: subprocess.Popen,
        on_log_line: Callable[[str], None],
        on_track_finished: Callable[[str, bool, str], None],
    ) -> None:
        if process.stdout is None:
            return

        for raw_line in iter(process.stdout.readline, ""):
            line = strip_ansi(raw_line)
            stripped = line.strip()
            on_log_line(stripped)

            if m := DOWNLOAD_SUCCESS.search(line):
                on_track_finished(m.group(1), True, "")
            elif m := DOWNLOAD_FAIL.search(line):
                on_track_finished(m.group(1), False, stripped)


def parse_download_lines(raw_lines: Iterable[str]) -> list[tuple[str, bool, str]]:
    """Utility for tests: parse downloadable outcomes from raw stdout lines."""
    parsed: list[tuple[str, bool, str]] = []
    for raw_line in raw_lines:
        line = strip_ansi(raw_line)
        if m := DOWNLOAD_SUCCESS.search(line):
            parsed.append((m.group(1), True, ""))
        elif m := DOWNLOAD_FAIL.search(line):
            parsed.append((m.group(1), False, line.strip()))
    return parsed
