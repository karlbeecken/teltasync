"""High-level facade combining Teltonika endpoint clients."""

from aiohttp import ClientSession

from teltasync.auth import Auth
from teltasync.exceptions import (
    TeltonikaAuthenticationError,
    TeltonikaConnectionError,
    TeltonikaException,
)
from teltasync.modems import Modems, ModemStatusFull, ModemStatusOffline
from teltasync.system import DeviceStatusData, System
from teltasync.unauthorized import UnauthorizedClient, UnauthorizedStatusData

AUTH_ERROR_CODES = {120, 121, 122, 123}


class Teltasync:  # pylint: disable=too-many-instance-attributes
    """Convenience client exposing common router operations."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        *,
        session: ClientSession | None = None,
        verify_ssl: bool = True,
    ):  # pylint: disable=too-many-arguments
        """Initialize the client with connection and credential settings."""

        self._session = session
        self._own_session = session is None
        self._base_url = base_url
        self._username = username
        self._password = password
        self._verify_ssl = verify_ssl

        self._auth: Auth | None = None
        self._system: System | None = None
        self._modems: Modems | None = None
        self._unauthorized: UnauthorizedClient | None = None

    @classmethod
    async def create(
        cls,
        base_url: str,
        username: str,
        password: str,
        *,
        verify_ssl: bool = True,
    ) -> "Teltasync":
        """Create a client with an internally managed aiohttp session."""

        return cls(
            base_url=base_url,
            username=username,
            password=password,
            verify_ssl=verify_ssl,
        )

    @property
    def session(self) -> ClientSession:
        """Return the aiohttp session, creating one when needed."""

        if self._session is None:
            self._session = ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the internally owned session, if present."""

        if self._own_session and self._session:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> "Teltasync":
        """Enter async context manager scope."""

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager scope and close managed resources."""

        await self.close()

    async def get_device_info(self) -> UnauthorizedStatusData:
        """Fetch device metadata available from the unauthorized endpoint."""

        await self._ensure_session()
        response = await self.unauthorized.get_status()
        if response.success and response.data:
            return response.data
        raise TeltonikaConnectionError("Failed to get device info")

    async def validate_credentials(self) -> bool:
        """Validate credentials by attempting login and then logout."""

        try:
            await self._ensure_session()
            await self.auth.authenticate()
        except TeltonikaAuthenticationError:
            return False
        finally:
            await self.logout()
        return True

    async def get_system_info(self) -> DeviceStatusData:
        """Fetch system/device status details."""

        await self._ensure_session()
        response = await self.system.get_device_status()
        if response.success and response.data:
            return response.data
        raise TeltonikaConnectionError("Failed to get system info")

    async def get_modem_status(self) -> list[ModemStatusFull | ModemStatusOffline]:
        """Fetch the status of all modems reported by the device."""

        await self._ensure_session()
        response = await self.modems.get_status()
        if response.success and response.data:
            return response.data
        raise TeltonikaConnectionError("Failed to get modem status")

    async def _run_modem_action(self, action, modem_id: str, action_name: str) -> None:
        """Execute a modem action and raise on an unsuccessful API response."""
        await self._ensure_session()
        response = await action(modem_id)
        if response and response.success:
            return

        message = f"Failed to {action_name}"
        if not response or not response.errors:
            raise TeltonikaConnectionError(message)

        first_error = response.errors[0]
        if first_error.code in AUTH_ERROR_CODES:
            raise TeltonikaAuthenticationError(
                f"{first_error.error} (code {first_error.code})"
            )

        raise TeltonikaException(first_error.error)

    async def reboot_modem(self, modem_id: str) -> None:
        """Reboot the specified modem."""
        await self._run_modem_action(self.modems.reboot_modem, modem_id, "reboot modem")

    async def restart_connection(self, modem_id: str) -> None:
        """Restart the connection for the specified modem."""
        await self._run_modem_action(
            self.modems.restart_connection,
            modem_id,
            "restart modem connection",
        )

    async def switch_sim(self, modem_id: str) -> None:
        """Switch to the next SIM of the specified modem."""
        await self._run_modem_action(
            self.modems.switch_sim, modem_id, "switch modem SIM"
        )

    async def reboot_device(self) -> bool:
        """Trigger device reboot and return whether it was accepted."""

        await self._ensure_session()
        response = await self.system.reboot()
        return bool(response and response.success)

    async def logout(self) -> bool:
        """Log out of the authenticated API session."""

        await self._ensure_session()
        response = await self.auth.logout()
        return bool(response and response.success)

    @property
    def auth(self) -> Auth:
        """Return lazy-initialized authentication client."""

        if self._auth is None:
            self._auth = Auth(
                self.session,
                self._base_url,
                self._username,
                self._password,
                check_certificate=self._verify_ssl,
            )
        return self._auth

    @property
    def system(self) -> System:
        """Return lazy-initialized system endpoint client."""

        if self._system is None:
            self._system = System(self.auth)
        return self._system

    @property
    def modems(self) -> Modems:
        """Return lazy-initialized modems endpoint client."""

        if self._modems is None:
            self._modems = Modems(self.auth)
        return self._modems

    @property
    def unauthorized(self) -> UnauthorizedClient:
        """Return lazy-initialized unauthorized endpoint client."""

        if self._unauthorized is None:
            self._unauthorized = UnauthorizedClient(
                self.session,
                self._base_url,
                check_certificate=self._verify_ssl,
            )
        return self._unauthorized

    async def _ensure_session(self) -> ClientSession:
        """Internal helper to guarantee session initialization."""

        return self.session
