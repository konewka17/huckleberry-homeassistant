"""Sensor platform for Huckleberry."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
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
    """Set up Huckleberry sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    children = data["children"]

    entities: list[SensorEntity] = [HuckleberryChildrenSensor(coordinator, children)]

    # Add individual child profile sensor for each child
    for child in children:
        entities.append(HuckleberryChildProfileSensor(coordinator, child))
        # Add growth sensor for each child
        entities.append(HuckleberryGrowthSensor(coordinator, child))
        # Add diaper sensor for each child
        entities.append(HuckleberryDiaperSensor(coordinator, child))

    async_add_entities(entities)


class HuckleberryChildrenSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing children information."""

    _attr_icon = "mdi:account-child"
    _attr_native_unit_of_measurement = "children"

    def __init__(self, coordinator, children: list[dict[str, Any]]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._children = children

        self._attr_name = "Huckleberry Children"
        self._attr_unique_id = "huckleberry_children"

    @property
    def native_value(self) -> int:
        """Return the count of children."""
        return len(self._children)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            "children": [
                {
                    "uid": child["uid"],
                    "name": child["name"],
                    "birthday": child.get("birthday"),
                    "picture": child.get("picture"),
                    "gender": child.get("gender"),
                    "color": child.get("color"),
                    "created_at": child.get("created_at"),
                    "night_start": child.get("night_start"),
                    "morning_cutoff": child.get("morning_cutoff"),
                    "expected_naps": child.get("expected_naps"),
                    "categories": child.get("categories"),
                }
                for child in self._children
            ],
            "child_ids": [child["uid"] for child in self._children],
            "child_names": [child["name"] for child in self._children],
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success


class HuckleberryChildProfileSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing individual child profile information."""

    _attr_icon = "mdi:account"

    def __init__(self, coordinator, child: dict[str, Any]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._child = child
        self.child_uid = child["uid"]
        self.child_name = child["name"]

        self._attr_has_entity_name = True
        self._attr_name = None
        self._attr_unique_id = f"{self.child_uid}_profile"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        device_info = {
            "identifiers": {(DOMAIN, self.child_uid)},
            "name": self.child_name,
            "manufacturer": "Huckleberry",
        }
        # Add profile picture as configuration_url if available
        if self._child.get("picture"):
            device_info["configuration_url"] = self._child["picture"]
        return device_info

    @property
    def native_value(self) -> str:
        """Return the child's name as the state."""
        return self.child_name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return child profile attributes."""
        attrs = {
            "uid": self.child_uid,
            "name": self.child_name,
        }

        # Add all available child attributes
        optional_fields = [
            "birthday", "picture", "gender", "color", "created_at",
            "night_start", "morning_cutoff", "expected_naps", "categories"
        ]
        for field in optional_fields:
            if self._child.get(field) is not None:
                attrs[field] = self._child[field]

        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success


class HuckleberryGrowthSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing child growth measurements."""

    _attr_icon = "mdi:human-male-height"

    def __init__(self, coordinator, child: dict[str, Any]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.child_uid = child["uid"]
        self.child_name = child["name"]

        self._attr_has_entity_name = True
        self._attr_name = "Growth"
        self._attr_unique_id = f"{self.child_uid}_growth"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        device_info = {
            "identifiers": {(DOMAIN, self.child_uid)},
            "name": self.child_name,
            "manufacturer": "Huckleberry",
        }
        return device_info

    @property
    def native_value(self) -> str | None:
        """Return the most recent measurement timestamp."""
        child_data = self.coordinator.data.get(self.child_uid, {})
        growth_data = child_data.get("growth_data", {})

        if not growth_data:
            return "No data"

        timestamp = growth_data.get("timestamp")
        if timestamp:
            from datetime import datetime
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")

        return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return growth measurement attributes."""
        child_data = self.coordinator.data.get(self.child_uid, {})
        growth_data = child_data.get("growth_data", {})

        if not growth_data:
            return {}

        attrs = {}

        # Add measurements if available
        weight = growth_data.get("weight")
        height = growth_data.get("height")
        head = growth_data.get("head")

        if weight is not None:
            weight_unit = growth_data.get("weight_units", "kg")
            attrs["weight"] = weight
            attrs["weight_unit"] = weight_unit
            attrs["weight_display"] = f"{weight} {weight_unit}"

        if height is not None:
            height_unit = growth_data.get("height_units", "cm")
            attrs["height"] = height
            attrs["height_unit"] = height_unit
            attrs["height_display"] = f"{height} {height_unit}"

        if head is not None:
            head_unit = growth_data.get("head_units", "hcm")
            attrs["head_circumference"] = head
            attrs["head_unit"] = head_unit
            attrs["head_display"] = f"{head} {head_unit}"

        timestamp = growth_data.get("timestamp")
        if timestamp:
            from datetime import datetime
            attrs["last_measured"] = datetime.fromtimestamp(timestamp).isoformat()

        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success


class HuckleberryDiaperSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing last diaper change information."""

    _attr_icon = "mdi:baby"

    def __init__(self, coordinator, child: dict[str, Any]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.child_uid = child["uid"]
        self.child_name = child["name"]

        self._attr_has_entity_name = True
        self._attr_name = "Last Diaper"
        self._attr_unique_id = f"{self.child_uid}_last_diaper"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.child_uid)},
            "name": self.child_name,
            "manufacturer": "Huckleberry",
        }

    @property
    def native_value(self) -> str | None:
        """Return the last diaper change timestamp."""
        child_data = self.coordinator.data.get(self.child_uid, {})
        diaper_data = child_data.get("diaper_data", {})

        prefs = diaper_data.get("prefs", {})
        last_diaper = prefs.get("lastDiaper", {})

        if not last_diaper:
            return "No changes logged"

        timestamp = last_diaper.get("start")
        if timestamp:
            from datetime import datetime
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")

        return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return diaper change attributes."""
        child_data = self.coordinator.data.get(self.child_uid, {})
        diaper_data = child_data.get("diaper_data", {})

        prefs = diaper_data.get("prefs", {})
        last_diaper = prefs.get("lastDiaper", {})

        if not last_diaper:
            return {}

        attrs = {}

        # Add timestamp
        timestamp = last_diaper.get("start")
        if timestamp:
            from datetime import datetime
            attrs["timestamp"] = timestamp
            attrs["time"] = datetime.fromtimestamp(timestamp).isoformat()

        # Add mode (pee, poo, both, dry)
        mode = last_diaper.get("mode")
        if mode:
            attrs["mode"] = mode
            attrs["type"] = mode.capitalize()

        # Add offset (timezone)
        offset = last_diaper.get("offset")
        if offset is not None:
            attrs["timezone_offset_minutes"] = offset

        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

