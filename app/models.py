import json
from datetime import datetime
from pathlib import Path
from sqlalchemy import (
    String, Integer, DateTime, Boolean, Text, ForeignKey, Enum
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    pass


class BatchStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"
    DEGRADED = "degraded"
    ARCHIVED = "archived"


class TrackStatus(str, enum.Enum):
    QUEUED = "queued"
    EXCLUDED = "excluded"
    DOWNLOADING = "downloading"
    TAGGING = "tagging"
    COMPLETE = "complete"
    FAILED = "failed"
    MISSING = "missing"


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_url: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[BatchStatus] = mapped_column(Enum(BatchStatus), default=BatchStatus.PENDING)

    profile_name: Mapped[str] = mapped_column(String, nullable=False)
    config_json: Mapped[str] = mapped_column(Text, nullable=False)
    spotdl_save_path: Mapped[str | None] = mapped_column(String, nullable=True)

    output_dir: Mapped[str] = mapped_column(String, nullable=False)
    m3u_path: Mapped[str | None] = mapped_column(String, nullable=True)

    total_tracks: Mapped[int] = mapped_column(Integer, default=0)
    succeeded: Mapped[int] = mapped_column(Integer, default=0)
    excluded: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)

    tracks: Mapped[list["Track"]] = relationship("Track", back_populates="batch", cascade="all, delete-orphan")
    file_ops: Mapped[list["FileOperation"]] = relationship("FileOperation", back_populates="batch")


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), nullable=False)

    spotify_uri: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    isrc: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    title: Mapped[str] = mapped_column(String, nullable=False)
    artist: Mapped[str] = mapped_column(String, nullable=False)
    album: Mapped[str | None] = mapped_column(String, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    explicit: Mapped[bool] = mapped_column(Boolean, default=False)
    cover_url: Mapped[str | None] = mapped_column(String, nullable=True)

    file_path: Mapped[str | None] = mapped_column(String, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[TrackStatus] = mapped_column(Enum(TrackStatus), default=TrackStatus.QUEUED)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    tags_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    art_embedded: Mapped[bool] = mapped_column(Boolean, default=False)

    batch: Mapped["Batch"] = relationship("Batch", back_populates="tracks")


class BlacklistEntry(Base):
    __tablename__ = "blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    spotify_uri: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    isrc: Mapped[str | None] = mapped_column(String, nullable=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    source: Mapped[str] = mapped_column(String, default="manual")


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    config_json: Mapped[str] = mapped_column(Text, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FileOperation(Base):
    __tablename__ = "file_operations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), nullable=False)
    track_id: Mapped[int | None] = mapped_column(ForeignKey("tracks.id"), nullable=True)
    op_type: Mapped[str] = mapped_column(String, nullable=False)
    source_path: Mapped[str | None] = mapped_column(String, nullable=True)
    dest_path: Mapped[str | None] = mapped_column(String, nullable=True)
    performed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    batch: Mapped["Batch"] = relationship("Batch", back_populates="file_ops")
