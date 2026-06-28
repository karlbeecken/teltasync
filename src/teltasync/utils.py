"""Utility helpers shared across the teltasync package."""

import asyncio
import re

from aiohttp import ClientConnectorError

from teltasync.exceptions import TeltonikaConnectionError


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def connection_error(base_url: str, exc: Exception) -> TeltonikaConnectionError:
    """Map aiohttp error to TeltonikaConnectionError."""
    if isinstance(exc, ClientConnectorError):
        message = f"Cannot connect to device at {base_url}: {exc}"
    elif isinstance(exc, asyncio.TimeoutError):
        message = f"Connection timeout to device at {base_url}"
    else:
        message = f"Connection error to device at {base_url}: {exc}"
    return TeltonikaConnectionError(message)
