"""Test Huckleberry binary sensors."""
from unittest.mock import patch, MagicMock
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from custom_components.huckleberry.const import DOMAIN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

async def test_binary_sensors(hass: HomeAssistant, mock_huckleberry_api):
    """Test binary sensors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test_password",
        },
    )
    entry.add_to_hass(hass)

    # Mock coordinator data
    mock_huckleberry_api.get_children.return_value = [
        {
            "uid": "child_1",
            "name": "Test Child",
            "birthDate": "2023-01-01",
            "gender": "boy",
            "profilePictureUrl": None
        }
    ]

    with patch(
        "custom_components.huckleberry.HuckleberryAPI",
        return_value=mock_huckleberry_api,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # Get the coordinator
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Simulate sleep data update
    coordinator._realtime_data = {
        "child_1": {
            "sleep_status": {
                "timer": {"active": True, "paused": False},
                "prefs": {}
            },
            "feed_status": {
                "timer": {"active": True, "paused": False, "lastSide": "left"},
                "prefs": {}
            }
        }
    }
    coordinator.async_set_updated_data(coordinator._realtime_data)
    await hass.async_block_till_done()

    # Check sleep sensor
    state = hass.states.get("binary_sensor.test_child_sleep_status")
    assert state is not None
    assert state.state == "on"

    # Check feeding sensor
    state = hass.states.get("binary_sensor.test_child_feeding_status")
    assert state is not None
    assert state.state == "on"
    assert state.attributes.get("last_side") == "left"

    # Simulate awake and not feeding
    coordinator._realtime_data["child_1"]["sleep_status"]["timer"]["active"] = False
    coordinator._realtime_data["child_1"]["feed_status"]["timer"]["active"] = False
    coordinator.async_set_updated_data(coordinator._realtime_data)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_child_sleep_status")
    assert state.state == "off"

    state = hass.states.get("binary_sensor.test_child_feeding_status")
    assert state.state == "off"
