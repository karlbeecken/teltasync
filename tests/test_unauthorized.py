"""Tests for unauthorized endpoint functionality."""

import pytest
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from aiohttp import ClientSession, ClientConnectorError

from teltasync.unauthorized import UnauthorizedClient, UnauthorizedStatusData, SecurityBanner
from teltasync.exceptions import TeltonikaConnectionError
from teltasync.api_base import ApiResponse


@pytest.fixture
def unauthorized_status_fixture():
    """Load unauthorized status test fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "unauthorized" / "status.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture
def unauthorized_status_with_banner_fixture():
    """Load unauthorized status test fixture with security banner."""
    fixture_path = Path(__file__).parent / "fixtures" / "unauthorized" / "status-with-banner.json"
    with open(fixture_path) as f:
        return json.load(f)


class TestUnauthorizedStatusData:
    """Test UnauthorizedStatusData model using fixture data."""

    def test_unauthorized_status_from_fixture(self, unauthorized_status_fixture):
        """Test creation of UnauthorizedStatusData from fixture."""
        response = ApiResponse[UnauthorizedStatusData](**unauthorized_status_fixture)

        assert response.success is True
        assert response.data is not None

        data = response.data
        assert data.device_name == "RUTX50"
        assert data.device_model == "RUTX50"
        assert data.api_version == "1.9.2"
        assert data.device_identifier == "123456781234567812345678"
        assert data.lang == "en"

    def test_unauthorized_status_with_banner_from_fixture(self, unauthorized_status_with_banner_fixture):
        """Test creation of UnauthorizedStatusData with security banner from fixture."""
        response = ApiResponse[UnauthorizedStatusData](**unauthorized_status_with_banner_fixture)

        assert response.success is True
        assert response.data is not None

        data = response.data
        assert data.device_name == "Test Device"
        assert data.device_model == "RUTX50"
        assert data.api_version == "1.9.2"
        assert data.device_identifier == "123456781234567812345678"
        assert data.lang == "en"

        # Test security banner
        assert data.security_banner is not None
        assert data.security_banner.title == "Unauthorized access prohibited"
        assert "This system is for authorized use only" in data.security_banner.message
        assert "All activities on this system are logged and monitored" in data.security_banner.message
        assert "disconnect immediately" in data.security_banner.message

    def test_security_banner_model(self):
        """Test SecurityBanner model."""
        banner = SecurityBanner(
            title="Warning",
            message="This device is monitored"
        )

        assert banner.title == "Warning"
        assert banner.message == "This device is monitored"

    def test_security_banner_multiline_message(self, unauthorized_status_with_banner_fixture):
        """Test security banner with multiline message."""
        response = ApiResponse[UnauthorizedStatusData](**unauthorized_status_with_banner_fixture)
        banner = response.data.security_banner

        assert banner is not None
        assert "\n\n" in banner.message  # Contains paragraph breaks
        assert banner.message.count("\n") >= 1  # Has line breaks

        # Test that the full message content is preserved
        expected_parts = [
            "This system is for authorized use only",
            "All activities on this system are logged and monitored",
            "By using this system, you consent to such monitoring",
            "Unauthorized access or misuse may result in",
            "If you are not authorized to use this system, disconnect immediately"
        ]

        for part in expected_parts:
            assert part in banner.message


class TestUnauthorizedClient:
    """Test UnauthorizedClient functionality."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return Mock(spec=ClientSession)

    @pytest.fixture
    def client(self, mock_session):
        """Create UnauthorizedClient for testing."""
        return UnauthorizedClient(
            session=mock_session,
            base_url="https://192.168.1.1/api",
            check_certificate=False
        )

    def test_client_initialization(self, mock_session):
        """Test UnauthorizedClient initialization."""
        client = UnauthorizedClient(
            session=mock_session,
            base_url="https://192.168.1.1/api",
            check_certificate=True
        )

        assert client.session is mock_session
        assert client.base_url == "https://192.168.1.1/api"
        assert client.check_certificate is True

    @pytest.mark.asyncio
    async def test_get_status_success(self, client, mock_session, unauthorized_status_fixture):
        """Test successful status retrieval using fixture data."""
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.json.return_value = unauthorized_status_fixture
        mock_response.raise_for_status.return_value = None

        # Setup async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None
        mock_session.get.return_value = mock_context

        result = await client.get_status()

        assert result.success is True
        assert result.data is not None
        assert result.data.device_name == "RUTX50"
        assert result.data.device_model == "RUTX50"
        assert result.data.api_version == "1.9.2"
        assert result.data.device_identifier == "123456781234567812345678"
        assert result.data.lang == "en"

        # Verify the correct URL was called
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert call_args[0][0] == "https://192.168.1.1/api/unauthorized/status"

    @pytest.mark.asyncio
    async def test_get_status_connection_error(self, client, mock_session):
        """Test status retrieval with connection error."""
        connection_error = ClientConnectorError(
            connection_key=Mock(ssl=False),
            os_error=OSError("Connection failed")
        )
        mock_session.get.side_effect = connection_error

        with pytest.raises(TeltonikaConnectionError) as exc_info:
            await client.get_status()

        assert "Cannot connect to device" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_status_timeout_error(self, client, mock_session):
        """Test status retrieval with timeout error."""
        import asyncio
        mock_session.get.side_effect = asyncio.TimeoutError()

        with pytest.raises(TeltonikaConnectionError) as exc_info:
            await client.get_status()

        assert "Connection timeout" in str(exc_info.value)

    def test_client_properties(self, client):
        """Test client properties."""
        assert client.session is not None
        assert client.check_certificate is False
        assert "192.168.1.1" in client.base_url

    @pytest.mark.asyncio
    async def test_get_status_with_banner_success(self, client, mock_session, unauthorized_status_with_banner_fixture):
        """Test successful status retrieval with security banner using fixture data."""
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.json.return_value = unauthorized_status_with_banner_fixture
        mock_response.raise_for_status.return_value = None

        # Setup async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None
        mock_session.get.return_value = mock_context

        result = await client.get_status()

        assert result.success is True
        assert result.data is not None
        assert result.data.device_name == "Test Device"
        assert result.data.device_model == "RUTX50"
        assert result.data.api_version == "1.9.2"
        assert result.data.device_identifier == "123456781234567812345678"
        assert result.data.lang == "en"

        # Test security banner with correct fixture values
        assert result.data.security_banner is not None
        assert result.data.security_banner.title == "Unauthorized access prohibited"
        assert "This system is for authorized use only" in result.data.security_banner.message
        assert "All activities on this system are logged and monitored" in result.data.security_banner.message

        # Verify the correct URL was called
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert call_args[0][0] == "https://192.168.1.1/api/unauthorized/status"

    @pytest.mark.asyncio
    async def test_get_status_with_banner_connection_error(self, client, mock_session):
        """Test status retrieval with connection error when security banner is present."""
        connection_error = ClientConnectorError(
            connection_key=Mock(ssl=False),
            os_error=OSError("Connection failed")
        )
        mock_session.get.side_effect = connection_error

        with pytest.raises(TeltonikaConnectionError) as exc_info:
            await client.get_status()

        assert "Cannot connect to device" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_status_with_banner_timeout_error(self, client, mock_session):
        """Test status retrieval with timeout error when security banner is present."""
        import asyncio
        mock_session.get.side_effect = asyncio.TimeoutError()

        with pytest.raises(TeltonikaConnectionError) as exc_info:
            await client.get_status()

        assert "Connection timeout" in str(exc_info.value)
