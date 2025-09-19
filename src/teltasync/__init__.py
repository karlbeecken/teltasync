"""Teltonika API library."""

from teltasync.exceptions import (
    TeltonikaException,
    TeltonikaConnectionError,
    TeltonikaAuthenticationError,
    TeltonikaInvalidCredentialsError,
)
from teltasync.teltasync import Teltasync

__version__ = "0.1.0"
__all__ = [
    "Teltasync",
    "TeltonikaException",
    "TeltonikaConnectionError",
    "TeltonikaAuthenticationError",
    "TeltonikaInvalidCredentialsError",
]
