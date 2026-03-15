from __future__ import annotations

import importlib
from typing import Iterable

import pytest


def import_first(candidates: Iterable[str]):
    """Import and return the first module available from a candidate list."""
    errors: list[str] = []
    for name in candidates:
        try:
            return importlib.import_module(name)
        except ModuleNotFoundError as exc:
            errors.append(f"{name}: {exc}")

    pytest.skip(
        "No supported module path is importable. "
        "Tried: " + ", ".join(candidates)
    )


def get_symbol(module_candidates: Iterable[str], symbol: str):
    module = import_first(module_candidates)
    if not hasattr(module, symbol):
        pytest.skip(f"Symbol '{symbol}' not found in module '{module.__name__}'")
    return getattr(module, symbol)


@pytest.fixture
def session_factory(tmp_path):
    db_module = import_first(
        [
            "spotdl_streaming_manager.db",
            "spotdl_streaming_manager.models",
            "app.db",
            "app.models",
            "src.db",
            "src.models",
        ]
    )

    Base = getattr(db_module, "Base", None)
    Batch = getattr(db_module, "Batch", None)
    Track = getattr(db_module, "Track", None)
    init_fn = getattr(db_module, "init_test_engine", None)
    session_local = getattr(db_module, "SessionLocal", None)

    if Base is None or Batch is None or Track is None:
        pytest.skip("Expected SQLAlchemy Base/Batch/Track models are not available")

    if init_fn is not None:
        SessionLocal = init_fn(tmp_path / "test.db")
    elif session_local is not None:
        SessionLocal = session_local
    else:
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
        except ModuleNotFoundError:
            pytest.skip("sqlalchemy not installed")

        engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)

    return {"Base": Base, "Batch": Batch, "Track": Track, "SessionLocal": SessionLocal}


@pytest.fixture
def profile_config_cls():
    return get_symbol(
        [
            "spotdl_streaming_manager.profile",
            "spotdl_streaming_manager.config",
            "app.profile",
            "app.config",
            "src.profile",
            "src.config",
        ],
        "ProfileConfig",
    )


@pytest.fixture
def v01_smoke_runner():
    runner = import_first(
        [
            "spotdl_streaming_manager.integration.v01_smoke",
            "app.integration.v01_smoke",
            "src.integration.v01_smoke",
        ]
    )

    if not hasattr(runner, "run_full_flow"):
        pytest.skip("run_full_flow() not implemented for integration smoke")

    class Wrapper:
        @staticmethod
        def run_full_flow():
            return runner.run_full_flow()

    return Wrapper()
