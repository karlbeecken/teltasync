"""Bindings for the modem endpoints on Teltonika hardware."""

from typing import Literal

from pydantic import Field, computed_field

from teltasync.api_base import ApiResponse
from teltasync.auth import Auth
from teltasync.base_model import TeltasyncBaseModel

# Enum types for the state fields
PinState = Literal[
    "Inserted",
    "Not ready",
    "Required PIN, X attempts left",
    "Required PUK, X attempts left",
    "Not inserted",
    "SIM failure",
    "Busy",
    "PUK"
]

OperatorState = Literal[
    "Not registered",
    "Registered, home",
    "Searching",
    "Denied",
    "Unknown",
    "Roaming"
]


def decode_ue_state(ue_state: int | None) -> str | None:
    """Decode User Equipment state code to human-readable description.

    Based on 3GPP TS 24.008.

    Args:
        ue_state: The UE state code (integer)

    Returns:
        Human-readable description of the UE state, or None if invalid/unknown
    """
    if ue_state is None:
        return None

    ue_states = {
        0: "Detached",
        1: "Attached",
        2: "Connecting",
        3: "Connected",
        4: "Idle",
        5: "Disconnecting",
        6: "Emergency Attached",
        7: "Limited Service",
        8: "No Service"
    }

    return ue_states.get(ue_state, f"Unknown UE state ({ue_state})")


def decode_mobile_stage(mobile_stage: int | None) -> str | None:
    """Decode mobile stage code to human-readable description.

    Key from https://developers.teltonika-networks.com/reference/rutx50/7.13.3/v1.5/modems#get-modems-status-id

    Args:
        mobile_stage: The mobile stage code (integer)

    Returns:
        Human-readable description of the mobile stage, or None if invalid/unknown
    """
    if mobile_stage is None:
        return None

    mobile_stages = {
        0: "Unknown state",
        1: "Waiting for SIM to be inserted",
        2: "SIM failure",
        3: "Idling",
        4: "Waiting for user action",
        5: "Waiting for PIN to be entered",
        6: "Waiting for PUK to be entered",
        7: "SIM blocked, no PUK attempts left",
        8: "Initializing mobile connection",
        9: "Configuring Voice over LTE (VoLTE)",
        10: "Setting up connection settings",
        11: "Scanning for available operators",
        12: "Currently handling SIM PIN event",
        13: "Currently handling SIM switch event",
        14: "Initializing modem",
        15: "Changed default SIM card",
        16: "Setting up data connection settings",
        17: "Clearing PDP context",
        18: "Currently handling config",
        19: "Mobile connection setup is complete"
    }

    return mobile_stages.get(mobile_stage, f"Unknown mobile stage ({mobile_stage})")


class CellInfo(TeltasyncBaseModel):
    """Cell information for modem."""
    mcc: str | None = Field(None, description="Mobile Country Code")
    mnc: str | None = Field(None, description="Mobile Network Code")
    cell_id: str | None = Field(None, alias="cellid", description="Cell ID")
    ue_state: int | None = Field(None, description="UE state code")
    lac: str | None = Field(None, description="Location Area Code")
    tac: str | None = Field(None, description="Tracking Area Code")
    pcid: int | None = Field(None, description="Physical Cell ID")
    earfcn: str | int | None = Field(None, description="E-ARFCN")
    arfcn: str | int | None = Field(None, description="ARFCN")
    uarfcn: str | int | None = Field(None, description="UARFCN")
    nr_arfcn: str | int | None = Field(None, alias="nr-arfcn", description="NR-ARFCN")
    rsrp: str | int | None = Field(None, description="Reference Signal Received Power")
    rsrq: str | int | None = Field(None, description="Reference Signal Received Quality")
    sinr: str | int | None = Field(None, description="Signal to Interference plus Noise Ratio")
    bandwidth: str | None = Field(None, description="Bandwidth")

    @computed_field
    def ue_state_description(self) -> str | None:
        """Get human-readable description of the UE state."""
        return decode_ue_state(self.ue_state)


class ServiceModes(TeltasyncBaseModel):
    """Service modes available for each network type."""
    field_2g: list[str] | None = Field(None, alias="2G", description="2G service modes")
    field_3g: list[str] | None = Field(None, alias="3G", description="3G service modes")
    field_4g: list[str] | None = Field(None, alias="4G", description="4G service modes")
    nb: list[str] | None = Field(None, alias="NB", description="NB-IoT service modes")
    field_5g_nsa: list[str] | None = Field(None, alias="5G_NSA", description="5G NSA service modes")
    field_5g_sa: list[str] | None = Field(None, alias="5G_SA", description="5G SA service modes")


class CarrierAggregationSignal(TeltasyncBaseModel):
    """Carrier aggregation signal information."""
    band: str | None = Field(None, description="Band")
    bandwidth: str | None = Field(None, description="Bandwidth")
    sinr: int | None = Field(None, description="SINR")
    rsrq: int | None = Field(None, description="RSRQ")
    rsrp: int | None = Field(None, description="RSRP")
    pcid: int | None = Field(None, description="Physical Cell ID")
    frequency: str | int | None = Field(None, description="Frequency")
    # Some CA signals might not have all fields
    primary: bool | None = Field(None, description="Primary carrier")


class ModemStatusFull(TeltasyncBaseModel):
    """Full modem status when online."""
    id: str = Field(description="Modem ID")
    imei: str | None = Field(None, description="IMEI")
    model: str | None = Field(None, description="Modem model")
    cell_info: list[CellInfo] | None = Field(None, description="Cell information")
    dynamic_mtu: bool | None = Field(None, description="Dynamic MTU support")
    service_modes: ServiceModes | None = Field(None, description="Available service modes")
    lac: str | None = Field(None, description="Location Area Code")
    tac: str | None = Field(None, description="Tracking Area Code")
    name: str | None = Field(None, description="Modem name")
    index: int | None = Field(None, description="Modem index")
    sim_count: int | None = Field(None, description="Number of SIM cards")
    version: str | None = Field(None, description="Modem version")
    manufacturer: str | None = Field(None, description="Manufacturer")
    builtin: bool | None = Field(None, description="Built-in modem")
    mode: int | None = Field(None, description="Modem mode")
    primary: bool | None = Field(None, description="Primary modem")
    multi_apn: bool | None = Field(None, description="Multi APN support")
    ipv6: bool | None = Field(None, description="IPv6 support")
    volte_supported: bool | None = Field(None, description="VoLTE support")
    auto_3g_bands: bool | None = Field(None, description="Auto 3G bands")
    operators_scan: bool | None = Field(None, description="Operators scan support")
    mobile_dfota: bool | None = Field(None, description="Mobile DFOTA support")
    no_ussd: bool | None = Field(None, description="No USSD")
    framed_routing: bool | None = Field(None, description="Framed routing")
    low_signal_reconnect: bool | None = Field(None, description="Low signal reconnect")
    active_sim: int | None = Field(None, description="Currently active SIM card")
    conntype: str | None = Field(None, description="Connection type")
    simstate: str | None = Field(None, description="SIM state")
    simstate_id: int | None = Field(None, description="SIM state ID")
    data_conn_state: str | None = Field(None, description="Data connection state")
    data_conn_state_id: int | None = Field(None, description="Data connection state ID")
    txbytes: int | None = Field(None, description="Transmitted bytes")
    rxbytes: int | None = Field(None, description="Received bytes")
    baudrate: int | None = Field(None, description="Baudrate")
    is_busy: int | None = Field(None, description="Is busy")
    data_off: bool | None = Field(None, description="Data turned off with mobileoff SMS")
    busy_state: str | None = Field(None, description="Busy state")
    busy_state_id: int | None = Field(None, description="Busy state ID")
    pinstate: PinState | None = Field(None, description="PIN state")
    pinstate_id: int | None = Field(None, description="PIN state ID (deprecated)", deprecated=True)
    operator_state: OperatorState | None = Field(None, description="Operator state")
    operator_state_id: int | None = Field(None, description="Operator state ID (deprecated)", deprecated=True)
    rssi: int | None = Field(None, description="Received Signal Strength Indicator")
    operator: str | None = Field(None, description="Operator name")
    provider: str | None = Field(None, description="Provider")
    ntype: str | None = Field(None, description="Network type")
    imsi: str | None = Field(None, description="International Mobile Subscriber Identity")
    iccid: str | None = Field(None, description="Integrated Circuit Card Identifier")
    cellid: str | None = Field(None, description="Cell ID")
    rscp: str | None = Field(None, description="Received Signal Code Power")
    ecio: str | None = Field(None, description="Energy per chip to Interference power ratio")
    rsrp: int | None = Field(None, description="Reference Signal Received Power")
    rsrq: int | None = Field(None, description="Reference Signal Received Quality")
    sinr: int | None = Field(None, description="Signal to Interference plus Noise Ratio")
    pinleft: int | None = Field(None, description="PIN attempts left")
    volte: bool | None = Field(None, description="VoLTE active")
    sc_band_av: str | None = Field(None, description="Carrier aggregation status")
    ca_signal: list[CarrierAggregationSignal] | None = Field(None, description="Carrier aggregation signal values")
    temperature: int | None = Field(None, description="Modem temperature")
    esim_profile: str | None = Field(None, description="Active eSIM profile")
    mobile_stage: int | None = Field(None, description="Current mobile connection stage")
    gnss_state: int | None = Field(None, description="GNSS state for devices that switch between mobile and GNSS")

    # Additional fields found in API response (not documented)
    nr5g_sa_disabled: bool | None = Field(None, description="5G SA disabled status")
    wwan_gnss_conflict: bool | None = Field(None, description="WWAN GNSS conflict status")
    modem_state_id: int | None = Field(None, description="Modem state ID")
    sim_switch_enabled: bool | None = Field(None, description="SIM switch enabled")
    serial: str | None = Field(None, description="Modem serial number")
    auto_2g_bands: bool | None = Field(None, description="Auto 2G bands")
    cfg_version: str | None = Field(None, description="Configuration version")
    csd: bool | None = Field(None, description="CSD support")
    pukleft: int | None = Field(None, description="PUK attempts left")
    band: str | None = Field(None, description="Current band")
    auto_5g_mode: bool | None = Field(None, description="Auto 5G mode")

    # Deprecated fields (keeping for compatibility)
    state: str | None = Field(None, description="Data connection state (deprecated)", deprecated=True)
    state_id: int | None = Field(None, description="Data connection state ID (deprecated)", deprecated=True)
    signal: int | None = Field(None, description="Signal strength (deprecated)", deprecated=True)
    oper: str | None = Field(None, description="Operator (deprecated)", deprecated=True)
    netstate: str | None = Field(None, description="Network state (deprecated)", deprecated=True)
    netstate_id: int | None = Field(None, description="Network state ID (deprecated)", deprecated=True)

    @computed_field
    def mobile_stage_description(self) -> str | None:
        """Get human-readable description of the mobile stage."""
        return decode_mobile_stage(self.mobile_stage)


class ModemStatusOffline(TeltasyncBaseModel):
    """Limited modem status when offline."""
    id: str = Field(description="Offline modem id")
    name: str | None = Field(None, description="Offline modem name")
    offline: str | None = Field(None, description="Modem state")
    blocked: str | None = Field(None, description="Modem block state")
    disabled: str | None = Field(None, description="Modem disable state")
    builtin: bool | None = Field(None, description="Modem type")
    primary: bool | None = Field(None, description="Primary modem")
    sim_count: int | None = Field(None, description="Modem SIM count")
    mode: int | None = Field(None, description="Modem mode")
    multi_apn: bool | None = Field(None, description="Multi APN support")
    operators_scan: bool | None = Field(None, description="Operators scan support")
    dynamic_mtu: bool | None = Field(None, description="Dynamic MTU support")
    ipv6: bool | None = Field(None, description="IPv6 support")
    volte: bool | None = Field(None, description="VoLTE support")
    esim_profile: str | None = Field(None, description="Active eSIM profile")


# Union type for modem status, can be either full (=online) or offline
ModemStatus = ModemStatusFull | ModemStatusOffline


class Modems:
    """Modem management client for Teltonika devices."""

    def __init__(self, auth: Auth):
        """Initialize modems client."""
        self.auth = auth

    async def get_status(self) -> ApiResponse[list[ModemStatus]]:
        """Get status of all modems.

        Returns:
            List of modem statuses. Each modem can be either online (full status)
            or offline (limited status) depending on its current state.
        """
        async with await self.auth.request("GET", "modems/status") as resp:
            json_response = await resp.json()
            return ApiResponse[list[ModemStatus]](**json_response)

    @staticmethod
    def is_online(modem: ModemStatus) -> bool:
        """Check if a modem is online based on its status type.

        Args:
            modem: Modem status object

        Returns:
            True if modem is online (has full status), False if offline.
        """
        return isinstance(modem, ModemStatusFull)

    @staticmethod
    def get_online_modems(modems_response: ApiResponse[list[ModemStatus]]) -> list[ModemStatusFull]:
        """Get only the online modems from a modems status response.

        Args:
            modems_response: Response from get_status()

        Returns:
            List of only the online modems with full status.
        """
        if not modems_response.success or not modems_response.data:
            return []

        return [modem for modem in modems_response.data if isinstance(modem, ModemStatusFull)]

    @staticmethod
    def get_offline_modems(modems_response: ApiResponse[list[ModemStatus]]) -> list[ModemStatusOffline]:
        """Get only the offline modems from a modems status response.

        Args:
            modems_response: Response from get_status()

        Returns:
            List of only the offline modems with limited status.
        """
        if not modems_response.success or not modems_response.data:
            return []

        return [modem for modem in modems_response.data if isinstance(modem, ModemStatusOffline)]
