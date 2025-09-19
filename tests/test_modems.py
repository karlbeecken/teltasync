"""Tests for modem functionality."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp import ClientSession

from teltasync import Teltasync
from teltasync.api_base import ApiResponse
from teltasync.modems import ModemStatusFull, ModemStatusOffline, decode_ue_state, Modems


@pytest.fixture
def modem_status_fixture():
    """Load modem status test fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "modems" / "status.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture
def mock_auth():
    """Create a mock auth object."""
    auth = Mock()
    auth.request = AsyncMock()
    return auth


@pytest.fixture
def mock_modems_response(modem_status_fixture):
    """Provide a mock modems response for tests."""
    from teltasync.api_base import ApiResponse
    return ApiResponse[list](**modem_status_fixture)


class TestUEStateDecoding:
    """Test UE state code decoding functionality."""

    def test_ue_state_decoding(self):
        """Test UE state code decoding."""
        # Test known UE states
        assert decode_ue_state(0) == "Detached"
        assert decode_ue_state(1) == "Attached"
        assert decode_ue_state(3) == "Connected"
        assert decode_ue_state(None) is None
        assert decode_ue_state(999) == "Unknown UE state (999)"

    def test_ue_state_computed_field(self, modem_status_fixture):
        """Test UE state computed field in CellInfo."""
        response = ApiResponse[list](**modem_status_fixture)
        modem_data = response.data[0]
        modem = ModemStatusFull(**modem_data)

        # Check cell info UE state descriptions
        assert modem.cell_info[0].ue_state == 3
        assert modem.cell_info[0].ue_state_description == "Connected"


class TestModemDataParsing:
    """Test modem data parsing and validation."""

    def test_na_conversion_in_cell_info(self, modem_status_fixture):
        """Test that N/A values are converted to None in cell info."""
        response = ApiResponse[list](**modem_status_fixture)
        modem_data = response.data[0]
        modem = ModemStatusFull(**modem_data)

        # Check that N/A values were converted to None
        cell = modem.cell_info[0]
        assert cell.lac is None  # Was "N/A"
        assert cell.rsrp is None  # Was "N/A"
        assert cell.mcc == "262"  # Actual value preserved

        cell2 = modem.cell_info[1]
        assert cell2.tac is None  # Was "N/A"
        assert cell2.rsrp == -103  # Actual numeric value preserved

    def test_baudrate_typo_handling(self, modem_status_fixture):
        """Test that the API's 'boudrate' typo is handled correctly."""
        response = ApiResponse[list](**modem_status_fixture)
        modem_data = response.data[0]
        modem = ModemStatusFull(**modem_data)

        # The fixture should contain 'boudrate' but we access it as 'baudrate'
        assert modem.baudrate == 115200

    def test_service_modes_parsing(self, modem_status_fixture):
        """Test that service modes with numeric keys are parsed correctly."""
        response = ApiResponse[list](**modem_status_fixture)
        modem_data = response.data[0]
        modem = ModemStatusFull(**modem_data)

        # Check that service modes are accessible with proper field names
        assert modem.service_modes is not None
        assert modem.service_modes.field_4g is not None  # Maps from "4G"
        assert modem.service_modes.field_3g is not None  # Maps from "3G"
        assert modem.service_modes.field_5g_sa is not None  # Maps from "5G_SA"


class TestModemsClient:
    """Test the Modems client functionality via Teltasync."""

    @pytest.mark.asyncio
    async def test_get_online_modems(self, mock_modems_response):
        """Test getting online modems."""
        mock_session = AsyncMock(spec=ClientSession)
        client = Teltasync(base_url="http://localhost/api", username="user", password="pass", session=mock_session)

        # Mock the modems get_status method
        client.modems.get_status = AsyncMock(return_value=mock_modems_response)

        result = await client.modems.get_status()
        online_modems = client.modems.get_online_modems(result)
        assert all(isinstance(m, ModemStatusFull) for m in online_modems)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_offline_modems(self, mock_modems_response):
        """Test getting offline modems."""
        mock_session = AsyncMock(spec=ClientSession)
        client = Teltasync(base_url="http://localhost/api", username="user", password="pass", session=mock_session)

        # Mock the modems get_status method
        client.modems.get_status = AsyncMock(return_value=mock_modems_response)

        result = await client.modems.get_status()
        offline_modems = client.modems.get_offline_modems(result)
        assert all(isinstance(m, ModemStatusOffline) for m in offline_modems)
        await client.close()

    @pytest.mark.asyncio
    async def test_get_status_success(self, mock_auth, modem_status_fixture):
        """Test successful modem status retrieval."""
        # Mock the HTTP response
        mock_response = AsyncMock()
        mock_response.json.return_value = modem_status_fixture
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        modems = Modems(mock_auth)
        result = await modems.get_status()

        assert result.success is True
        assert len(result.data) == 1
        assert isinstance(result.data[0], ModemStatusFull)

        modem = result.data[0]
        assert modem.id == "2-1"
        assert modem.name == "Internal modem"
        assert modem.operator == "test-operator.de"
        assert modem.temperature == 45
        assert modem.conntype == "5G (NSA)"

    @pytest.mark.asyncio
    async def test_utility_methods(self, mock_auth, modem_status_fixture):
        """Test utility methods for filtering modems."""
        mock_response = AsyncMock()
        mock_response.json.return_value = modem_status_fixture
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        modems = Modems(mock_auth)
        result = await modems.get_status()

        # Test is_online method
        modem = result.data[0]
        assert modems.is_online(modem) is True

        # Test get_online_modems
        online_modems = modems.get_online_modems(result)
        assert len(online_modems) == 1
        assert isinstance(online_modems[0], ModemStatusFull)

        # Test get_offline_modems (should be empty with our fixture)
        offline_modems = modems.get_offline_modems(result)
        assert len(offline_modems) == 0

    @pytest.mark.asyncio
    async def test_empty_response_handling(self, mock_auth):
        """Test handling of empty or failed responses."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {"success": False, "data": None, "errors": []}
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        modems = Modems(mock_auth)
        result = await modems.get_status()

        # Test utility methods with empty data
        online_modems = modems.get_online_modems(result)
        offline_modems = modems.get_offline_modems(result)

        assert len(online_modems) == 0
        assert len(offline_modems) == 0


class TestModemStatusTypes:
    """Test different modem status types."""

    def test_modem_status_full_creation(self, modem_status_fixture):
        """Test creation of ModemStatusFull from fixture data."""
        response = ApiResponse[list](**modem_status_fixture)
        modem_data = response.data[0]
        modem = ModemStatusFull(**modem_data)

        # Test essential fields
        assert modem.id == "2-1"
        assert modem.manufacturer == "Quectel"
        assert modem.model == "RG501Q-EU"
        assert modem.serial == "XXXYY12345678"  # Match actual fixture data
        assert modem.imei == "123456789012345"

        # Test optional fields that might be None
        assert modem.provider is None  # Was "N/A" in fixture
        assert modem.temperature == 45
        assert modem.rssi == -58

    def test_carrier_aggregation_data(self, modem_status_fixture):
        """Test carrier aggregation signal data parsing."""
        response = ApiResponse[list](**modem_status_fixture)
        modem_data = response.data[0]
        modem = ModemStatusFull(**modem_data)

        assert modem.ca_signal is not None
        assert len(modem.ca_signal) == 4

        # Test primary carrier
        primary_carrier = next((ca for ca in modem.ca_signal if ca.primary), None)
        assert primary_carrier is not None
        assert primary_carrier.band == "LTE B1"
        assert primary_carrier.bandwidth == "20"

        # Test 5G carrier (might not have all fields)
        fiveg_carrier = next((ca for ca in modem.ca_signal if "5G" in ca.band), None)
        assert fiveg_carrier is not None
        assert fiveg_carrier.band == "5G N78"
