# teltasync

teltasync is an async python library for interfacing with Teltonika routers via their HTTP API.

## Installation

You can install the library using pip:

```bash
pip install teltasync
```

## Usage

This is a simple example of how to use the library:

```python
import asyncio

from teltasync import Teltasync


async def main():
    # Create client
    client = Teltasync(
        base_url="https://192.168.1.1/api",  # Full API URL
        username="admin",  # Admin username
        password="YOUR_PASSWORD",  # Admin password
        verify_ssl=False  # Most Teltonika devices use self-signed certs
    )

    try:
        # Get basic device info (no authentication required)
        device_info = await client.get_device_info()
        print(f"Device: {device_info.device_name} ({device_info.device_model})")

        # Validate credentials
        if await client.validate_credentials():
            print("Credentials are valid!")

            # Get detailed system information
            system_info = await client.get_system_info()
            print(f"Firmware version: {system_info.static.fw_version}")

            # Get modem status
            modems = await client.get_modem_status()
            for modem in modems:
                print(f"Modem {modem.id}: {modem.operator} ({modem.conntype})")
                print(f"  Signal: {modem.rssi} dBm")

        else:
            print("Invalid credentials!")

    finally:
        # Always close the session
        await client.close()


# Using as async context manager (recommended)
async def context_manager_example():
    async with Teltasync(
            base_url="https://192.168.1.1/api",
            username="admin",
            password="YOUR_PASSWORD",
            verify_ssl=False
    ) as client:
        device_info = await client.get_device_info()
        print(f"Device: {device_info.device_name}")
        # Session automatically closed when exiting context


# Run the example
if __name__ == "__main__":
    asyncio.run(main())
```

## Supported Devices

Although it was currently only tested against a RUTX50, this library should work with most Teltonika routers that
support the [HTTP API](https://developers.teltonika-networks.com/), including:

- RUT series (RUT240, RUT241, RUT950, RUT955, etc.)
- RUTX series (RUTX09, RUTX11, RUTX12, etc.)
- TRB series gateways
- Other Teltonika devices with HTTP API support

## Requirements

- Python 3.13+
- aiohttp
- pydantic
