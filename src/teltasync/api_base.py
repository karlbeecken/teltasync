"""Base models for Teltonika API responses."""

from typing import Any, Generic, TypeVar

from pydantic import model_validator

from teltasync.base_model import TeltasyncBaseModel

T = TypeVar("T")


def _convert_na_to_none(value: Any) -> Any:
    """
    For some reason, the API sometimes returns "N/A" strings instead of a proper null value.
    This function is there to covert such values to a correct None (recursively).
    """
    if value == "N/A":
        return None
    if isinstance(value, dict):
        return {key: _convert_na_to_none(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_convert_na_to_none(item) for item in value]
    return value


class ApiError(TeltasyncBaseModel):
    """Model representing an error returned by the API."""

    code: int
    error: str
    source: str | None = None
    section: str | None = None


class ApiResponse(TeltasyncBaseModel, Generic[T]):
    """
    Generic response model for API calls. Contains success state, and if applicable, data
    and/or errors.
    """

    success: bool
    data: T | None = None
    errors: list[ApiError] | None = None

    @model_validator(mode="before")
    @classmethod
    def _convert_na_strings(cls, values: Any) -> Any:
        """Convert "N/A" strings to None before pydantic validation."""
        return _convert_na_to_none(values)

    def get_error_by_code(self, code: int) -> ApiError | None:
        """Helper method to retrieve an error by its code."""
        return next(
            (error for error in (self.errors or []) if error.code == code),
            None,
        )
