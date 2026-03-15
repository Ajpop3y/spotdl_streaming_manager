from pathlib import Path

from sqlalchemy import desc, select

from app.models import Batch, BatchStatus, Track, TrackStatus


class LibraryReconciler:
    def __init__(self, session):
        self.session = session

    def scan_recent(self, n: int = 20) -> list[int]:
        batches = self.session.scalars(select(Batch).order_by(desc(Batch.created_at)).limit(n)).all()
        degraded_batch_ids: list[int] = []

        for batch in batches:
            missing_any = False
            tracks = self.session.scalars(select(Track).where(Track.batch_id == batch.id)).all()
            for track in tracks:
                if track.file_path and not Path(track.file_path).exists():
                    track.status = TrackStatus.MISSING
                    missing_any = True

            if missing_any:
                batch.status = BatchStatus.DEGRADED
                degraded_batch_ids.append(batch.id)

        self.session.commit()
        return degraded_batch_ids
