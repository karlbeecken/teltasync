"""Exceptions for the Teltonika API client."""


class TeltonikaException(Exception):
    """Base exception for all Teltonika API client errors."""


class TeltonikaConnectionError(TeltonikaException):
    """Exception raised for connection-related issues with the Teltonika API."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


class TeltonikaAuthenticationError(TeltonikaException):
    """Exception raised for authentication failures with the Teltonika API."""

    def __init__(self, message: str, error_code: int | None = None):
        super().__init__(message)
        self.error_code = error_code


class TeltonikaInvalidCredentialsError(TeltonikaAuthenticationError):
    """Exception raised specifically for invalid username or password errors."""

    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message, 121)
