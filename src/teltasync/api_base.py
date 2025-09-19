from typing import Any, Generic, TypeVar

from pydantic import model_validator

from teltasync.base_model import TeltasyncBaseModel

T = TypeVar("T")


def _convert_na_to_none(value: Any) -> Any:
    if value == "N/A":
        return None
    if isinstance(value, dict):
        return {key: _convert_na_to_none(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_convert_na_to_none(item) for item in value]
    return value


class ApiError(TeltasyncBaseModel):
    code: int
    error: str
    source: str | None = None
    section: str | None = None


class ApiResponse(TeltasyncBaseModel, Generic[T]):
    success: bool
    data: T | None = None
    errors: list[ApiError] | None = None

    @model_validator(mode="before")
    @classmethod
    def _convert_na_strings(cls, values: Any) -> Any:
        if isinstance(values, dict):
            return _convert_na_to_none(values)
        return values

    def get_error_by_code(self, code: int) -> ApiError | None:
        if not self.errors:
            return None
        return next((error for error in self.errors if error.code == code), None)
