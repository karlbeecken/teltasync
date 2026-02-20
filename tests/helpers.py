"""Shared helpers for fixture-backed tests."""

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(*parts: str) -> dict[str, Any]:
    """Load a JSON fixture from ``tests/fixtures``."""
    fixture_path = FIXTURES_DIR.joinpath(*parts)
    with open(fixture_path, encoding="utf-8") as fixture_file:
        return json.load(fixture_file)
