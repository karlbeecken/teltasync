"""Teltonika API library."""

from teltasync.exceptions import (
    TeltonikaAuthenticationError,
    TeltonikaConnectionError,
    TeltonikaException,
    TeltonikaInvalidCredentialsError,
)
from teltasync.teltasync import Teltasync

__version__ = "0.2.0"
__all__ = [
    "Teltasync",
    "TeltonikaException",
    "TeltonikaConnectionError",
    "TeltonikaAuthenticationError",
    "TeltonikaInvalidCredentialsError",
]
