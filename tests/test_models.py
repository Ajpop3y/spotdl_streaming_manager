from __future__ import annotations

import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import ProfileConfig
from app.models import Base, Batch, BlacklistEntry, FileOperation, Profile, Track


def test_model_create_query_roundtrip() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        batch = Batch(
            source_url="https://open.spotify.com/playlist/abc",
            profile_name="Standard",
            config_json=json.dumps(ProfileConfig().to_spotdl_config()),
            output_dir="/tmp/music",
        )
        session.add(batch)
        session.flush()

        track = Track(
            batch_id=batch.id,
            spotify_uri="spotify:track:123",
            isrc="US1234567890",
            title="Song",
            artist="Artist",
        )
        blacklist = BlacklistEntry(
            spotify_uri="spotify:track:blacklisted",
            display_name="Artist - Blacklisted Song",
        )
        profile = Profile(
            name="Loud",
            config_json=json.dumps(ProfileConfig(format="mp3").to_spotdl_config()),
            is_default=False,
        )
        op = FileOperation(
            batch_id=batch.id,
            track_id=None,
            op_type="archive",
            source_path="/tmp/music/Song.m4a",
            dest_path="/tmp/archive/Song.m4a",
        )

        session.add_all([track, blacklist, profile, op])
        session.commit()

    with Session(engine) as session:
        loaded_batch = session.scalar(select(Batch).where(Batch.source_url.like("%spotify%")))
        loaded_track = session.scalar(select(Track).where(Track.spotify_uri == "spotify:track:123"))
        loaded_blacklist = session.scalar(select(BlacklistEntry).where(BlacklistEntry.spotify_uri.is_not(None)))
        loaded_profile = session.scalar(select(Profile).where(Profile.name == "Loud"))
        loaded_op = session.scalar(select(FileOperation).where(FileOperation.op_type == "archive"))

        assert loaded_batch is not None
        assert loaded_track is not None
        assert loaded_blacklist is not None
        assert loaded_profile is not None
        assert loaded_op is not None
        assert loaded_track.batch_id == loaded_batch.id
