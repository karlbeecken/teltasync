"""Tests for authentication functionality."""

from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp import ClientConnectorError

from teltasync.auth import Auth
from teltasync.exceptions import TeltonikaConnectionError, TeltonikaAuthenticationError, \
    TeltonikaInvalidCredentialsError


class TestAuthExceptions:
    """Test authentication exception classes."""

    def test_authentication_error_creation(self):
        """Test TeltonikaAuthenticationError exception."""
        error = TeltonikaAuthenticationError("Test error", 121)
        assert str(error) == "Test error"
        assert error.error_code == 121

    def test_connection_error_creation(self):
        """Test TeltonikaConnectionError exception."""
        original_error = Exception("Network error")
        error = TeltonikaConnectionError("Connection failed", original_error)
        assert str(error) == "Connection failed"
        assert error.original_error is original_error


class TestAuth:
    """Test Auth class functionality."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock aiohttp session."""
        return Mock()

    @pytest.fixture
    def auth(self, mock_session):
        """Create an Auth instance with mock session."""
        return Auth(
            session=mock_session,
            base_url="https://test.device.com/api",
            username="test_user",
            password="test_pass",
            check_certificate=False
        )

    def _setup_mock_response(self, mock_session, method, json_response):
        """Helper method to set up mock HTTP response."""
        mock_response = AsyncMock()
        mock_response.json.return_value = json_response
        mock_response.status = 200

        # Set up the async context manager properly
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_response
        mock_context_manager.__aexit__.return_value = None

        getattr(mock_session, method).return_value = mock_context_manager
        return mock_response

    @pytest.mark.asyncio
    async def test_successful_authentication(self, auth, mock_session):
        """Test successful authentication flow."""
        # Mock successful login response
        mock_response = self._setup_mock_response(mock_session, "post", {
            "success": True,
            "data": {
                "username": "test_user",
                "token": "test_token_123",
                "expires": 300
            }
        })

        response = await auth.authenticate()

        assert response.success is True
        assert response.data.username == "test_user"
        assert response.data.token == "test_token_123"
        assert response.data.expires == 300
        assert auth.is_authenticated is True
        assert auth.token == "test_token_123"

    @pytest.mark.asyncio
    async def test_authentication_with_connection_error(self, auth, mock_session):
        """Test authentication with connection error."""
        # Create a mock connection error that doesn't cause SSL issues
        connection_error = ClientConnectorError(
            connection_key=Mock(ssl=False),
            os_error=OSError("Connection failed")
        )
        mock_session.post.side_effect = connection_error

        with pytest.raises(TeltonikaConnectionError) as exc_info:
            await auth.authenticate()

        assert "Cannot connect to device" in str(exc_info.value)
        assert exc_info.value.original_error is connection_error

    @pytest.mark.asyncio
    async def test_authentication_with_401_error(self, auth, mock_session):
        """Test authentication with 401 HTTP error."""
        mock_response = self._setup_mock_response(mock_session, "post", {
            "success": False,
            "data": None,
            "errors": None
        })
        mock_response.status = 401

        with pytest.raises(TeltonikaInvalidCredentialsError):
            await auth.authenticate()

    @pytest.mark.asyncio
    async def test_authentication_with_api_error(self, auth, mock_session):
        """Test authentication with API error response."""
        mock_response = self._setup_mock_response(mock_session, "post", {
            "success": False,
            "errors": [
                {
                    "code": 121,
                    "error": "Invalid credentials"
                }
            ]
        })

        with pytest.raises(TeltonikaAuthenticationError) as exc_info:
            await auth.authenticate()

        assert "Invalid credentials" in str(exc_info.value)
        assert exc_info.value.error_code == 121

    @pytest.mark.asyncio
    async def test_logout_success(self, auth, mock_session):
        """Test successful logout."""
        # Set up authenticated state
        auth._token = "test_token"
        auth._authenticated = True

        mock_response = self._setup_mock_response(mock_session, "post", {
            "success": True,
            "data": {"response": "Logged out successfully"}
        })

        response = await auth.logout()

        assert response.success is True
        assert response.data.response == "Logged out successfully"
        assert auth.token is None
        assert auth.is_authenticated is False

    @pytest.mark.asyncio
    async def test_logout_no_active_session(self, auth, mock_session):
        """Test logout with no active session."""
        response = await auth.logout()

        assert response.success is True
        assert response.data.response == "No active session"

    @pytest.mark.asyncio
    async def test_session_status_active(self, auth, mock_session):
        """Test getting active session status."""
        auth._token = "test_token"

        mock_response = self._setup_mock_response(mock_session, "get", {
            "success": True,
            "data": {"active": True}
        })

        response = await auth.get_session_status()

        assert response.success is True
        assert response.data.active is True

    @pytest.mark.asyncio
    async def test_session_status_inactive_clears_token(self, auth, mock_session):
        """Test that inactive session status clears stored token."""
        auth._token = "test_token"
        auth._authenticated = True

        mock_response = self._setup_mock_response(mock_session, "get", {
            "success": True,
            "data": {"active": False}
        })

        response = await auth.get_session_status()

        assert response.success is True
        assert response.data.active is False
        assert auth.token is None
        assert auth.is_authenticated is False

    @pytest.mark.asyncio
    async def test_session_status_no_token(self, auth, mock_session):
        """Test session status check with no token."""
        response = await auth.get_session_status()

        assert response.success is True
        assert response.data.active is False

    def test_is_token_expired_no_token(self, auth):
        """Test token expiry check with no token."""
        assert auth.is_token_expired() is True

    def test_is_token_expired_valid_token(self, auth):
        """Test token expiry check with valid token."""
        import time
        auth._token = "test_token"
        auth._token_expires = 300  # 5 minutes
        auth._token_time = time.time()

        assert auth.is_token_expired() is False

    def test_is_token_expired_expired_token(self, auth):
        """Test token expiry check with expired token."""
        import time
        auth._token = "test_token"
        auth._token_expires = 300  # 5 minutes
        auth._token_time = time.time() - 400  # 400 seconds ago

        assert auth.is_token_expired() is True

    def test_clear_token(self, auth):
        """Test clearing token data."""
        auth._token = "test_token"
        auth._token_expires = 300
        auth._token_username = "test_user"
        auth._authenticated = True

        auth.clear_token()

        assert auth.token is None
        assert auth._token_expires is None
        assert auth._token_username is None
        assert auth.is_authenticated is False
