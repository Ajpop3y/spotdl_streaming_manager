from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProfileConfig:
    client_id: str = ""
    client_secret: str = ""
    user_auth: bool = False

    audio_provider: str = "youtube-music"
    filter_results: bool = True

    threads: int = 4
    cookie_file: str = ""
    sponsor_block: bool = False
    yt_dlp_args: str = ""

    format: str = "m4a"
    bitrate: str = "disable"
    output: str = "{artist}/{album}/{track-number} - {title}.{output-ext}"

    generate_lrc: bool = False
    skip_explicit: bool = False
    save_errors: str = ""
    archive: str = ""

    def to_spotdl_config(self) -> dict:
        cfg = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "user_auth": self.user_auth,
            "audio_provider": self.audio_provider,
            "threads": self.threads,
            "format": self.format,
            "bitrate": self.bitrate,
            "output": self.output,
            "generate_lrc": self.generate_lrc,
            "skip_explicit": self.skip_explicit,
        }
        if not self.filter_results:
            cfg["dont_filter_results"] = True
        if self.cookie_file:
            cfg["cookie_file"] = self.cookie_file
        if self.sponsor_block:
            cfg["sponsor_block"] = True
        if self.yt_dlp_args:
            cfg["yt_dlp_args"] = self.yt_dlp_args
        if self.save_errors:
            cfg["save_errors"] = self.save_errors
        if self.archive:
            cfg["archive"] = self.archive
        return cfg

    def write_to_file(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_spotdl_config(), indent=2), encoding="utf-8")
