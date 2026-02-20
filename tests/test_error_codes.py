"""Tests for Teltonika API error codes."""

from teltasync.error_codes import ERROR_DESCRIPTIONS, TeltonikaErrorCode


def test_error_descriptions_cover_all_enum_values():
    """Ensure every declared API code has a human-readable description."""
    enum_values = {code.value for code in TeltonikaErrorCode}
    description_values = set(ERROR_DESCRIPTIONS)
    assert description_values == enum_values


def test_error_descriptions_are_non_empty():
    """Ensure all error descriptions are non-empty strings."""
    assert all(
        isinstance(description, str) and description
        for description in ERROR_DESCRIPTIONS.values()
    )
