"""Define tests for the Sensor objects."""
import aiohttp
import pytest

from simplipy import get_systems
from simplipy.sensor import SensorTypes

from .const import TEST_EMAIL, TEST_PASSWORD
from .fixtures import *
from .fixtures.v2 import *
from .fixtures.v3 import *


@pytest.mark.asyncio
async def test_properties_base(event_loop, v2_server):
    """Test that base sensor properties are created properly."""
    async with v2_server:
        async with aiohttp.ClientSession(loop=event_loop) as websession:
            [system] = await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)

            sensor = system.sensors['195']
            assert sensor.name == 'Garage Keypad'
            assert sensor.serial == '195'
            assert sensor.type == SensorTypes.keypad


@pytest.mark.asyncio
async def test_properties_v2(event_loop, v2_server):
    """Test that v2 sensor properties are created properly."""
    async with v2_server:
        async with aiohttp.ClientSession(loop=event_loop) as websession:
            [system] = await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)

            sensor = system.sensors['195']
            assert sensor.data == 0
            assert not sensor.error
            assert not sensor.low_battery
            assert sensor.settings == 1
            assert not sensor.triggered


@pytest.mark.asyncio
async def test_properties_v3(event_loop, v3_server):
    """Test that v3 sensor properties are created properly."""
    async with v3_server:
        async with aiohttp.ClientSession(loop=event_loop) as websession:
            [system] = await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)

            entry_sensor = system.sensors['825']
            assert not entry_sensor.error
            assert not entry_sensor.low_battery
            assert not entry_sensor.offline
            assert not entry_sensor.settings['instantTrigger']
            assert not entry_sensor.triggered

            siren = system.sensors['236']
            assert not siren.triggered

            temperature_sensor = system.sensors['320']
            assert temperature_sensor.temperature == 67

            # Ensure that attempting to access the temperature attribute of a
            # non-temperature sensor throws an error:
            with pytest.raises(ValueError):
                assert siren.temperature == 42


@pytest.mark.asyncio
async def test_unknown_sensor_type(caplog, event_loop, v2_server):
    """Test that a message is logged when unknown sensors types are found."""
    async with v2_server:
        async with aiohttp.ClientSession(loop=event_loop) as websession:
            await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)
            assert any('Unknown' in e.message for e in caplog.records)