"""Tests for the IPBuilding API client."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.ipbuilding.api import (
    IPBuildingAPI,
    IPBuildingCannotConnect,
)


def _mock_response(status: int, json_data=None) -> MagicMock:
    """Build a MagicMock that quacks like aiohttp's response context manager."""
    resp = MagicMock()
    resp.status = status
    resp.raise_for_status = MagicMock()
    if json_data is not None:
        resp.json = AsyncMock(return_value=json_data)
    else:
        resp.json = AsyncMock(return_value=None)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=None)
    return resp


async def test_get_devices_returns_list() -> None:
    """A JSON array response should be returned as-is."""
    session = MagicMock()
    session.get = MagicMock(return_value=_mock_response(200, [{"ID": 1, "Type": 1}]))
    api = IPBuildingAPI("192.0.2.1", 30200, session)

    result = await api.get_devices()

    assert result == [{"ID": 1, "Type": 1}]


async def test_get_devices_wraps_single_dict() -> None:
    """A single-object JSON response should be wrapped in a list."""
    session = MagicMock()
    session.get = MagicMock(return_value=_mock_response(200, {"ID": 1, "Type": 1}))
    api = IPBuildingAPI("192.0.2.1", 30200, session)

    result = await api.get_devices()

    assert result == [{"ID": 1, "Type": 1}]


async def test_get_devices_unwraps_items_key() -> None:
    """A {'items': [...]} response should be unwrapped to the inner list."""
    session = MagicMock()
    session.get = MagicMock(return_value=_mock_response(200, {"items": [{"ID": 1}]}))
    api = IPBuildingAPI("192.0.2.1", 30200, session)

    result = await api.get_devices()

    assert result == [{"ID": 1}]


async def test_get_devices_type_filter() -> None:
    """A type filter should drop devices whose Type is not in the filter."""
    session = MagicMock()
    session.get = MagicMock(
        return_value=_mock_response(
            200,
            [
                {"ID": 1, "Type": 1},
                {"ID": 2, "Type": 2},
                {"ID": 3, "Type": 1},
            ],
        )
    )
    api = IPBuildingAPI("192.0.2.1", 30200, session)

    result = await api.get_devices([1])

    assert {d["ID"] for d in result} == {1, 3}


async def test_get_devices_timeout_raises_cannot_connect() -> None:
    """An asyncio.TimeoutError should surface as IPBuildingCannotConnect."""
    session = MagicMock()
    session.get = MagicMock(
        side_effect=asyncio.TimeoutError(),
    )
    api = IPBuildingAPI("192.0.2.1", 30200, session, timeout=0.05)

    with pytest.raises(IPBuildingCannotConnect):
        await api.get_devices()


async def test_get_devices_client_error_raises_cannot_connect() -> None:
    """An aiohttp.ClientError should surface as IPBuildingCannotConnect."""
    session = MagicMock()
    session.get = MagicMock(
        side_effect=aiohttp.ClientError("connection refused"),
    )
    api = IPBuildingAPI("192.0.2.1", 30200, session)

    with pytest.raises(IPBuildingCannotConnect):
        await api.get_devices()


async def test_set_value_default_action_type() -> None:
    """When action_type is None and value=0, default to 'OFF'; otherwise 'DIM'."""
    session = MagicMock()
    session.get = MagicMock(return_value=_mock_response(200, None))
    api = IPBuildingAPI("192.0.2.1", 30200, session)

    await api.set_value(42, 0)
    _args, kwargs = session.get.call_args
    assert kwargs["params"]["actionType"] == "OFF"
    assert kwargs["params"]["value"] == 0

    session.get.reset_mock()
    await api.set_value(42, 50)
    _args, kwargs = session.get.call_args
    assert kwargs["params"]["actionType"] == "DIM"
    assert kwargs["params"]["value"] == 50


async def test_set_value_uses_write_timeout() -> None:
    """set_value should use the constructor's write_timeout, not the read timeout."""
    session = MagicMock()
    session.get = MagicMock(return_value=_mock_response(200, None))
    api = IPBuildingAPI("192.0.2.1", 30200, session, timeout=10.0, write_timeout=2.0)

    # Patch asyncio.timeout to record the values it was called with.
    seen: list[float] = []
    import contextlib

    @contextlib.asynccontextmanager
    async def _fake_timeout(value: float):
        seen.append(value)
        yield

    import custom_components.ipbuilding.api as api_mod

    real_timeout = api_mod.asyncio.timeout
    api_mod.asyncio.timeout = _fake_timeout  # type: ignore[assignment]
    try:
        await api.set_value(1, 1, "ON")
    finally:
        api_mod.asyncio.timeout = real_timeout  # type: ignore[assignment]

    assert seen == [2.0]


async def test_validate_connection_propagates_cannot_connect() -> None:
    """validate_connection should re-raise IPBuildingCannotConnect unchanged."""
    session = MagicMock()
    session.get = MagicMock(
        side_effect=aiohttp.ClientError("refused"),
    )
    api = IPBuildingAPI("192.0.2.1", 30200, session)

    with pytest.raises(IPBuildingCannotConnect):
        await api.validate_connection()
