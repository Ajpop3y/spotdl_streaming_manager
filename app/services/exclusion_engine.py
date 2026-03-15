import json
from pathlib import Path

from rapidfuzz import fuzz

from app.models import BlacklistEntry

FUZZY_THRESHOLD = 85


def load_spotdl_file(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_display_name(song: dict) -> str:
    return f"{song['artist']} - {song['name']}"


def run_exclusion(
    spotdl_path: Path,
    blacklist_db_entries: list[BlacklistEntry],
    text_exclusion_list: list[str],
) -> tuple[list[dict], list[dict]]:
    songs = load_spotdl_file(spotdl_path)
    keep, excluded = [], []

    blacklist_uris = {e.spotify_uri for e in blacklist_db_entries if e.spotify_uri}
    blacklist_isrcs = {e.isrc for e in blacklist_db_entries if e.isrc}

    for song in songs:
        uri = song.get("song_id")
        isrc = song.get("isrc")

        if uri in blacklist_uris or (isrc and isrc in blacklist_isrcs):
            excluded.append(song)
            continue

        display = build_display_name(song)
        is_excluded = any(
            fuzz.token_sort_ratio(display.lower(), entry.lower()) >= FUZZY_THRESHOLD
            for entry in text_exclusion_list
        )
        if is_excluded:
            excluded.append(song)
            continue

        keep.append(song)

    with open(spotdl_path, "w", encoding="utf-8") as f:
        json.dump(keep, f, ensure_ascii=False, indent=2)

    return keep, excluded


def blacklist_entries_from_fuzzy_matches(excluded_list: list[dict]) -> list[BlacklistEntry]:
    entries: list[BlacklistEntry] = []
    for song in excluded_list:
        entries.append(
            BlacklistEntry(
                spotify_uri=song.get("song_id"),
                isrc=song.get("isrc"),
                display_name=build_display_name(song),
                source="exclusion_engine",
            )
        )
    return entries
