from aiohttp import ClientSession

from teltasync.auth import Auth
from teltasync.exceptions import TeltonikaAuthenticationError, TeltonikaConnectionError
from teltasync.modems import ModemStatusFull, ModemStatusOffline, Modems
from teltasync.system import DeviceStatusData, System
from teltasync.unauthorized import UnauthorizedClient, UnauthorizedStatusData


class Teltasync:
    def __init__(
            self,
            base_url: str,
            username: str,
            password: str,
            *,
            session: ClientSession | None = None,
            verify_ssl: bool = True,
    ):
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
        session = ClientSession()
        return cls(
            base_url=base_url,
            username=username,
            password=password,
            session=session,
            verify_ssl=verify_ssl,
        )

    @property
    def session(self) -> ClientSession:
        if self._session is None:
            self._session = ClientSession()
        return self._session

    async def close(self) -> None:
        if self._own_session and self._session:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> "Teltasync":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def get_device_info(self) -> UnauthorizedStatusData:
        await self._ensure_session()
        response = await self.unauthorized.get_status()
        if response.success and response.data:
            return response.data
        raise TeltonikaConnectionError("Failed to get device info")

    async def validate_credentials(self) -> bool:
        try:
            await self._ensure_session()
            await self.auth.authenticate()
        except TeltonikaAuthenticationError:
            return False
        finally:
            await self.logout()
        return True

    async def get_system_info(self) -> DeviceStatusData:
        await self._ensure_session()
        response = await self.system.get_device_status()
        if response.success and response.data:
            return response.data
        raise TeltonikaConnectionError("Failed to get system info")

    async def get_modem_status(self) -> list[ModemStatusFull | ModemStatusOffline]:
        await self._ensure_session()
        response = await self.modems.get_status()
        if response.success and response.data:
            return response.data
        raise TeltonikaConnectionError("Failed to get modem status")

    async def reboot_device(self) -> bool:
        await self._ensure_session()
        response = await self.system.reboot()
        return bool(response and response.success)

    async def logout(self) -> bool:
        await self._ensure_session()
        response = await self.auth.logout()
        return bool(response and response.success)

    @property
    def auth(self) -> Auth:
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
        if self._system is None:
            self._system = System(self.auth)
        return self._system

    @property
    def modems(self) -> Modems:
        if self._modems is None:
            self._modems = Modems(self.auth)
        return self._modems

    @property
    def unauthorized(self) -> UnauthorizedClient:
        if self._unauthorized is None:
            self._unauthorized = UnauthorizedClient(
                self.session,
                self._base_url,
                check_certificate=self._verify_ssl,
            )
        return self._unauthorized

    async def _ensure_session(self) -> ClientSession:
        return self.session
