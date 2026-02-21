"""Tests for the main Teltasync client."""

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientSession

from teltasync import Teltasync
from teltasync.api_base import ApiError, ApiResponse
from teltasync.exceptions import (
    TeltonikaAuthenticationError,
    TeltonikaConnectionError,
    TeltonikaException,
)
from teltasync.modems import ModemStatus, ModemStatusFull
from teltasync.system import DeviceStatusData
from teltasync.unauthorized import UnauthorizedStatusData
from tests.helpers import load_fixture


@pytest.fixture(name="unauthorized_status_fixture")
def fixture_unauthorized_status():
    """Load unauthorized status fixture data."""
    return load_fixture("unauthorized", "status.json")


@pytest.fixture(name="system_status_fixture")
def fixture_system_status():
    """Load system status fixture data."""
    return load_fixture("system", "device_status.json")


@pytest.fixture(name="modems_status_fixture")
def fixture_modems_status():
    """Load modems status fixture data."""
    return load_fixture("modems", "status.json")


@pytest.fixture(name="unauthorized_status_response")
def fixture_unauthorized_status_response(unauthorized_status_fixture):
    """Return parsed unauthorized status fixture response."""
    return ApiResponse[UnauthorizedStatusData](**unauthorized_status_fixture)


@pytest.fixture(name="system_status_response")
def fixture_system_status_response(system_status_fixture):
    """Return parsed system status fixture response."""
    return ApiResponse[DeviceStatusData](**system_status_fixture)


@pytest.fixture(name="modems_status_response")
def fixture_modems_status_response(modems_status_fixture):
    """Return parsed modems status fixture response."""
    return ApiResponse[list[ModemStatus]](**modems_status_fixture)


@pytest.fixture(name="client")
def fixture_client():
    """Create a Teltasync client with an external mock session."""
    mock_session = AsyncMock(spec=ClientSession)
    return Teltasync(
        base_url="https://192.168.1.1/api",
        username="admin",
        password="password",
        session=mock_session,
    )


@pytest.mark.asyncio
async def test_create_class_method_returns_client():
    """Test the create class method."""
    client = await Teltasync.create(
        base_url="https://192.168.1.1/api",
        username="admin",
        password="password",
        verify_ssl=False,
    )

    assert isinstance(client, Teltasync)
    session = client.session
    assert isinstance(session, ClientSession)

    await client.close()
    assert session.closed is True


@pytest.mark.asyncio
async def test_create_class_method_closes_managed_session():
    """Test create() closes the lazily created managed session."""
    mock_session = AsyncMock(spec=ClientSession)

    with patch("teltasync.teltasync.ClientSession", return_value=mock_session):
        client = await Teltasync.create(
            base_url="https://192.168.1.1/api",
            username="admin",
            password="password",
        )
        _ = client.session
        await client.close()

    mock_session.close.assert_called_once()


@pytest.mark.asyncio
async def test_close_with_external_session_does_not_close_it(client):
    """Test closing client with external session does not close it."""
    external_session = client.session
    await client.close()
    external_session.close.assert_not_called()


@pytest.mark.asyncio
async def test_async_context_manager_with_external_session(client):
    """Test using Teltasync as async context manager."""
    async with client as wrapped_client:
        assert wrapped_client is client


@pytest.mark.asyncio
async def test_get_device_info_from_fixture(
    client,
    unauthorized_status_response,
    snapshot,
):
    """Test device info retrieval against fixture content."""
    client.unauthorized.get_status = AsyncMock(
        return_value=unauthorized_status_response
    )

    result = await client.get_device_info()
    assert result == snapshot


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case",
    [
        pytest.param(
            (
                "get_device_info",
                "unauthorized",
                "get_status",
                ApiResponse[UnauthorizedStatusData](success=False, data=None),
                "Failed to get device info",
            ),
            id="device_info",
        ),
        pytest.param(
            (
                "get_system_info",
                "system",
                "get_device_status",
                ApiResponse[DeviceStatusData](success=False, data=None),
                "Failed to get system info",
            ),
            id="system_info",
        ),
        pytest.param(
            (
                "get_modem_status",
                "modems",
                "get_status",
                ApiResponse[list](success=False),
                "Failed to get modem status",
            ),
            id="modem_status",
        ),
    ],
)
async def test_endpoint_failure_raises_connection_error(client, case):
    """Test endpoint methods raise connection errors on unsuccessful responses."""
    method_name, component_name, component_method, response, error_message = case
    component = getattr(client, component_name)
    setattr(component, component_method, AsyncMock(return_value=response))

    with pytest.raises(TeltonikaConnectionError, match=error_message):
        await getattr(client, method_name)()


@pytest.mark.parametrize(
    ("auth_side_effect", "expected"),
    [(None, True), (TeltonikaAuthenticationError("Invalid credentials"), False)],
)
@pytest.mark.asyncio
async def test_validate_credentials(client, auth_side_effect, expected: bool):
    """Test credential validation outcome for success and auth failure."""
    if auth_side_effect is None:
        client.auth.authenticate = AsyncMock()
    else:
        client.auth.authenticate = AsyncMock(side_effect=auth_side_effect)
    client.auth.logout = AsyncMock()

    result = await client.validate_credentials()
    assert result is expected


@pytest.mark.asyncio
async def test_get_system_info_from_fixture(
    client,
    system_status_response,
    snapshot,
):
    """Test system info retrieval against fixture content."""
    client.system.get_device_status = AsyncMock(return_value=system_status_response)

    result = await client.get_system_info()
    assert result == snapshot


@pytest.mark.asyncio
async def test_get_modem_status_from_fixture(
    client,
    modems_status_response,
    snapshot,
):
    """Test modem status retrieval against fixture content."""
    client.modems.get_status = AsyncMock(return_value=modems_status_response)

    result = await client.get_modem_status()
    first_modem = result[0]

    assert len(result) == 1
    assert isinstance(first_modem, ModemStatusFull)
    assert result == snapshot


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (ApiResponse[dict](success=True), True),
        (ApiResponse[dict](success=False), False),
        (None, False),
    ],
)
@pytest.mark.asyncio
async def test_reboot_device_outcome(client, response, expected: bool):
    """Test reboot_device return value mapping."""
    client.system.reboot = AsyncMock(return_value=response)

    result = await client.reboot_device()
    assert result is expected


@pytest.mark.parametrize(
    ("method_name", "action_method"),
    [
        ("reboot_modem", "reboot_modem"),
        ("restart_connection", "restart_connection"),
        ("switch_sim", "switch_sim"),
    ],
)
@pytest.mark.asyncio
async def test_modem_action_success_returns_none(client, method_name, action_method):
    """Test modem actions return None on success."""
    setattr(
        client.modems,
        action_method,
        AsyncMock(return_value=ApiResponse[dict](success=True)),
    )

    result = await getattr(client, method_name)("2-1")
    assert result is None


@pytest.mark.parametrize(
    ("method_name", "action_method", "error_message"),
    [
        ("reboot_modem", "reboot_modem", "Failed to reboot modem"),
        (
            "restart_connection",
            "restart_connection",
            "Failed to restart modem connection",
        ),
        ("switch_sim", "switch_sim", "Failed to switch modem SIM"),
    ],
)
@pytest.mark.asyncio
async def test_modem_action_failure_raises(
    client, method_name, action_method, error_message
):
    """Test modem actions raise on unsuccessful API responses."""
    setattr(
        client.modems,
        action_method,
        AsyncMock(return_value=ApiResponse[dict](success=False)),
    )

    with pytest.raises(TeltonikaConnectionError, match=error_message):
        await getattr(client, method_name)("2-1")


@pytest.mark.asyncio
async def test_modem_action_failure_without_errors_raises_connection_error(client):
    """Test modem action failure without API errors raises connection error."""
    client.modems.reboot_modem = AsyncMock(
        return_value=ApiResponse[dict](
            success=False,
            data={"message": "Action rejected"},
        )
    )

    with pytest.raises(TeltonikaConnectionError, match="Failed to reboot modem"):
        await client.reboot_modem("2-1")


@pytest.mark.asyncio
async def test_modem_action_failure_includes_api_error_details(client):
    """Test modem action failure uses the router API error message."""
    client.modems.restart_connection = AsyncMock(
        return_value=ApiResponse[dict](
            success=False,
            errors=[
                ApiError(
                    code=123,
                    error="Operation failed",
                    source="modem",
                    section="general",
                )
            ],
        )
    )

    with pytest.raises(
        TeltonikaException,
        match="Operation failed",
    ):
        await client.restart_connection("2-1")


@pytest.mark.asyncio
async def test_modem_action_auth_error_raises_authentication_error(client):
    """Test modem actions map auth-related API errors to auth exceptions."""
    client.modems.switch_sim = AsyncMock(
        return_value=ApiResponse[dict](
            success=False,
            errors=[ApiError(code=121, error="Login failed")],
        )
    )

    with pytest.raises(
        TeltonikaAuthenticationError,
        match=r"Login failed \(code 121\)",
    ):
        await client.switch_sim("2-1")


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (ApiResponse[dict](success=True), True),
        (ApiResponse[dict](success=False), False),
    ],
)
@pytest.mark.asyncio
async def test_logout_outcome(client, response, expected: bool):
    """Test logout return value mapping."""
    client.auth.logout = AsyncMock(return_value=response)

    result = await client.logout()
    assert result is expected


def test_rich_api_properties_are_cached(client):
    """Test that rich API clients are accessible and cached."""
    auth = client.auth
    system = client.system
    modems = client.modems
    unauthorized = client.unauthorized

    assert auth is client.auth
    assert system is client.system
    assert modems is client.modems
    assert unauthorized is client.unauthorized
