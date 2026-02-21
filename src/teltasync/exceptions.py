"""Exceptions for the Teltonika API client."""

class TeltonikaException(Exception):
    """Base exception for all Teltonika API client errors."""


class TeltonikaConnectionError(TeltonikaException):
    """Exception raised for connection-related issues with the Teltonika API."""


class TeltonikaAuthenticationError(TeltonikaException):
    """Exception raised for authentication failures with the Teltonika API."""


class TeltonikaInvalidCredentialsError(TeltonikaAuthenticationError):
    """Exception raised specifically for invalid username or password errors."""
