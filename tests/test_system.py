"""Tests for system endpoint functionality."""

from unittest.mock import AsyncMock, Mock

import pytest

from teltasync.system import DeviceStatusData, RebootResponse, System
from tests.helpers import load_fixture


@pytest.fixture(name="device_status_fixture")
def fixture_device_status():
    """Load device status fixture data."""
    return load_fixture("system", "device_status.json")


@pytest.fixture(name="mock_auth")
def fixture_mock_auth():
    """Create a mock auth object."""
    auth = Mock()
    auth.request = AsyncMock()
    return auth


class TestSystemClient:
    """Test the System endpoint wrapper."""

    @pytest.mark.asyncio
    async def test_get_device_status_parses_fixture(
        self,
        mock_auth,
        device_status_fixture,
        snapshot,
    ):
        """Test device status parsing against fixture content."""
        mock_response = AsyncMock()
        mock_response.json.return_value = device_status_fixture
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        system = System(mock_auth)
        result = await system.get_device_status()

        assert result.success is True
        data = result.data
        assert isinstance(data, DeviceStatusData)

        assert data == snapshot
        assert data.board.hw_info.field_2_5_gigabit_port is False
        mock_auth.request.assert_awaited_once_with("GET", "system/device/status")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                {
                    "fixture_file": "device_status_trb500.json",
                    "expected_model": "Teltonika TRB5XX",
                    "expected_default_ip": "192.168.2.1",
                    "expected_bl_ver": None,
                    "expected_gps_out": None,
                },
                id="trb500",
            ),
            pytest.param(
                {
                    "fixture_file": "device_status_trb140.json",
                    "expected_model": "Teltonika TRB14X",
                    "expected_default_ip": "192.168.2.1",
                    "expected_bl_ver": None,
                    "expected_gps_out": None,
                },
                id="trb140",
            ),
            pytest.param(
                {
                    "fixture_file": "device_status_rut950.json",
                    "expected_model": "Teltonika RUT9XX",
                    "expected_default_ip": "192.168.1.1",
                    "expected_bl_ver": "4.0.8",
                    "expected_gps_out": None,
                },
                id="rut950",
            ),
            pytest.param(
                {
                    "fixture_file": "device_status_rut241.json",
                    "expected_model": "Teltonika RUT2M",
                    "expected_default_ip": "192.168.1.1",
                    "expected_bl_ver": "4.2.0",
                    "expected_gps_out": None,
                },
                id="rut241",
            ),
        ],
    )
    async def test_get_device_status_parses_additional_device_variants(
        self,
        mock_auth,
        snapshot,
        case,
    ):
        """Test device status parsing for additional observed device payload variants."""
        device_status_fixture = load_fixture("system", case["fixture_file"])
        mock_response = AsyncMock()
        mock_response.json.return_value = device_status_fixture
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        system = System(mock_auth)
        result = await system.get_device_status()

        assert result.success is True
        data = result.data
        assert isinstance(data, DeviceStatusData)
        assert data == snapshot
        assert data.static.model == case["expected_model"]
        assert data.mnf_info.bl_ver == case["expected_bl_ver"]
        assert data.board.network.lan is not None
        assert data.board.network.lan.default_ip == case["expected_default_ip"]
        assert data.board.modems is not None
        assert data.board.modems[0].gps_out == case["expected_gps_out"]
        mock_auth.request.assert_awaited_once_with("GET", "system/device/status")

    @pytest.mark.asyncio
    async def test_reboot_success(self, mock_auth):
        """Test reboot endpoint success payload parsing."""
        reboot_payload = {"success": True, "data": {}}
        mock_response = AsyncMock()
        mock_response.json.return_value = reboot_payload
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        system = System(mock_auth)
        result = await system.reboot()

        assert result.success is True
        assert isinstance(result.data, RebootResponse)
        assert result.data.model_dump() == {}
        mock_auth.request.assert_awaited_once_with("POST", "system/actions/reboot")

    @pytest.mark.asyncio
    async def test_reboot_failure(self, mock_auth):
        """Test reboot endpoint error payload parsing."""
        reboot_payload = {
            "success": False,
            "errors": [{"code": 100, "error": "Response not implemented"}],
        }
        mock_response = AsyncMock()
        mock_response.json.return_value = reboot_payload
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        system = System(mock_auth)
        result = await system.reboot()

        assert result.success is False
        assert result.data is None
        assert result.errors is not None
        assert result.errors[0].code == 100
        assert result.errors[0].error == "Response not implemented"
