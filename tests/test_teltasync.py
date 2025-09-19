"""Tests for the main Teltasync client."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from aiohttp import ClientSession

from teltasync import Teltasync
from teltasync.exceptions import TeltonikaConnectionError, TeltonikaAuthenticationError
from teltasync.auth import TokenData
from teltasync.system import DeviceStatusData
from teltasync.modems import ModemStatusFull
from teltasync.unauthorized import UnauthorizedStatusData
from teltasync.api_base import ApiResponse


class TestTeltasyncInitialization:
    """Test Teltasync client initialization."""

    def test_init_with_session(self):
        """Test initialization with provided session."""
        mock_session = Mock(spec=ClientSession)
        client = Teltasync(
            base_url="https://192.168.1.1/api",
            username="admin",
            password="password",
            session=mock_session
        )

        assert client._session is mock_session
        assert client._own_session is False
        assert client.session is mock_session

    def test_init_without_session(self):
        """Test initialization without session (will create one)."""
        client = Teltasync(
            base_url="https://192.168.1.1/api",
            username="admin",
            password="password"
        )

        assert client._own_session is True

    @pytest.mark.asyncio
    async def test_create_class_method(self):
        """Test the create class method."""
        client = await Teltasync.create(
            base_url="https://192.168.1.1/api",
            username="admin",
            password="password",
            verify_ssl=False
        )

        assert isinstance(client, Teltasync)
        await client.close()


class TestTeltasyncContextManager:
    """Test async context manager functionality."""

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test using Teltasync as async context manager."""
        with patch('aiohttp.ClientSession'):
            async with Teltasync(
                base_url="https://192.168.1.1/api",
                username="admin",
                password="password"
            ) as client:
                assert isinstance(client, Teltasync)

    @pytest.mark.asyncio
    async def test_close_with_own_session(self):
        """Test closing client with own session."""
        mock_session = AsyncMock(spec=ClientSession)

        with patch('teltasync.teltasync.ClientSession', return_value=mock_session):
            client = Teltasync(
                base_url="https://192.168.1.1/api",
                username="admin",
                password="password"
            )

            # Trigger session creation
            await client._ensure_session()

            await client.close()
            mock_session.close.assert_called_once()
            assert client._session is None

    @pytest.mark.asyncio
    async def test_close_with_external_session(self):
        """Test closing client with external session (should not close it)."""
        mock_session = AsyncMock(spec=ClientSession)
        client = Teltasync(
            base_url="https://192.168.1.1/api",
            username="admin",
            password="password",
            session=mock_session
        )

        await client.close()
        # Should not call close on external session
        mock_session.close.assert_not_called()


class TestTeltasyncSimpleInterface:
    """Test the simple python-tado style interface methods."""

    @pytest.fixture
    def client(self):
        """Create a Teltasync client with mocked components."""
        mock_session = Mock(spec=ClientSession)
        client = Teltasync(
            base_url="https://192.168.1.1/api",
            username="admin",
            password="password",
            session=mock_session
        )

        # Mock the internal components
        client._auth = Mock()
        client._system = Mock()
        client._modems = Mock()
        client._unauthorized = Mock()

        return client

    @pytest.mark.asyncio
    async def test_get_device_info_success(self, client):
        """Test successful device info retrieval."""
        device_info = Mock(spec=UnauthorizedStatusData)
        mock_response = ApiResponse[UnauthorizedStatusData](
            success=True,
            data=device_info
        )
        client._unauthorized.get_status = AsyncMock(return_value=mock_response)

        result = await client.get_device_info()
        assert result == device_info
        client._unauthorized.get_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_device_info_failure(self, client):
        """Test device info retrieval failure."""
        mock_response = ApiResponse[UnauthorizedStatusData](
            success=False,
            data=None
        )
        client._unauthorized.get_status = AsyncMock(return_value=mock_response)

        with pytest.raises(TeltonikaConnectionError, match="Failed to get device info"):
            await client.get_device_info()

    @pytest.mark.asyncio
    async def test_validate_credentials_success(self, client):
        """Test successful credential validation."""
        client._auth.authenticate = AsyncMock()
        client._auth.logout = AsyncMock()

        result = await client.validate_credentials()
        assert result is True
        client._auth.authenticate.assert_called_once()
        client._auth.logout.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_credentials_failure(self, client):
        """Test credential validation failure."""
        client._auth.authenticate = AsyncMock(side_effect=TeltonikaAuthenticationError("Invalid credentials"))
        client._auth.logout = AsyncMock(return_value=False)

        result = await client.validate_credentials()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_system_info_success(self, client):
        """Test successful system info retrieval."""
        system_data = Mock(spec=DeviceStatusData)
        mock_response = ApiResponse[DeviceStatusData](
            success=True,
            data=system_data
        )
        client._system.get_device_status = AsyncMock(return_value=mock_response)

        result = await client.get_system_info()
        assert result == system_data

    @pytest.mark.asyncio
    async def test_get_system_info_failure(self, client):
        """Test system info retrieval failure."""
        mock_response = ApiResponse[DeviceStatusData](
            success=False,
            data=None
        )
        client._system.get_device_status = AsyncMock(return_value=mock_response)

        with pytest.raises(TeltonikaConnectionError, match="Failed to get system info"):
            await client.get_system_info()

    @pytest.mark.asyncio
    async def test_get_modem_status_success(self, client):
        """Test successful modem status retrieval."""
        modem_data = [Mock(spec=ModemStatusFull)]
        mock_response = ApiResponse[list](
            success=True,
            data=modem_data
        )
        client._modems.get_status = AsyncMock(return_value=mock_response)

        result = await client.get_modem_status()
        assert result == modem_data

    @pytest.mark.asyncio
    async def test_get_modem_status_failure(self, client):
        """Test modem status retrieval failure."""
        mock_response = ApiResponse[list](
            success=False,
            data=None
        )
        client._modems.get_status = AsyncMock(return_value=mock_response)

        with pytest.raises(TeltonikaConnectionError, match="Failed to get modem status"):
            await client.get_modem_status()

    @pytest.mark.asyncio
    async def test_reboot_device_success(self, client):
        """Test successful device reboot."""
        mock_response = ApiResponse[dict](success=True)
        client._system.reboot = AsyncMock(return_value=mock_response)

        result = await client.reboot_device()
        assert result is True

    @pytest.mark.asyncio
    async def test_reboot_device_failure(self, client):
        """Test device reboot failure."""
        mock_response = ApiResponse[dict](success=False)
        client._system.reboot = AsyncMock(return_value=mock_response)

        result = await client.reboot_device()
        assert result is False

    @pytest.mark.asyncio
    async def test_reboot_device_none_response(self, client):
        """Test device reboot with None response."""
        client._system.reboot = AsyncMock(return_value=None)

        result = await client.reboot_device()
        assert result is False

    @pytest.mark.asyncio
    async def test_logout_success(self, client):
        """Test successful logout."""
        mock_response = ApiResponse[dict](success=True)
        client._auth.logout = AsyncMock(return_value=mock_response)

        result = await client.logout()
        assert result is True

    @pytest.mark.asyncio
    async def test_logout_failure(self, client):
        """Test logout failure."""
        mock_response = ApiResponse[dict](success=False)
        client._auth.logout = AsyncMock(return_value=mock_response)

        result = await client.logout()
        assert result is False


class TestTeltasyncRichAPIAccess:
    """Test access to rich API components."""

    def test_rich_api_properties(self):
        """Test that rich API components are accessible."""
        mock_session = Mock(spec=ClientSession)
        client = Teltasync(
            base_url="https://192.168.1.1/api",
            username="admin",
            password="password",
            session=mock_session
        )

        # Test that all rich API components are accessible
        assert client.auth is not None
        assert client.system is not None
        assert client.modems is not None
        assert client.unauthorized is not None

        # Test that they return the actual component instances
        assert client.auth is client._auth
        assert client.system is client._system
        assert client.modems is client._modems
        assert client.unauthorized is client._unauthorized
