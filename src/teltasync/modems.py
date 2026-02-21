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
    "PUK",
]

PinStateId = Literal[
    0,
    1,
    2,
    4,
    5,
    10,
    13,
    14,
    15,
]

OperatorState = Literal[
    "Not registered", "Registered, home", "Searching", "Denied", "Unknown", "Roaming"
]

ModemName = Literal[
    "Primary modem",
    "Secondary modem",
    "External modem",
    "Internal modem",
    "Unknown modem",
]

ModemMode = Literal[0, 1, 2, 3]

SimState = Literal["Inserted", "Not inserted"]

DataConnectionState = Literal["Connected", "Disconnected", "Unknown"]
DataConnectionStateId = Literal[0, 1, 2]

OperatorStateId = Literal[0, 1, 2, 3, 4, 5]

CarrierAggregationState = Literal["Inactive", "Active"]

MobileStageId = Literal[
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
]

ModemStateId = Literal[1, 2, 3, 4, 5]

ModemBlocked = Literal[0, 1]

ModemDisabled = Literal[0, 1]


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
        8: "No Service",
    }

    return ue_states.get(ue_state, f"Unknown UE state ({ue_state})")


def decode_mobile_stage(mobile_stage: int | None) -> str | None:
    """Decode mobile stage code to human-readable description.

    Key from:
    https://developers.teltonika-networks.com/reference/rutx50/7.13.3/v1.5/
    modems#get-modems-status-id

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
        19: "Mobile connection setup is complete",
        20: "Waiting for SIM switch",
        21: "Trying saved PIN",
        22: "Trying saved PUK",
        23: "Flight mode enabled",
    }

    return mobile_stages.get(mobile_stage, f"Unknown mobile stage ({mobile_stage})")


def decode_modem_state(modem_state_id: int | None) -> str | None:
    """Decode modem state code to human-readable description.

    Args:
        modem_state_id: The modem state code (integer)

    Returns:
        Human-readable description of the modem state, or None if invalid/unknown
    """
    if modem_state_id is None:
        return None

    modem_states = {
        1: "Modem is in functioning state",
        2: "Modem shut down unexpectedly",
        3: "Modem rebooted by modem manager",
        4: "Modem rebooted by user",
        5: "Modem shut down by user",
    }

    return modem_states.get(modem_state_id, f"Unknown modem state ({modem_state_id})")


class CellInfo(TeltasyncBaseModel):
    """Cell information for modem."""

    mcc: str | None = Field(None, description="Mobile Country Code")
    mnc: str | None = Field(None, description="Mobile Network Code")
    cell_id: str | None = Field(None, alias="cellid", description="Cell ID")
    ue_state: int | None = Field(None, description="User Equipment state")
    lac: str | None = Field(None, description="Location Area Code")
    tac: str | None = Field(None, description="Tracking Area Code")
    pcid: int | None = Field(None, description="Physical Cell ID")
    earfcn: str | int | None = Field(
        None, description="E-UTRA Absolute Radio Frequency Channel Number"
    )
    arfcn: str | int | None = Field(
        None, description="Absolute Radio Frequency Channel Number"
    )
    uarfcn: str | int | None = Field(
        None, description="UMTS Absolute Radio Frequency Channel Number"
    )
    nr_arfcn: str | int | None = Field(
        None,
        alias="nr-arfcn",
        description="New Radio Absolute Radio Frequency Channel Number",
    )
    rsrp: str | int | None = Field(None, description="Reference Signal Received Power")
    rsrq: str | int | None = Field(
        None, description="Reference Signal Received Quality"
    )
    sinr: str | int | None = Field(
        None, description="Signal to Interference plus Noise Ratio"
    )
    bandwidth: str | None = Field(None, description="Bandwidth")

    @computed_field
    def ue_state_description(self) -> str | None:
        """Get human-readable description of the UE state."""
        return decode_ue_state(self.ue_state)


class ServiceModes(TeltasyncBaseModel):
    """Service modes available for each network type."""

    field_2g: list[str] | None = Field(
        None, alias="2G", description="Supported service modes for 2G"
    )
    field_3g: list[str] | None = Field(
        None, alias="3G", description="Supported service modes for 3G"
    )
    field_4g: list[str] | None = Field(
        None, alias="4G", description="Supported service modes for 4G"
    )
    nb: list[str] | None = Field(
        None, alias="NB", description="Supported service modes for NB"
    )
    field_5g_nsa: list[str] | None = Field(
        None, alias="5G_NSA", description="Supported service modes for 5G_NSA"
    )
    field_5g_sa: list[str] | None = Field(
        None, alias="5G_SA", description="Supported service modes for 5G_SA"
    )


class CarrierAggregationSignal(TeltasyncBaseModel):
    """Carrier aggregation signal information."""

    band: str | None = Field(None, description="Band number")
    bandwidth: str | None = Field(None, description="Bandwidth")
    sinr: int | None = Field(
        None, description="Signal to Interference plus Noise Ratio"
    )
    rsrq: int | None = Field(None, description="Reference Signal Received Quality")
    rsrp: int | None = Field(None, description="Reference Signal Received Power")
    pcid: int | None = Field(None, description="Physical Cell ID")
    frequency: str | int | None = Field(None, description="Frequency")
    # Some CA signals might not have all fields
    primary: bool | None = Field(
        None, description="Indicates if this is the primary cell"
    )


class ModemStatusFull(TeltasyncBaseModel):
    """Full modem status when online."""

    id: str = Field(description="Modem usb id")
    imei: str | None = Field(
        None, description="International Mobile Equipment Identity number"
    )
    model: str | None = Field(None, description="Modem model")
    cell_info: list[CellInfo] | None = Field(None, description="Cell information")
    dynamic_mtu: bool | None = Field(None, description="Dynamic MTU status")
    service_modes: ServiceModes | None = Field(
        None, description="Supported service modes"
    )
    lac: str | None = Field(
        None,
        description=(
            "The Location Area Code is a unique number given to each location area "
            "within the network."
        ),
    )
    tac: str | None = Field(
        None,
        description=(
            "The Tracking Area Code is a unique number given to each location area "
            "within the network."
        ),
    )
    name: ModemName | None = Field(None, description="Modem name")
    index: int | None = Field(None, description="Modem index")
    sim_count: int | None = Field(None, description="Number of SIM cards")
    version: str | None = Field(None, description="Modem firmware version")
    manufacturer: str | None = Field(None, description="Modem manufacturer")
    builtin: bool | None = Field(None, description="Modem type")
    mode: ModemMode | None = Field(None, description="Modem mode")
    primary: bool | None = Field(None, description="Primary modem")
    multi_apn: bool | None = Field(None, description="Modem supports multiple APN")
    ipv6: bool | None = Field(None, description="Modem supports IPv6")
    volte_supported: bool | None = Field(None, description="Modem supports VoLTE")
    auto_3g_bands: bool | None = Field(
        None, description="Modem selects 3G band automatically"
    )
    operators_scan: bool | None = Field(
        None, description="Modem supports operator scanning"
    )
    mobile_dfota: bool | None = Field(None, description="Modem supports mobile DFOTA")
    no_ussd: bool | None = Field(None, description="Modem does not support USSD")
    framed_routing: bool | None = Field(
        None, description="Modem supports framed routing"
    )
    low_signal_reconnect: bool | None = Field(
        None, description="Modem supports low signal reconnect"
    )
    active_sim: int | None = Field(None, description="Currently active SIM card")
    conntype: str | None = Field(None, description="Modem connection type")
    simstate: SimState | None = Field(None, description="SIM card state")
    simstate_id: int | None = Field(None, description="SIM state ID")
    data_conn_state: DataConnectionState | None = Field(
        None, description="Data connection state"
    )
    data_conn_state_id: DataConnectionStateId | None = Field(
        None, description="Data connection state ID"
    )
    txbytes: int | None = Field(None, description="Total number of bytes sent")
    rxbytes: int | None = Field(None, description="Total number of bytes received")
    baudrate: int | None = Field(None, description="Baud rate of the modem")
    is_busy: int | None = Field(None, description="Indicates if the modem is busy")
    data_off: bool | None = Field(
        None, description="Shows if data was turned off with mobileoff SMS"
    )
    busy_state: str | None = Field(None, description="Modem busy state")
    busy_state_id: int | None = Field(None, description="Modem busy state ID")
    pinstate: PinState | None = Field(None, description="SIM card PIN state")
    pinstate_id: int | None = Field(
        None, description="SIM card PIN state ID (deprecated)", deprecated=True
    )
    operator_state: OperatorState | None = Field(None, description="Operator state")
    operator_state_id: OperatorStateId | None = Field(
        None, description="Operator state ID (deprecated)", deprecated=True
    )
    rssi: int | None = Field(None, description="Received Signal Strength Indicator")
    operator: str | None = Field(None, description="Operator name")
    provider: str | None = Field(None, description="Provider name")
    ntype: str | None = Field(None, description="Network type")
    imsi: str | None = Field(
        None, description="International Mobile Subscriber Identity number"
    )
    iccid: str | None = Field(
        None, description="Integrated Circuit Card Identifier number"
    )
    cellid: str | None = Field(None, description="Cell ID")
    rscp: str | None = Field(None, description="Received Signal Code Power")
    ecio: str | None = Field(
        None, description="Quality/Cleanliness of the signal from the tower"
    )
    rsrp: int | None = Field(None, description="Reference Signal Received Power")
    rsrq: int | None = Field(None, description="Reference Signal Received Quality")
    sinr: int | None = Field(
        None, description="Signal to Interference plus Noise Ratio"
    )
    pinleft: int | None = Field(
        None, description="Number of attempts left to enter the PIN code"
    )
    volte: bool | None = Field(None, description="Modem supports VoLTE")
    sc_band_av: CarrierAggregationState | None = Field(
        None, description="Carrier aggregation"
    )
    ca_signal: list[CarrierAggregationSignal] | None = Field(
        None, description="Carrier aggregation signal values"
    )
    temperature: int | None = Field(None, description="Modem temperature")
    esim_profile: str | None = Field(None, description="Active eSIM profile")
    mobile_stage: MobileStageId | None = Field(
        None, description="Indicates current mobile connection stage"
    )
    gnss_state: int | None = Field(
        None,
        description=(
            "Indicates the state of GNSS for devices that switch between mobile and GNSS"
        ),
    )

    # Additional fields found in API response (not documented)
    nr5g_sa_disabled: bool | None = Field(
        None, description="Indicates if 5G SA mode is not supported"
    )
    wwan_gnss_conflict: bool | None = Field(
        None, description="Indicates if mobile will stop working when GNSS is enabled"
    )
    modem_state_id: ModemStateId | None = Field(
        None,
        description=(
            "Indicates the state of the modem. 1 = Modem is in functioning state, "
            "2 = Modem shut down unexpectedly, 3 = Modem rebooted by modem manager, "
            "4 = Modem rebooted by user, 5 = Modem shut down by user."
        ),
    )
    sim_switch_enabled: bool | None = Field(
        None, description="Indicates if SIM switch is for active SIM"
    )
    serial: str | None = Field(None, description="Modem serial number")
    auto_2g_bands: bool | None = Field(
        None, description="Modem selects 2G band automatically"
    )
    cfg_version: str | None = Field(None, description="Modem configuration version")
    csd: bool | None = Field(None, description="Indicates CSD support")
    pukleft: int | None = Field(
        None, description="Number of attempts left to enter the PUK code"
    )
    band: str | None = Field(None, description="Active band")
    auto_5g_mode: bool | None = Field(
        None, description="Indicates if 5G mode can not be controlled manually"
    )

    # Deprecated fields (keep for compatibility)
    state: DataConnectionState | None = Field(
        None, description="Data connection state (deprecated)", deprecated=True
    )
    state_id: DataConnectionStateId | None = Field(
        None, description="Data connection state ID (deprecated)", deprecated=True
    )
    signal: int | None = Field(
        None,
        description="Received Signal Strength Indicator (deprecated)",
        deprecated=True,
    )
    oper: str | None = Field(
        None, description="Operator name (deprecated)", deprecated=True
    )
    netstate: OperatorState | None = Field(
        None, description="Operator state (deprecated)", deprecated=True
    )
    netstate_id: OperatorStateId | None = Field(
        None, description="Operator state ID (deprecated)", deprecated=True
    )

    @computed_field
    def mobile_stage_description(self) -> str | None:
        """Get human-readable description of the mobile stage."""
        return decode_mobile_stage(self.mobile_stage)

    @computed_field
    def modem_state_description(self) -> str | None:
        """Get human-readable description of the modem state."""
        return decode_modem_state(self.modem_state_id)


class ModemStatusOffline(TeltasyncBaseModel):
    """Limited modem status when offline."""

    id: str = Field(description="Offline modem id")
    name: ModemName | None = Field(None, description="Offline modem name")
    offline: str | None = Field(None, description="Modem state")
    blocked: ModemBlocked | None = Field(None, description="Modem block state")
    disabled: ModemDisabled | None = Field(None, description="Modem disable state")
    builtin: bool | None = Field(None, description="Modem type")
    primary: bool | None = Field(None, description="Primary modem")
    sim_count: int | None = Field(None, description="Modem SIM count")
    mode: ModemMode | None = Field(None, description="Modem mode")
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
    def get_online_modems(
        modems_response: ApiResponse[list[ModemStatus]],
    ) -> list[ModemStatusFull]:
        """Get only the online modems from a modems status response.

        Args:
            modems_response: Response from get_status()

        Returns:
            List of only the online modems with full status.
        """
        if not modems_response.success or not modems_response.data:
            return []

        return [
            modem
            for modem in modems_response.data
            if isinstance(modem, ModemStatusFull)
        ]

    @staticmethod
    def get_offline_modems(
        modems_response: ApiResponse[list[ModemStatus]],
    ) -> list[ModemStatusOffline]:
        """Get only the offline modems from a modems status response.

        Args:
            modems_response: Response from get_status()

        Returns:
            List of only the offline modems with limited status.
        """
        if not modems_response.success or not modems_response.data:
            return []

        return [
            modem
            for modem in modems_response.data
            if isinstance(modem, ModemStatusOffline)
        ]

    async def reboot_modem(self, modem_id: str) -> ApiResponse:
        """Reboot a specified modem."""
        async with await self.auth.request(
            "POST", f"modems/{modem_id}/actions/reboot"
        ) as resp:
            json_response = await resp.json()
            return ApiResponse(**json_response)

    async def restart_connection(self, modem_id: str) -> ApiResponse:
        """Restart the connection of a specified modem."""
        async with await self.auth.request(
            "POST", f"modems/{modem_id}/actions/restart_connection"
        ) as resp:
            json_response = await resp.json()
            return ApiResponse(**json_response)

    async def switch_sim(self, modem_id: str) -> ApiResponse:
        """Switch to the next SIM of the specified modem."""
        async with await self.auth.request(
            "POST", f"modems/{modem_id}/actions/switch_sim"
        ) as resp:
            json_response = await resp.json()
            return ApiResponse(**json_response)
