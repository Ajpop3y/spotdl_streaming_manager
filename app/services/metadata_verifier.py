from dataclasses import dataclass, field
from pathlib import Path

from mutagen import File as MutagenFile
from mutagen.id3 import APIC, ID3, ID3NoHeaderError


@dataclass
class VerificationResult:
    has_art: bool = False
    has_title: bool = False
    has_artist: bool = False
    id3_version: tuple | None = None
    issues: list[str] = field(default_factory=list)


def verify_track(file_path: Path) -> VerificationResult:
    result = VerificationResult()
    audio = MutagenFile(file_path)
    if audio is None:
        result.issues.append("tag verification failed")
        return result

    tags = getattr(audio, "tags", None)
    if tags is None:
        result.issues.append("missing tags")
        return result

    if isinstance(tags, ID3):
        result.id3_version = tags.version
        result.has_title = bool(tags.getall("TIT2"))
        result.has_artist = bool(tags.getall("TPE1"))
        result.has_art = bool(tags.getall("APIC"))
    else:
        result.has_title = "title" in tags
        result.has_artist = "artist" in tags
        pictures = getattr(audio, "pictures", None)
        covr = tags.get("covr") if hasattr(tags, "get") else None
        result.has_art = bool(pictures) or bool(covr)

    if not result.has_art:
        result.issues.append("missing embedded art")
    if not result.has_title:
        result.issues.append("missing title")
    if not result.has_artist:
        result.issues.append("missing artist")
    if result.id3_version and result.id3_version[:2] != (2, 4):
        result.issues.append(f"non-canonical id3 version: {result.id3_version}")

    return result


def normalize_id3_version(file_path: Path) -> bool:
    try:
        id3 = ID3(file_path)
    except ID3NoHeaderError:
        return False

    if id3.version[:2] == (2, 3):
        id3.save(file_path, v2_version=4)
        return True
    return False
