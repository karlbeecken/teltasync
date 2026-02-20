"""Shared Pydantic base model configuration for API payload models."""

from pydantic import BaseModel, ConfigDict

from teltasync.utils import camel_to_snake


class TeltasyncBaseModel(BaseModel):
    """Base model with snake_case alias handling for Teltonika responses."""

    model_config = ConfigDict(alias_generator=camel_to_snake, populate_by_name=True)
