"""Authentication client and payload models for Teltonika API sessions."""

import asyncio
import time
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout, ContentTypeError
from pydantic import BaseModel, ValidationError

from teltasync.api_base import ApiResponse
from teltasync.error_codes import SESSION_REJECTED_CODES
from teltasync.exceptions import (
    TeltonikaAuthenticationError,
    TeltonikaConnectionError,
    TeltonikaInvalidCredentialsError,
)
from teltasync.utils import connection_error


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

    async def _open_json(
        self,
        make_request: Callable[[], AbstractAsyncContextManager[Any]],
    ) -> tuple[int, dict[str, Any] | None]:
        """Open a prepared request, returning its status and JSON body."""

        payload: dict[str, Any] | None
        try:
            async with make_request() as resp:
                status = resp.status
                try:
                    payload = await resp.json()
                except (ContentTypeError, ValueError):
                    payload = None
        except (ClientError, OSError, asyncio.TimeoutError, ValueError) as exc:
            raise connection_error(self.base_url, exc) from exc

        return status, payload

    async def authenticate(self) -> ApiResponse[TokenData]:
        """Authenticate with username/password and cache the returned token."""

        status, payload = await self._open_json(
            lambda: self.session.post(
                f"{self.base_url}/login",
                json={"username": self.username, "password": self.password},
                ssl=self.check_certificate,
                timeout=ClientTimeout(total=10.0),
            )
        )

        if payload is None:
            raise TeltonikaConnectionError(
                f"Unexpected non-JSON response from device during login (HTTP {status})"
            )

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
            _, payload = await self._open_json(
                lambda: self.session.post(
                    f"{self.base_url}/logout",
                    headers={"Authorization": f"Bearer {self._token}"},
                    ssl=self.check_certificate,
                    timeout=ClientTimeout(total=10.0),
                )
            )
        finally:
            self.clear_token()

        if payload is None:
            raise TeltonikaConnectionError(
                "Unexpected non-JSON response from device during logout"
            )
        return ApiResponse[LogoutResponse](**payload)

    @staticmethod
    def _inactive_session() -> ApiResponse[SessionStatusData]:
        """Return a fake response indicating no active session."""

        return ApiResponse[SessionStatusData](
            success=True,
            data=SessionStatusData(active=False),
        )

    async def get_session_status(self) -> ApiResponse[SessionStatusData]:
        """Return whether the current token still maps to an active session."""

        if self._token is None:
            return self._inactive_session()

        try:
            _, payload = await self._open_json(
                lambda: self.session.get(
                    f"{self.base_url}/session/status",
                    headers={"Authorization": f"Bearer {self._token}"},
                    ssl=self.check_certificate,
                    timeout=ClientTimeout(total=10.0),
                )
            )
        except TeltonikaConnectionError:
            payload = None

        if payload is None:
            self.clear_token()
            return self._inactive_session()

        try:
            response = ApiResponse[SessionStatusData](**payload)
        except ValidationError:
            self.clear_token()
            return self._inactive_session()

        if response.success and response.data and not response.data.active:
            self.clear_token()
        return response

    async def request_json(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Perform an authenticated request, recovering a rejected session."""

        status, payload = await self._send(method, endpoint, **kwargs)

        if self._is_session_rejected(status, payload):
            self.clear_token()
            await self.authenticate()
            status, payload = await self._send(method, endpoint, **kwargs)
            if self._is_session_rejected(status, payload):
                self.clear_token()
                raise TeltonikaAuthenticationError(
                    f"Device rejected the session after re-authentication (HTTP {status})"
                )

        if not isinstance(payload, dict):
            raise TeltonikaConnectionError(
                f"Unexpected response body from device (HTTP {status})"
            )

        return payload

    async def _send(
        self,
        method: str,
        endpoint: str,
        *,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> tuple[int, dict[str, Any] | None]:
        """Send a single authenticated request, returning the status and JSON body."""

        if self.is_token_expired():
            await self.authenticate()

        request_headers = dict(headers or {})
        if self._token:
            request_headers["Authorization"] = f"Bearer {self._token}"

        return await self._open_json(
            lambda: self.session.request(
                method,
                f"{self.base_url}/{endpoint.lstrip('/')}",
                headers=request_headers,
                ssl=self.check_certificate,
                **kwargs,
            )
        )

    @staticmethod
    def _is_session_rejected(status: int, payload: dict[str, Any] | None) -> bool:
        """Return whether the session was rejected."""

        if isinstance(payload, dict) and not payload.get("success"):
            if any(
                isinstance(error, dict) and error.get("code") in SESSION_REJECTED_CODES
                for error in (payload.get("errors") or [])
            ):
                return True
        return status == 401
