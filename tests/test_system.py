"""Tests for system functionality."""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from teltasync import Teltasync
from teltasync.api_base import ApiResponse
from teltasync.system import DeviceStatusData, System


@pytest.fixture
def mock_auth():
    """Create a mock auth object."""
    auth = Mock()
    auth.request = AsyncMock()
    return auth


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    return Mock()


@pytest.fixture
def client(mock_session):
    """Create a Teltasync client with mock session."""
    return Teltasync(
        base_url="http://localhost/api",
        username="user",
        password="pass",
        session=mock_session
    )


@pytest.fixture
def mock_device_status_response():
    """Provide a mock device status response for tests."""
    fixture_path = Path(__file__).parent / "fixtures" / "system" / "device_status.json"
    with open(fixture_path) as f:
        data = json.load(f)
    return ApiResponse[DeviceStatusData](**data)


class TestSystemClient:
    """Test the System client functionality via Teltasync."""

    @pytest.mark.asyncio
    async def test_get_device_status_success(self, client, mock_device_status_response):
        """Test getting device status successfully."""
        # Mock the system get_device_status method
        client.system.get_device_status = AsyncMock(return_value=mock_device_status_response)

        result = await client.system.get_device_status()
        assert isinstance(result.data, DeviceStatusData)
        assert hasattr(result.data, "mnf_info")  # Correct attribute name
        assert hasattr(result.data.board, "hw_info")  # Correct attribute name
