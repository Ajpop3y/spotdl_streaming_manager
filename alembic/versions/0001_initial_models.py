"""initial models

Revision ID: 0001_initial_models
Revises: 
Create Date: 2026-03-15 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_models"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.Enum("PENDING", "RUNNING", "COMPLETE", "PARTIAL", "FAILED", "DEGRADED", "ARCHIVED", name="batchstatus"), nullable=False),
        sa.Column("profile_name", sa.String(), nullable=False),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("spotdl_save_path", sa.String(), nullable=True),
        sa.Column("output_dir", sa.String(), nullable=False),
        sa.Column("m3u_path", sa.String(), nullable=True),
        sa.Column("total_tracks", sa.Integer(), nullable=False),
        sa.Column("succeeded", sa.Integer(), nullable=False),
        sa.Column("excluded", sa.Integer(), nullable=False),
        sa.Column("failed", sa.Integer(), nullable=False),
    )

    op.create_table(
        "blacklist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("spotify_uri", sa.String(), nullable=True, unique=True),
        sa.Column("isrc", sa.String(), nullable=True),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
    )

    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "tracks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("batches.id"), nullable=False),
        sa.Column("spotify_uri", sa.String(), nullable=True),
        sa.Column("isrc", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("artist", sa.String(), nullable=False),
        sa.Column("album", sa.String(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("duration_s", sa.Integer(), nullable=True),
        sa.Column("explicit", sa.Boolean(), nullable=False),
        sa.Column("cover_url", sa.String(), nullable=True),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("status", sa.Enum("QUEUED", "EXCLUDED", "DOWNLOADING", "TAGGING", "COMPLETE", "FAILED", "MISSING", name="trackstatus"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("tags_verified", sa.Boolean(), nullable=False),
        sa.Column("art_embedded", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_tracks_spotify_uri", "tracks", ["spotify_uri"])
    op.create_index("ix_tracks_isrc", "tracks", ["isrc"])

    op.create_table(
        "file_operations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("batches.id"), nullable=False),
        sa.Column("track_id", sa.Integer(), sa.ForeignKey("tracks.id"), nullable=True),
        sa.Column("op_type", sa.String(), nullable=False),
        sa.Column("source_path", sa.String(), nullable=True),
        sa.Column("dest_path", sa.String(), nullable=True),
        sa.Column("performed_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("file_operations")
    op.drop_index("ix_tracks_isrc", table_name="tracks")
    op.drop_index("ix_tracks_spotify_uri", table_name="tracks")
    op.drop_table("tracks")
    op.drop_table("profiles")
    op.drop_table("blacklist")
    op.drop_table("batches")

    sa.Enum(name="trackstatus").drop(op.get_bind(), checkfirst=False)
    sa.Enum(name="batchstatus").drop(op.get_bind(), checkfirst=False)
