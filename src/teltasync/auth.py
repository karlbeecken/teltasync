"""Authentication client and payload models for Teltonika API sessions."""

import asyncio
import time

from aiohttp import ClientConnectorError, ClientError, ClientSession, ClientTimeout
from pydantic import BaseModel

from teltasync.api_base import ApiResponse
from teltasync.exceptions import (
    TeltonikaAuthenticationError,
    TeltonikaConnectionError,
    TeltonikaInvalidCredentialsError,
)


class TokenData(BaseModel):
    """Session token details returned by `/login`."""

    username: str
    token: str
    expires: int


class LogoutResponse(BaseModel):
    """Response body returned by `/logout`."""

    response: str


class SessionStatusData(BaseModel):
    """Boolean wrapper for session activity status."""

    active: bool


class Auth:  # pylint: disable=too-many-instance-attributes
    """Authenticated HTTP client used by other endpoint wrappers."""

    def __init__(
        self,
        session: ClientSession,
        base_url: str,
        username: str,
        password: str,
        check_certificate: bool = True,
    ):  # pylint: disable=too-many-arguments,too-many-positional-arguments
        """Initialize credentials and token state for API access."""

        self.session = session
        self.base_url = base_url
        self.username = username
        self.password = password
        self.check_certificate = check_certificate

        self._token: str | None = None
        self._token_expires: int | None = None
        self._token_username: str | None = None
        self._token_time: float | None = None
        self._authenticated = False

    @property
    def token(self) -> str | None:
        """Return the currently cached bearer token."""

        return self._token

    @property
    def is_authenticated(self) -> bool:
        """Return ``True`` when a token exists and auth state is active."""

        return self._authenticated and self._token is not None

    def is_token_expired(self) -> bool:
        """Return whether the cached token is missing or near expiration."""

        if not self._token or not self._token_expires or not self._token_time:
            return True
        return time.time() - self._token_time >= self._token_expires - 5

    def clear_token(self) -> None:
        """Clear all in-memory token metadata."""

        self._token = None
        self._token_expires = None
        self._token_username = None
        self._token_time = None
        self._authenticated = False

    async def authenticate(self) -> ApiResponse[TokenData]:
        """Authenticate with username/password and cache the returned token."""

        try:
            async with self.session.post(
                f"{self.base_url}/login",
                json={"username": self.username, "password": self.password},
                ssl=self.check_certificate,
                timeout=ClientTimeout(total=10.0),
            ) as resp:
                status = resp.status
                payload = await resp.json()
        except ClientConnectorError as exc:
            raise TeltonikaConnectionError(
                f"Cannot connect to device at {self.base_url}: {exc}",
            ) from exc
        except asyncio.TimeoutError as exc:
            raise TeltonikaConnectionError(
                f"Connection timeout to device at {self.base_url}",
            ) from exc
        except (ClientError, OSError, ValueError) as exc:
            message = str(exc)
            timeout_hit = "timeout" in message.lower()
            error_kind = "timeout" if timeout_hit else "error"
            raise TeltonikaConnectionError(
                f"Connection {error_kind} to device at {self.base_url}: {message}",
            ) from exc

        response = ApiResponse[TokenData](**payload)

        if response.success and response.data:
            self._token = response.data.token
            self._token_expires = response.data.expires
            self._token_username = response.data.username
            self._token_time = time.time()
            self._authenticated = True
            return response

        if status == 401:
            raise TeltonikaInvalidCredentialsError("Invalid username or password")

        if response.errors:
            err = response.errors[0]
            raise TeltonikaAuthenticationError(
                f"Authentication failed: {err.error} (code {err.code})",
            )

        raise TeltonikaAuthenticationError("Authentication failed")

    async def logout(self) -> ApiResponse[LogoutResponse]:
        """Invalidate the current session token on the device."""

        if self._token is None:
            return ApiResponse[LogoutResponse](
                success=True,
                data=LogoutResponse(response="No active session"),
            )

        try:
            async with self.session.post(
                f"{self.base_url}/logout",
                headers={"Authorization": f"Bearer {self._token}"},
                ssl=self.check_certificate,
                timeout=ClientTimeout(total=10.0),
            ) as resp:
                payload = await resp.json()
                return ApiResponse[LogoutResponse](**payload)
        finally:
            self.clear_token()

    async def get_session_status(self) -> ApiResponse[SessionStatusData]:
        """Return whether the current token still maps to an active session."""

        if self._token is None:
            return ApiResponse[SessionStatusData](
                success=True,
                data=SessionStatusData(active=False),
            )

        try:
            async with self.session.get(
                f"{self.base_url}/session/status",
                headers={"Authorization": f"Bearer {self._token}"},
                ssl=self.check_certificate,
                timeout=ClientTimeout(total=10.0),
            ) as resp:
                payload = await resp.json()
        except (ClientError, OSError, ValueError, asyncio.TimeoutError):
            self.clear_token()
            return ApiResponse[SessionStatusData](
                success=True,
                data=SessionStatusData(active=False),
            )

        response = ApiResponse[SessionStatusData](**payload)
        if response.success and response.data and not response.data.active:
            self.clear_token()
        return response

    async def request(self, method: str, endpoint: str, **kwargs):
        """Build an authenticated request context manager for callers."""

        if self.is_token_expired():
            await self.authenticate()

        headers = kwargs.pop("headers", {})
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        return self.session.request(
            method,
            f"{self.base_url}/{endpoint.lstrip('/')}",
            headers=headers,
            ssl=self.check_certificate,
            **kwargs,
        )
