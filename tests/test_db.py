from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import init_db
from app.models import Profile


def test_init_db_inserts_default_profile_once(tmp_path) -> None:
    db_path = tmp_path / "manager.db"
    db_url = f"sqlite:///{db_path}"

    init_db(db_url)
    init_db(db_url)

    engine = create_engine(db_url, future=True)
    with Session(engine) as session:
        rows = session.scalars(select(Profile).where(Profile.name == "Standard")).all()

    assert len(rows) == 1
    assert rows[0].is_default is True
    assert '"audio_provider": "youtube-music"' in rows[0].config_json
