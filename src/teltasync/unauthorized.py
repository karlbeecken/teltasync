"""Client and models for the public unauthorized status endpoint."""

import asyncio
from typing import Optional

from aiohttp import ClientConnectorError, ClientSession, ClientTimeout
from pydantic import ConfigDict

from teltasync.api_base import ApiResponse
from teltasync.base_model import TeltasyncBaseModel
from teltasync.exceptions import TeltonikaConnectionError
from teltasync.utils import camel_to_snake


class SecurityBanner(TeltasyncBaseModel):
    """Banner text shown on devices that expose a legal warning."""

    title: str
    message: str


class UnauthorizedStatusData(TeltasyncBaseModel):
    """Payload returned by ``/unauthorized/status``."""

    lang: str
    filename: Optional[str] = None
    device_name: str
    device_model: str
    api_version: str
    device_identifier: str
    security_banner: Optional[SecurityBanner] = None

    model_config = ConfigDict(alias_generator=camel_to_snake, populate_by_name=True)


class UnauthorizedClient:  # pylint: disable=too-few-public-methods
    """Thin HTTP client for unauthenticated status requests."""

    def __init__(
        self, session: ClientSession, base_url: str, check_certificate: bool = True
    ):
        """Initialize the unauthorized client."""

        self.session = session
        self.base_url = base_url
        self.check_certificate = check_certificate

    async def get_status(self) -> ApiResponse[UnauthorizedStatusData]:
        """Fetch the device metadata available without authentication."""

        try:
            async with self.session.get(
                f"{self.base_url}/unauthorized/status",
                ssl=self.check_certificate,
                timeout=ClientTimeout(total=10.0),
            ) as resp:
                payload = await resp.json()
                return ApiResponse[UnauthorizedStatusData](**payload)
        except (ClientConnectorError, asyncio.TimeoutError) as exc:
            message = (
                f"Cannot connect to device at {self.base_url}: {exc}"
                if isinstance(exc, ClientConnectorError)
                else f"Connection timeout to {self.base_url}"
            )
            raise TeltonikaConnectionError(message) from exc
