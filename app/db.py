from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import ProfileConfig
from app.models import Base, Profile

DEFAULT_DB_PATH = Path("spotdl_manager.db")
DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH}"

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Session:
    return SessionLocal()


def init_db(db_url: str | None = None) -> None:
    active_engine = engine if db_url is None else create_engine(db_url, future=True)
    local_session = SessionLocal if db_url is None else sessionmaker(bind=active_engine, autoflush=False, autocommit=False, future=True)

    Base.metadata.create_all(bind=active_engine)

    with local_session() as session:
        existing = session.scalar(select(Profile).where(Profile.name == "Standard"))
        if existing is None:
            default_profile = Profile(
                name="Standard",
                config_json=json.dumps(ProfileConfig().to_spotdl_config(), indent=2),
                is_default=True,
            )
            session.add(default_profile)
            session.commit()
