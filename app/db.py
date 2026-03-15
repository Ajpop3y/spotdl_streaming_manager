import json
from contextlib import contextmanager
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import ProfileConfig
from app.models import Base, Profile

DATABASE_URL = "sqlite:///spotdl_manager.db"

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _default_profile() -> Profile:
    cfg = ProfileConfig(
        audio_provider="youtube-music",
        threads=4,
        format="m4a",
        bitrate="disable",
        output="{artist}/{album}/{track-number} - {title}.{output-ext}",
        filter_results=True,
        generate_lrc=False,
        skip_explicit=False,
    )
    return Profile(name="Standard", config_json=json.dumps(cfg.to_spotdl_config()), is_default=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        existing = session.scalar(select(Profile).where(Profile.name == "Standard"))
        if existing is None:
            session.add(_default_profile())
            session.commit()


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
