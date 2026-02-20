"""Tests for modem functionality."""

from unittest.mock import AsyncMock, Mock

import pytest

from teltasync.api_base import ApiResponse
from teltasync.modems import (
    Modems,
    ModemStatus,
    ModemStatusFull,
    ModemStatusOffline,
    decode_ue_state,
)
from tests.helpers import load_fixture


@pytest.fixture(name="modem_status_fixture")
def fixture_modem_status():
    """Load modem status test fixture."""
    return load_fixture("modems", "status.json")


@pytest.fixture(name="modems_status_response")
def fixture_modems_status_response(modem_status_fixture):
    """Provide a parsed modems response from fixture."""
    return ApiResponse[list[ModemStatus]](**modem_status_fixture)


@pytest.fixture(name="mock_auth")
def fixture_mock_auth():
    """Create a mock auth object."""
    auth = Mock()
    auth.request = AsyncMock()
    return auth


class TestUEStateDecoding:
    """Test UE state code decoding functionality."""

    def test_ue_state_decoding(self):
        """Test UE state code decoding."""
        assert decode_ue_state(0) == "Detached"
        assert decode_ue_state(1) == "Attached"
        assert decode_ue_state(3) == "Connected"
        assert decode_ue_state(None) is None
        assert decode_ue_state(999) == "Unknown UE state (999)"

    def test_ue_state_computed_field(self, modems_status_response):
        """Test UE state computed field in CellInfo."""
        data = modems_status_response.data
        assert data is not None
        modem = data[0]
        assert isinstance(modem, ModemStatusFull)

        cell_info = modem.cell_info
        assert cell_info is not None
        cell = cell_info[0]
        assert cell.ue_state == 3
        assert cell.ue_state_description == "Connected"


class TestModemDataParsing:
    """Test modem data parsing and validation."""

    def test_full_payload_snapshot(
        self,
        modems_status_response,
        snapshot,
    ):
        """Test parsed modem payload snapshot."""
        data = modems_status_response.data
        assert data is not None

        assert data == snapshot

    def test_na_conversion_in_cell_info(self, modems_status_response):
        """Test that N/A values are converted to None in cell info."""
        data = modems_status_response.data
        assert data is not None
        modem = data[0]
        assert isinstance(modem, ModemStatusFull)

        cell_info = modem.cell_info
        assert cell_info is not None
        cell = cell_info[0]
        assert cell.lac is None  # Was "N/A"
        assert cell.rsrp is None  # Was "N/A"
        assert cell.mcc == "262"

        cell2 = cell_info[1]
        assert cell2.tac is None  # Was "N/A"
        assert cell2.rsrp == -103

    def test_baudrate_typo_handling(self, modems_status_response):
        """Test that the API's 'boudrate' typo is handled correctly."""
        data = modems_status_response.data
        assert data is not None
        modem = data[0]
        assert isinstance(modem, ModemStatusFull)
        assert modem.baudrate == 115200

    def test_service_modes_parsing(self, modems_status_response):
        """Test that service modes with numeric keys are parsed correctly."""
        data = modems_status_response.data
        assert data is not None
        modem = data[0]
        assert isinstance(modem, ModemStatusFull)

        assert modem.service_modes is not None
        assert modem.service_modes.field_4g is not None
        assert modem.service_modes.field_3g is not None
        assert modem.service_modes.field_5g_sa is not None

    def test_carrier_aggregation_data(self, modems_status_response):
        """Test carrier aggregation signal data parsing."""
        data = modems_status_response.data
        assert data is not None
        modem = data[0]
        assert isinstance(modem, ModemStatusFull)

        assert modem.ca_signal is not None
        assert len(modem.ca_signal) == 4

        primary_carrier = next((ca for ca in modem.ca_signal if ca.primary), None)
        assert primary_carrier is not None
        assert primary_carrier.band == "LTE B1"
        assert primary_carrier.bandwidth == "20"

        fiveg_carrier = next((ca for ca in modem.ca_signal if "5G" in ca.band), None)
        assert fiveg_carrier is not None
        assert fiveg_carrier.band == "5G N78"


class TestModemsClient:
    """Test Modems client endpoints and utility helpers."""

    @pytest.mark.asyncio
    async def test_get_status_parses_fixture(
        self, mock_auth, modem_status_fixture, snapshot
    ):
        """Test successful modem status retrieval using fixture data."""
        mock_response = AsyncMock()
        mock_response.json.return_value = modem_status_fixture
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        modems = Modems(mock_auth)
        result = await modems.get_status()

        assert result.success is True
        data = result.data
        assert data is not None
        assert len(data) == len(modem_status_fixture["data"])
        assert isinstance(data[0], ModemStatusFull)
        assert data[0].id == modem_status_fixture["data"][0]["id"]
        assert data[0].operator == modem_status_fixture["data"][0]["operator"]
        assert data[0].conntype == modem_status_fixture["data"][0]["conntype"]
        assert data[0] == snapshot

        mock_auth.request.assert_awaited_once_with("GET", "modems/status")

    def test_utility_methods(self, modems_status_response):
        """Test utility methods for filtering modem status types."""
        online_modems = Modems.get_online_modems(modems_status_response)
        offline_modems = Modems.get_offline_modems(modems_status_response)

        assert len(online_modems) == 1
        assert isinstance(online_modems[0], ModemStatusFull)
        assert len(offline_modems) == 0
        assert Modems.is_online(online_modems[0]) is True

    def test_utility_methods_with_mixed_statuses(self, modem_status_fixture):
        """Test utility methods with one online and one offline modem."""
        mixed_payload = {
            "success": True,
            "data": [
                modem_status_fixture["data"][0],
                {"id": "2-2", "offline": "1", "name": "External modem"},
            ],
        }
        response = ApiResponse[list[ModemStatus]](**mixed_payload)

        online_modems = Modems.get_online_modems(response)
        offline_modems = Modems.get_offline_modems(response)

        assert len(online_modems) == 1
        assert len(offline_modems) == 1
        assert isinstance(offline_modems[0], ModemStatusOffline)
        assert offline_modems[0].id == "2-2"

    @pytest.mark.asyncio
    async def test_empty_response_handling(self, mock_auth):
        """Test handling of empty or failed responses."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {"success": False, "data": None, "errors": []}
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        modems = Modems(mock_auth)
        result = await modems.get_status()

        online_modems = modems.get_online_modems(result)
        offline_modems = modems.get_offline_modems(result)

        assert len(online_modems) == 0
        assert len(offline_modems) == 0
