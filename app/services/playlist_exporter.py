from pathlib import Path

from app.models import Batch, Track, TrackStatus


def export_batch_m3u8(batch: Batch, tracks: list[Track], output_path: Path):
    lines = ["#EXTM3U", ""]
    for track in tracks:
        if track.status != TrackStatus.COMPLETE or not track.file_path:
            continue
        file_path = Path(track.file_path)
        rel_path = file_path.relative_to(output_path.parent)
        duration = track.duration_s or -1
        artist_title = f"{track.artist} - {track.title}"
        lines.append(f"#EXTINF:{duration},{artist_title}")
        lines.append(str(rel_path))

    output_path.write_text("\n".join(lines), encoding="utf-8")
