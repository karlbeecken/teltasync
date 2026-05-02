"""Teltonika API library."""

from teltasync.exceptions import (
    TeltonikaAuthenticationError,
    TeltonikaConnectionError,
    TeltonikaException,
    TeltonikaInvalidCredentialsError,
)
from teltasync.teltasync import Teltasync

__version__ = "0.3.1"
__all__ = [
    "Teltasync",
    "TeltonikaException",
    "TeltonikaConnectionError",
    "TeltonikaAuthenticationError",
    "TeltonikaInvalidCredentialsError",
]
