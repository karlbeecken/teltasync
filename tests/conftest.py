"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import pytest
from syrupy import SnapshotAssertion

from .syrupy import TeltasyncSnapshotExtension


@pytest.fixture(name="snapshot")
def snapshot_assertion(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the teltasync extension."""
    return snapshot.use_extension(TeltasyncSnapshotExtension)
