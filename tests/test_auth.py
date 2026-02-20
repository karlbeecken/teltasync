"""Tests for authentication functionality."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiohttp import ClientConnectorError

from teltasync.auth import Auth
from teltasync.exceptions import (
    TeltonikaAuthenticationError,
    TeltonikaConnectionError,
    TeltonikaInvalidCredentialsError,
)


def _mock_context_response(json_response: dict, *, status: int = 200):
    """Build an async context manager yielding a mocked aiohttp response."""
    mock_response = AsyncMock()
    mock_response.json.return_value = json_response
    mock_response.status = status

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
    error = TeltonikaAuthenticationError("Test error", 121)
    assert str(error) == "Test error"
    assert error.error_code == 121


def test_connection_error_creation():
    """Test TeltonikaConnectionError exception."""
    original_error = Exception("Network error")
    error = TeltonikaConnectionError("Connection failed", original_error)
    assert str(error) == "Connection failed"
    assert error.original_error is original_error


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
    assert exc_info.value.original_error is connection_error


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
    assert exc_info.value.error_code == 121


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
async def test_session_status_active(auth, mock_session):
    """Test getting active session status."""
    await _authenticate_success(auth, mock_session)
    mock_session.get.return_value = _mock_context_response(
        {"success": True, "data": {"active": True}}
    )

    response = await auth.get_session_status()

    assert response.success is True
    assert response.data is not None
    assert response.data.active is True
    assert auth.token is not None


@pytest.mark.asyncio
async def test_session_status_inactive_clears_token(auth, mock_session):
    """Test that inactive session status clears stored token."""
    await _authenticate_success(auth, mock_session)
    mock_session.get.return_value = _mock_context_response(
        {"success": True, "data": {"active": False}}
    )

    response = await auth.get_session_status()

    assert response.success is True
    assert response.data is not None
    assert response.data.active is False
    assert auth.token is None
    assert auth.is_authenticated is False


@pytest.mark.asyncio
async def test_session_status_no_token(auth):
    """Test session status check with no token."""
    response = await auth.get_session_status()

    assert response.success is True
    assert response.data is not None
    assert response.data.active is False


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
