from pydantic import ConfigDict, BaseModel

from teltasync.utils import camel_to_snake


class TeltasyncBaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=camel_to_snake, populate_by_name=True)
