"""Tests for authentication functionality."""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiohttp import ClientConnectorError, ContentTypeError

from teltasync.auth import Auth
from teltasync.exceptions import (
    TeltonikaAuthenticationError,
    TeltonikaConnectionError,
    TeltonikaInvalidCredentialsError,
)


def _mock_context_response(json_response: Any, *, status: int = 200):
    """Build an async context manager yielding a mocked aiohttp response."""
    mock_response = AsyncMock()
    mock_response.json.return_value = json_response
    mock_response.status = status

    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_response
    mock_context_manager.__aexit__.return_value = None
    return mock_context_manager


def _non_json_response(*, status: int):
    """Build a context manager with a non-JSON response (e.g. HTML error page)."""
    mock_response = AsyncMock()
    mock_response.status = status
    mock_response.json.side_effect = ContentTypeError(Mock(), (), status=status)

    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_response
    mock_context_manager.__aexit__.return_value = None
    return mock_context_manager


@pytest.fixture(name="mock_session")
def fixture_mock_session():
    """Create a mock aiohttp session."""
    return Mock()


@pytest.fixture(name="auth")
def fixture_auth(mock_session):
    """Create an Auth instance with mock session."""
    return Auth(
        session=mock_session,
        base_url="https://test.device.com/api",
        username="test_user",
        password="test_pass",
        check_certificate=False,
    )


async def _authenticate_success(auth: Auth, mock_session, *, expires: int = 300):
    """Authenticate successfully and return the API response."""
    mock_session.post.return_value = _mock_context_response(
        {
            "success": True,
            "data": {
                "username": "test_user",
                "token": "test_token_123",
                "expires": expires,
            },
        }
    )
    return await auth.authenticate()


def test_authentication_error_creation():
    """Test TeltonikaAuthenticationError exception."""
    error = TeltonikaAuthenticationError("Test error")
    assert str(error) == "Test error"


def test_connection_error_creation():
    """Test TeltonikaConnectionError exception."""
    error = TeltonikaConnectionError("Connection failed")
    assert str(error) == "Connection failed"


@pytest.mark.asyncio
async def test_successful_authentication(auth, mock_session):
    """Test successful authentication flow."""
    response = await _authenticate_success(auth, mock_session)

    assert response.success is True
    assert response.data is not None
    assert response.data.username == "test_user"
    assert response.data.token == "test_token_123"
    assert response.data.expires == 300
    assert auth.is_authenticated is True
    assert auth.token == "test_token_123"


@pytest.mark.asyncio
async def test_authentication_with_connection_error(auth, mock_session):
    """Test authentication with connection error."""
    connection_error = ClientConnectorError(
        connection_key=Mock(ssl=False), os_error=OSError("Connection failed")
    )
    mock_session.post.side_effect = connection_error

    with pytest.raises(TeltonikaConnectionError) as exc_info:
        await auth.authenticate()

    assert "Cannot connect to device" in str(exc_info.value)
    assert exc_info.value.__cause__ is connection_error


@pytest.mark.asyncio
async def test_authentication_with_401_error(auth, mock_session):
    """Test authentication with 401 HTTP error."""
    mock_session.post.return_value = _mock_context_response(
        {"success": False, "data": None, "errors": None},
        status=401,
    )

    with pytest.raises(TeltonikaInvalidCredentialsError):
        await auth.authenticate()


@pytest.mark.asyncio
async def test_authentication_with_api_error(auth, mock_session):
    """Test authentication with API error response."""
    mock_session.post.return_value = _mock_context_response(
        {
            "success": False,
            "errors": [{"code": 121, "error": "Invalid credentials"}],
        }
    )

    with pytest.raises(TeltonikaAuthenticationError) as exc_info:
        await auth.authenticate()

    assert "Invalid credentials" in str(exc_info.value)
    assert "(code 121)" in str(exc_info.value)


@pytest.mark.asyncio
async def test_authentication_with_non_json_response(auth, mock_session):
    """Test a non-JSON login response produces a connection error."""
    mock_session.post.return_value = _non_json_response(status=502)

    with pytest.raises(TeltonikaConnectionError):
        await auth.authenticate()


@pytest.mark.asyncio
async def test_authentication_fails_without_error_details(auth, mock_session):
    """Test an unsuccessful login with no error details raises a generic auth error."""
    mock_session.post.return_value = _mock_context_response({"success": False})

    with pytest.raises(TeltonikaAuthenticationError):
        await auth.authenticate()


@pytest.mark.asyncio
async def test_logout_success(auth, mock_session):
    """Test successful logout."""
    await _authenticate_success(auth, mock_session)
    mock_session.post.return_value = _mock_context_response(
        {"success": True, "data": {"response": "Logged out successfully"}}
    )

    response = await auth.logout()

    assert response.success is True
    assert response.data is not None
    assert response.data.response == "Logged out successfully"
    assert auth.token is None
    assert auth.is_authenticated is False


@pytest.mark.asyncio
async def test_logout_no_active_session(auth):
    """Test logout with no active session."""
    response = await auth.logout()

    assert response.success is True
    assert response.data is not None
    assert response.data.response == "No active session"


@pytest.mark.asyncio
async def test_logout_with_non_json_response(auth, mock_session):
    """Test a non-JSON logout response produces a connection error and clears the token."""
    await _authenticate_success(auth, mock_session)
    mock_session.post.return_value = _non_json_response(status=502)

    with pytest.raises(TeltonikaConnectionError):
        await auth.logout()
    assert auth.token is None


@pytest.mark.parametrize(
    ("active", "token_expected"),
    [(True, True), (False, False)],
)
@pytest.mark.asyncio
async def test_session_status_with_existing_token(
    auth, mock_session, active, token_expected
):
    """Test session status behavior when a token exists."""
    await _authenticate_success(auth, mock_session)
    mock_session.get.return_value = _mock_context_response(
        {"success": True, "data": {"active": active}}
    )

    response = await auth.get_session_status()

    assert response.success is True
    assert response.data is not None
    assert response.data.active is active
    if token_expected:
        assert auth.token is not None
    else:
        assert auth.token is None
        assert auth.is_authenticated is False


@pytest.mark.asyncio
async def test_session_status_no_token(auth):
    """Test session status check with no token."""
    response = await auth.get_session_status()

    assert response.success is True
    assert response.data is not None
    assert response.data.active is False


@pytest.mark.asyncio
async def test_session_status_connection_error_degrades_to_inactive(auth, mock_session):
    """Test a transport error during a session status check returns inactive."""
    await _authenticate_success(auth, mock_session)
    mock_session.get.side_effect = ClientConnectorError(
        connection_key=Mock(ssl=False), os_error=OSError("Connection failed")
    )

    response = await auth.get_session_status()

    assert response.data is not None
    assert response.data.active is False
    assert auth.token is None


@pytest.mark.asyncio
async def test_session_status_invalid_body_degrades_to_inactive(auth, mock_session):
    """Test a wrongly shaped session status body returns inactive instead of raising."""
    await _authenticate_success(auth, mock_session)
    mock_session.get.return_value = _mock_context_response(
        {"success": True, "data": {}}
    )

    response = await auth.get_session_status()

    assert response.data is not None
    assert response.data.active is False
    assert auth.token is None


def test_is_token_expired_no_token(auth):
    """Test token expiry check with no token."""
    assert auth.is_token_expired() is True


@pytest.mark.parametrize(
    ("second_time", "expected"),
    [(1200.0, False), (1400.0, True)],
)
@pytest.mark.asyncio
async def test_is_token_expired_after_auth(auth, mock_session, second_time, expected):
    """Test token expiry check with valid and expired tokens."""
    with patch("teltasync.auth.time.time", side_effect=[1000.0, second_time]):
        await _authenticate_success(auth, mock_session, expires=300)
        assert auth.is_token_expired() is expected


@pytest.mark.asyncio
async def test_clear_token(auth, mock_session):
    """Test clearing token data."""
    await _authenticate_success(auth, mock_session)
    auth.clear_token()

    assert auth.token is None
    assert auth.is_authenticated is False
    assert auth.is_token_expired() is True


_SUCCESS_PAYLOAD = {"success": True, "data": {"value": 1}}
_REJECTED_BODY = {"success": False, "errors": [{"code": 123, "error": "Invalid JWT"}]}


@pytest.mark.asyncio
async def test_request_json_returns_payload(auth, mock_session):
    """Test a request returns the decoded JSON body when the session is valid."""
    await _authenticate_success(auth, mock_session)
    mock_session.request.return_value = _mock_context_response(_SUCCESS_PAYLOAD)

    assert await auth.request_json("GET", "modems/status") == _SUCCESS_PAYLOAD


@pytest.mark.asyncio
async def test_request_json_merges_caller_headers(auth, mock_session):
    """Test passed headers are merged with the Authorization header."""
    await _authenticate_success(auth, mock_session)
    mock_session.request.return_value = _mock_context_response(_SUCCESS_PAYLOAD)

    await auth.request_json("GET", "modems/status", headers={"X-Test": "1"})

    sent_headers = mock_session.request.call_args.kwargs["headers"]
    assert sent_headers["X-Test"] == "1"
    assert sent_headers["Authorization"] == "Bearer test_token_123"


@pytest.mark.asyncio
async def test_request_json_returns_non_auth_error_without_retry(auth, mock_session):
    """Test a non session API error is returned as-is, without re-authenticating."""
    await _authenticate_success(auth, mock_session)
    mock_session.post.reset_mock()
    error_payload = {
        "success": False,
        "errors": [{"code": 116, "error": "Invalid query parameter"}],
    }
    mock_session.request.return_value = _mock_context_response(error_payload)

    assert await auth.request_json("GET", "modems/status") == error_payload
    mock_session.post.assert_not_called()
    assert mock_session.request.call_count == 1


@pytest.mark.asyncio
async def test_request_json_authenticates_when_token_missing(auth, mock_session):
    """Test a request authenticates first when there is no cached token."""
    mock_session.post.return_value = _mock_context_response(
        {
            "success": True,
            "data": {"username": "test_user", "token": "tok", "expires": 300},
        }
    )
    mock_session.request.return_value = _mock_context_response(_SUCCESS_PAYLOAD)

    assert await auth.request_json("GET", "modems/status") == _SUCCESS_PAYLOAD
    mock_session.post.assert_called_once()


@pytest.mark.parametrize(
    "rejection",
    [
        _mock_context_response({"success": False}, status=401),
        _mock_context_response(_REJECTED_BODY, status=403),
        _mock_context_response(_REJECTED_BODY),
        _non_json_response(status=401),
    ],
    ids=["http_401", "http_403_with_code", "body_error_code", "non_json_401"],
)
@pytest.mark.asyncio
async def test_request_json_recovers_from_rejected_session(
    auth, mock_session, rejection
):
    """Test a rejected session is recovered by re-authenticating and retrying."""
    await _authenticate_success(auth, mock_session)
    mock_session.post.reset_mock()
    mock_session.request.side_effect = [
        rejection,
        _mock_context_response(_SUCCESS_PAYLOAD),
    ]

    assert await auth.request_json("GET", "modems/status") == _SUCCESS_PAYLOAD
    mock_session.post.assert_called_once()
    assert mock_session.request.call_count == 2


@pytest.mark.asyncio
async def test_request_json_passes_through_bare_forbidden(auth, mock_session):
    """Test a bare 403 (no session rejection code) is returned without re-authenticating."""
    await _authenticate_success(auth, mock_session)
    mock_session.post.reset_mock()
    forbidden_payload = {
        "success": False,
        "errors": [{"code": 116, "error": "Forbidden"}],
    }
    mock_session.request.return_value = _mock_context_response(
        forbidden_payload, status=403
    )

    assert await auth.request_json("GET", "modems/status") == forbidden_payload
    mock_session.post.assert_not_called()
    assert mock_session.request.call_count == 1


@pytest.mark.asyncio
async def test_request_json_raises_on_non_dict_body(auth, mock_session):
    """Test a top level JSON array body is a connection error, not an opaque TypeError."""
    await _authenticate_success(auth, mock_session)
    mock_session.request.return_value = _mock_context_response([1, 2, 3])

    with pytest.raises(TeltonikaConnectionError):
        await auth.request_json("GET", "modems/status")


@pytest.mark.asyncio
async def test_request_json_raises_when_rejected_after_retry(auth, mock_session):
    """Test a session still rejected after re-authentication raises an auth error."""
    await _authenticate_success(auth, mock_session)
    mock_session.request.side_effect = [
        _mock_context_response({"success": False}, status=401),
        _mock_context_response({"success": False}, status=401),
    ]

    with pytest.raises(TeltonikaAuthenticationError):
        await auth.request_json("GET", "modems/status")
    assert auth.token is None


@pytest.mark.asyncio
async def test_request_json_raises_invalid_credentials(auth, mock_session):
    """Test invalid credentials during the re-auth surface as a credentials error."""
    await _authenticate_success(auth, mock_session)
    mock_session.request.return_value = _mock_context_response(
        {"success": False}, status=401
    )
    mock_session.post.return_value = _mock_context_response(
        {"success": False, "data": None, "errors": None}, status=401
    )

    with pytest.raises(TeltonikaInvalidCredentialsError):
        await auth.request_json("GET", "modems/status")


@pytest.mark.asyncio
async def test_request_json_raises_connection_error_on_non_json(auth, mock_session):
    """Test a non-JSON, non auth response is a connection error (e.g. 502 during reboot)."""
    await _authenticate_success(auth, mock_session)
    mock_session.request.return_value = _non_json_response(status=502)

    with pytest.raises(TeltonikaConnectionError):
        await auth.request_json("GET", "modems/status")


@pytest.mark.asyncio
async def test_request_json_raises_connection_error_on_transport_error(
    auth, mock_session
):
    """Test a transport error during a request surfaces as a connection error."""
    await _authenticate_success(auth, mock_session)
    mock_session.request.side_effect = ClientConnectorError(
        connection_key=Mock(ssl=False), os_error=OSError("Connection failed")
    )

    with pytest.raises(TeltonikaConnectionError):
        await auth.request_json("GET", "modems/status")
