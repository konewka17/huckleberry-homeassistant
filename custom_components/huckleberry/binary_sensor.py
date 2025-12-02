"""Binary sensor platform for Huckleberry."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Huckleberry binary sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    children = data["children"]

    entities = []
    for child in children:
        entities.append(HuckleberrySleepSensor(coordinator, child))
        entities.append(HuckleberryFeedingSensor(coordinator, child))

    async_add_entities(entities)


class HuckleberrySleepSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Huckleberry sleep sensor."""

    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_icon = "mdi:sleep"

    def __init__(self, coordinator, child: dict[str, Any]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._child = child
        self.child_uid = child["uid"]
        self.child_name = child["name"]

        self._attr_has_entity_name = True
        self._attr_name = "Sleep status"
        self._attr_unique_id = f"{self.child_uid}_sleep_status"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.child_uid)},
            "name": self.child_name,
            "manufacturer": "Huckleberry",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the baby is sleeping."""
        if self.child_uid not in self.coordinator.data:
            return False

        sleep_status = self.coordinator.data[self.child_uid].get("sleep_status", {})

        # Check real-time timer data structure
        if isinstance(sleep_status, dict) and "timer" in sleep_status:
            timer = sleep_status.get("timer", {})
            return timer.get("active", False) and not timer.get("paused", False)

        # Fallback to old structure
        return sleep_status.get("is_sleeping", False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        if self.child_uid not in self.coordinator.data:
            return {}

        sleep_status = self.coordinator.data[self.child_uid].get("sleep_status", {})

        attrs = {}

        # Handle real-time data structure
        if isinstance(sleep_status, dict) and "timer" in sleep_status:
            timer = sleep_status.get("timer", {})
            prefs = sleep_status.get("prefs", {})

            # Track paused state
            if timer.get("active"):
                attrs["is_paused"] = timer.get("paused", False)

            if timer.get("active") and not timer.get("paused"):
                # Currently sleeping
                if "timestamp" in timer:
                    attrs["sleep_start"] = timer["timestamp"].get("seconds")
                # timerStartTime is in milliseconds for sleep tracking
                if "timerStartTime" in timer:
                    attrs["timer_start_time_ms"] = timer.get("timerStartTime")
                    # Convert to seconds for chronometer (Home Assistant expects Unix timestamp)
                    attrs["timer_start_time"] = int(timer.get("timerStartTime") / 1000)

            # Last sleep info
            if "lastSleep" in prefs:
                last_sleep = prefs["lastSleep"]
                attrs["last_sleep_duration_seconds"] = last_sleep.get("duration")
                attrs["last_sleep_start"] = last_sleep.get("start")
        else:
            # Fallback to legacy computed structure
            attrs["last_updated"] = sleep_status.get("last_updated")

            duration = sleep_status.get("sleep_duration")
            start = sleep_status.get("sleep_start")
            if start:
                attrs["sleep_start"] = start
            if duration is not None:
                attrs["sleep_duration_seconds"] = duration
                hours = int(duration // 3600)
                minutes = int((duration % 3600) // 60)
                attrs["sleep_duration"] = f"{hours}h {minutes}m"

        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.child_uid in self.coordinator.data
        )


class HuckleberryFeedingSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Huckleberry feeding sensor."""

    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_icon = "mdi:baby-bottle"

    def __init__(self, coordinator, child: dict[str, Any]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._child = child
        self.child_uid = child["uid"]
        self.child_name = child["name"]

        self._attr_has_entity_name = True
        self._attr_name = "Feeding status"
        self._attr_unique_id = f"{self.child_uid}_feeding_status"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.child_uid)},
            "name": self.child_name,
            "manufacturer": "Huckleberry",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the baby is feeding."""
        if self.child_uid not in self.coordinator.data:
            return False

        feed_status = self.coordinator.data[self.child_uid].get("feed_status", {})

        # Check real-time timer data structure
        if isinstance(feed_status, dict) and "timer" in feed_status:
            timer = feed_status.get("timer", {})
            return timer.get("active", False) and not timer.get("paused", False)

        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        if self.child_uid not in self.coordinator.data:
            return {}

        feed_status = self.coordinator.data[self.child_uid].get("feed_status", {})

        attrs = {}

        # Handle real-time data structure
        if isinstance(feed_status, dict) and "timer" in feed_status:
            timer = feed_status.get("timer", {})
            prefs = feed_status.get("prefs", {})

            if timer.get("active") and not timer.get("paused"):
                # Currently feeding
                if "timestamp" in timer:
                    attrs["feeding_start"] = timer["timestamp"].get("seconds")
                attrs["left_duration_seconds"] = timer.get("leftDuration", 0)
                attrs["right_duration_seconds"] = timer.get("rightDuration", 0)
                attrs["last_side"] = timer.get("lastSide", "unknown")

            # Last feeding info
            if "lastNursing" in prefs:
                last_nursing = prefs["lastNursing"]
                attrs["last_nursing_start"] = last_nursing.get("start")
                attrs["last_nursing_duration_seconds"] = last_nursing.get("duration")
                attrs["last_nursing_left_seconds"] = last_nursing.get("leftDuration", 0)
                attrs["last_nursing_right_seconds"] = last_nursing.get("rightDuration", 0)

        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.child_uid in self.coordinator.data
        )
