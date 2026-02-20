"""Syrupy extension for teltasync snapshots."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import TYPE_CHECKING, Any, cast

from pydantic import BaseModel
from syrupy.extensions.amber import AmberDataSerializer, AmberSnapshotExtension

if TYPE_CHECKING:
    from syrupy.types import SerializableData


class TeltasyncSnapshotSerializer(AmberDataSerializer):
    """Serializer that keeps snapshot tests model-first."""

    @classmethod
    def _serialize(cls, data: SerializableData, **kwargs: Any) -> str:
        """Serialize pydantic models and dataclasses as deterministic dicts."""
        serializable_data = data
        if isinstance(data, BaseModel):
            serializable_data = data.model_dump(
                by_alias=True,
                exclude_none=True,
                exclude_computed_fields=True,
            )
        elif is_dataclass(data) and not isinstance(data, type):
            serializable_data = asdict(cast(Any, data))

        return super()._serialize(serializable_data, **kwargs)


class TeltasyncSnapshotExtension(AmberSnapshotExtension):
    """Syrupy extension for teltasync tests."""

    VERSION = "3"
    serializer_class: type[AmberDataSerializer] = TeltasyncSnapshotSerializer
