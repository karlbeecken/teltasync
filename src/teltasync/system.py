"""System endpoint bindings for the Teltonika API."""

from pydantic import Field

from teltasync.api_base import ApiResponse
from teltasync.auth import Auth
from teltasync.base_model import TeltasyncBaseModel


class ManufacturingInfo(TeltasyncBaseModel):
    """Manufacturing metadata returned by /system/device/status."""

    mac_eth: str = Field(alias="macEth", description="Ethernet WAN MAC address")
    name: str = Field(description="Product code")
    hw_ver: str = Field(alias="hwver", description="Hardware revision")
    batch: str = Field(description="Batch number")
    serial: str = Field(description="Serial number")
    mac: str = Field(description="Ethernet LAN MAC address")
    bl_ver: str = Field(alias="blver", description="Bootloader version")


class ReleaseInfo(TeltasyncBaseModel):
    """Firmware release summary."""

    distribution: str = Field(description="Distribution name")
    revision: str = Field(description="Revision")
    version: str = Field(description="Version of release")
    target: str = Field(description="Target of device")
    description: str = Field(description="Description of release")


class StaticInfo(TeltasyncBaseModel):
    """Firmware and hardware identifiers for the device."""

    fw_version: str = Field(description="Firmware version")
    kernel: str = Field(description="Kernel version")
    system: str = Field(description="Processor name")
    device_name: str = Field(description="Device name")
    hostname: str = Field(description="Hostname of router")
    cpu_count: int = Field(description="Number of CPU cores")
    release: ReleaseInfo
    fw_build_date: str = Field(description="Firmware build date")
    model: str = Field(description="Model name")
    board_name: str = Field(description="Board name")


class Features(TeltasyncBaseModel):
    """Feature flags advertised by the device."""

    ipv6: bool = Field(description="IPv6 support")


class Modem(TeltasyncBaseModel):
    """Single modem entry in the system response."""

    id: str = Field(description="Modem ID")
    num: str = Field(description="Modem number")
    builtin: bool = Field(description="Modem built-in")
    sim_count: int = Field(alias="simcount", description="Modem SIM count")
    gps_out: bool = Field(description="GPS support")
    primary: bool = Field(description="Modem primary")
    revision: str = Field(description="Modem revision")
    modem_func_id: int = Field(description="Modem func id")
    multi_apn: bool = Field(description="Modem multiple APN support")
    operator_scan: bool = Field(description="Modem operator scan support")
    dhcp_filter: bool = Field(description="Modem DHCP filter support")
    dynamic_mtu: bool = Field(description="Modem dynamic MTU support")
    ipv6: bool = Field(description="Modem IPv6 support")
    volte: bool = Field(description="Modem VoLTE support")
    csd: bool = Field(description="Modem CSD support")
    band_list: list[str] = Field(description="Modem supported bands")
    product: str = Field(description="Modem product code")
    vendor: str = Field(description="Modem vendor")
    gps: str = Field(description="GPS support")
    stop_bits: str = Field(description="Modem stop bits")
    baudrate: str = Field(alias="boudrate", description="Modem baudrate")
    type: str = Field(description="Modem type")
    desc: str = Field(description="Modem description")
    control: str = Field(description="Modem control")


class NetworkInterface(TeltasyncBaseModel):
    """Configuration values for a network interface."""

    proto: str = Field(description="Protocol")
    device: str = Field(description="Device name")
    default_ip: str | None = Field(None, description="Default IP address")


class NetworkConfig(TeltasyncBaseModel):
    """WAN and LAN interface configuration."""

    wan: NetworkInterface
    lan: NetworkInterface


class ModelInfo(TeltasyncBaseModel):
    """Identifier and marketing name for the device."""

    id: str = Field(description="Model ID")
    platform: str = Field(description="Model platform")
    name: str = Field(description="Model name")


class NetworkOptions(TeltasyncBaseModel):
    """Limits and defaults used by the switch configuration."""

    readonly_vlans: int
    max_mtu: int
    vlans: int


class SwitchRole(TeltasyncBaseModel):
    """Mapping of switch ports to their assigned role."""

    ports: str = Field(description="Switch ports")
    role: str = Field(description="Switch role")
    device: str = Field(description="Switch device")


class SwitchPort(TeltasyncBaseModel):
    """Switch port definition with tagging hints."""

    device: str | None = Field(None, description="Switch port device")
    num: int = Field(description="Switch port number")
    want_untag: bool | None = Field(None, description="Switch port want untag")
    need_tag: bool | None = Field(None, description="Switch port need tag")
    role: str | None = Field(None, description="Switch port role")
    index: int | None = Field(None, description="Switch port index")


class SwitchConfig(TeltasyncBaseModel):
    """Complete switch profile for switch0."""

    enable: bool
    roles: list[SwitchRole]
    ports: list[SwitchPort]
    reset: bool = Field(description="Switch reset")


class Switch(TeltasyncBaseModel):
    """Wrapper for switch configuration blocks."""

    switch0: SwitchConfig


class HardwareInfo(TeltasyncBaseModel):
    """Hardware capabilities advertised by the platform."""

    wps: bool | None = Field(None, description="WPS support")
    rs232: bool | None = Field(None, description="RS232 support")
    nat_offloading: bool | None = Field(None, description="NAT Offloading support")
    dual_sim: bool | None = Field(None, description="Dual SIM support")
    bluetooth: bool | None = Field(None, description="Bluetooth support")
    soft_port_mirror: bool | None = Field(
        None, description="Software Port Mirroring support"
    )
    vcert: bool | None = Field(None, description="VCert support")
    micro_usb: bool | None = Field(None, description="Micro USB support")
    wifi: bool | None = Field(None, description="WiFi support")
    sd_card: bool | None = Field(None, description="SD Card support")
    multi_tag: bool | None = Field(None, description="Multi Tag support")
    dual_modem: bool | None = Field(None, description="Dual Modem support")
    sfp_switch: bool | None = Field(None, description="SFP switch support")
    dsa: bool | None = Field(None, description="DSA support")
    hw_nat: bool | None = Field(None, description="HW NAT support")
    sw_rst_on_init: bool | None = Field(None, description="SW RST on init support")
    at_sim: bool | None = Field(None, description="AT SIM support")
    port_link: bool | None = Field(None, description="Port link support")
    ios: bool | None = Field(None, description="iOS support")
    usb: bool | None = Field(None, description="USB support")
    console: bool | None = Field(None, description="Console support")
    dual_band_ssid: bool | None = Field(None, description="Dual band SSID support")
    gps: bool | None = Field(None, description="GPS support")
    ethernet: bool | None = Field(None, description="Ethernet support")
    sfp_port: bool | None = Field(None, description="SFP port support")
    rs485: bool | None = Field(None, description="RS485 support")
    mobile: bool | None = Field(None, description="Mobile support")
    poe: bool | None = Field(None, description="POE support")
    gigabit_port: bool | None = Field(None, description="Gigabit port support")
    field_2_5_gigabit_port: bool | None = Field(
        None, alias="2_5_gigabit_port", description="2.5 Gigabit port support"
    )

    # Additional undocumented fields found in the response
    esim: bool | None = Field(None, description="eSIM support")
    modem_reset: bool | None = Field(None, description="Modem reset support")


class BoardInfo(TeltasyncBaseModel):
    """High-level board configuration including modems and switch."""

    modems: list[Modem]
    network: NetworkConfig
    model: ModelInfo
    usb_jack: str = Field(description="USB ports")
    network_options: NetworkOptions
    switch: Switch
    hw_info: HardwareInfo = Field(alias="hwinfo")


class DeviceStatusData(TeltasyncBaseModel):
    """Aggregated payload returned by the status endpoint."""

    mnf_info: ManufacturingInfo = Field(alias="mnfinfo")
    static: StaticInfo
    features: Features
    board: BoardInfo


class RebootResponse(TeltasyncBaseModel):
    """Minimal response body for reboot requests."""


class System:
    """API wrapper for /system endpoints."""

    def __init__(self, auth: Auth):
        self.auth = auth

    async def get_device_status(self) -> ApiResponse[DeviceStatusData]:
        """Return manufacturing, firmware and hardware details."""
        async with await self.auth.request("GET", "system/device/status") as resp:
            json_response = await resp.json()
            return ApiResponse[DeviceStatusData](**json_response)

    async def reboot(self) -> ApiResponse[RebootResponse]:
        """Trigger a reboot and return the raw API response."""
        async with await self.auth.request("POST", "system/actions/reboot") as resp:
            json_response = await resp.json()
            return ApiResponse[RebootResponse](**json_response)
