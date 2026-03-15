from pathlib import Path

from app.config import ProfileConfig


def write_profile_config(profile_config: ProfileConfig, path: Path) -> None:
    profile_config.write_to_file(path)
