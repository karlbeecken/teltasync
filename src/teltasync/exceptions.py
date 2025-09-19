class TeltonikaException(Exception):
    pass


class TeltonikaConnectionError(TeltonikaException):
    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


class TeltonikaAuthenticationError(TeltonikaException):
    def __init__(self, message: str, error_code: int | None = None):
        super().__init__(message)
        self.error_code = error_code


class TeltonikaInvalidCredentialsError(TeltonikaAuthenticationError):
    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message, 121)
