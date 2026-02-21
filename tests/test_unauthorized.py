"""Tests for unauthorized endpoint functionality."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp import ClientConnectorError, ClientSession

from teltasync.api_base import ApiResponse
from teltasync.exceptions import TeltonikaConnectionError
from teltasync.unauthorized import (
    SecurityBanner,
    UnauthorizedClient,
    UnauthorizedStatusData,
)
from tests.helpers import load_fixture


@pytest.fixture(name="unauthorized_status_fixture")
def fixture_unauthorized_status():
    """Load unauthorized status test fixture."""
    return load_fixture("unauthorized", "status.json")


@pytest.fixture(name="unauthorized_status_with_banner_fixture")
def fixture_unauthorized_status_with_banner():
    """Load unauthorized status test fixture with security banner."""
    return load_fixture("unauthorized", "status-with-banner.json")


class TestUnauthorizedStatusData:
    """Test UnauthorizedStatusData model using fixture data."""

    def test_unauthorized_status_from_fixture(
        self, unauthorized_status_fixture, snapshot
    ):
        """Test creation of UnauthorizedStatusData from fixture."""
        response = ApiResponse[UnauthorizedStatusData](**unauthorized_status_fixture)

        assert response.success is True
        data = response.data
        assert isinstance(data, UnauthorizedStatusData)

        assert data == snapshot

    def test_unauthorized_status_with_banner_from_fixture(
        self, unauthorized_status_with_banner_fixture, snapshot
    ):
        """Test creation of UnauthorizedStatusData with security banner."""
        response = ApiResponse[UnauthorizedStatusData](
            **unauthorized_status_with_banner_fixture
        )

        assert response.success is True
        data = response.data
        assert isinstance(data, UnauthorizedStatusData)
        assert data.security_banner is not None

        assert data == snapshot

    def test_security_banner_model(self):
        """Test SecurityBanner model."""
        banner = SecurityBanner(title="Warning", message="This device is monitored")

        assert banner.title == "Warning"
        assert banner.message == "This device is monitored"

    def test_security_banner_multiline_message(
        self, unauthorized_status_with_banner_fixture
    ):
        """Test security banner multiline content remains intact."""
        response = ApiResponse[UnauthorizedStatusData](
            **unauthorized_status_with_banner_fixture
        )
        data = response.data
        assert isinstance(data, UnauthorizedStatusData)
        banner = data.security_banner

        assert banner is not None
        assert (
            banner.message
            == unauthorized_status_with_banner_fixture["data"]["security_banner"][
                "message"
            ]
        )
        assert "\n\n" in banner.message


class TestUnauthorizedClient:
    """Test UnauthorizedClient functionality."""

    @pytest.fixture(name="mock_session")
    def fixture_mock_session(self):
        """Create a mock session."""
        return Mock(spec=ClientSession)

    @pytest.fixture(name="client")
    def fixture_client(self, mock_session):
        """Create UnauthorizedClient for testing."""
        return UnauthorizedClient(
            session=mock_session,
            base_url="https://192.168.1.1/api",
            check_certificate=False,
        )

    def test_client_initialization(self, mock_session):
        """Test UnauthorizedClient initialization."""
        client = UnauthorizedClient(
            session=mock_session,
            base_url="https://192.168.1.1/api",
            check_certificate=True,
        )

        assert client.session is mock_session
        assert client.base_url == "https://192.168.1.1/api"
        assert client.check_certificate is True

    @pytest.fixture(
        name="status_payload",
        params=["status.json", "status-with-banner.json"],
        ids=["status", "status_with_banner"],
    )
    def fixture_status_payload(self, request):
        """Return unauthorized status payload for client success tests."""
        return load_fixture("unauthorized", request.param)

    @pytest.mark.asyncio
    async def test_get_status_success_from_fixture(
        self, client, mock_session, snapshot, status_payload
    ):
        """Test successful status retrieval using fixture data."""
        mock_response = AsyncMock()
        mock_response.json.return_value = status_payload

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None
        mock_session.get.return_value = mock_context

        result = await client.get_status()

        assert result.success is True
        data = result.data
        assert isinstance(data, UnauthorizedStatusData)

        assert data == snapshot

        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert call_args[0][0] == "https://192.168.1.1/api/unauthorized/status"

    @pytest.mark.asyncio
    async def test_get_status_connection_error(self, client, mock_session):
        """Test status retrieval with connection error."""
        connection_error = ClientConnectorError(
            connection_key=Mock(ssl=False), os_error=OSError("Connection failed")
        )
        mock_session.get.side_effect = connection_error

        with pytest.raises(TeltonikaConnectionError, match="Cannot connect to device"):
            await client.get_status()

    @pytest.mark.asyncio
    async def test_get_status_timeout_error(self, client, mock_session):
        """Test status retrieval with timeout error."""
        mock_session.get.side_effect = asyncio.TimeoutError()

        with pytest.raises(TeltonikaConnectionError, match="Connection timeout"):
            await client.get_status()

    def test_client_properties(self, client):
        """Test client properties."""
        assert client.session is not None
        assert client.check_certificate is False
        assert "192.168.1.1" in client.base_url
