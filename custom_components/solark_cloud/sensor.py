"""Sensor platform for SolArk Cloud integration."""

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ENERGY_LABELS
from .coordinator import SolarkCloudCoordinator

logger = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS: dict[str, dict[str, Any]] = {
    "PV": {
        "name": "Solar Production",
        "icon": "mdi:solar-power-variant",
    },
    "Load": {
        "name": "Home Consumption",
        "icon": "mdi:home-lightning-bolt",
    },
    "Export": {
        "name": "Grid Export",
        "icon": "mdi:transmission-tower-export",
    },
    "Import": {
        "name": "Grid Import",
        "icon": "mdi:transmission-tower-import",
    },
    "Charge": {
        "name": "Battery Charge",
        "icon": "mdi:battery-charging",
    },
    "Discharge": {
        "name": "Battery Discharge",
        "icon": "mdi:battery-arrow-down",
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SolArk Cloud sensor entities."""
    coordinator: SolarkCloudCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    for label in ENERGY_LABELS:
        description = SENSOR_DESCRIPTIONS.get(label, {"name": label, "icon": "mdi:flash"})
        # Today sensor
        entities.append(
            SolarkCloudEnergySensor(
                coordinator=coordinator,
                label=label,
                period="today",
                name=f"{description['name']} Today",
                icon=description["icon"],
            )
        )
        # Month sensor
        entities.append(
            SolarkCloudEnergySensor(
                coordinator=coordinator,
                label=label,
                period="month",
                name=f"{description['name']} This Month",
                icon=description["icon"],
            )
        )

    # Real-time power sensors
    realtime_sensors = [
        {"key": "pv_power", "name": "Solar Power", "icon": "mdi:solar-power-variant", "device_class": SensorDeviceClass.POWER, "unit": UnitOfPower.WATT},
        {"key": "load_power", "name": "Home Power", "icon": "mdi:home-lightning-bolt", "device_class": SensorDeviceClass.POWER, "unit": UnitOfPower.WATT},
        {"key": "grid_power", "name": "Grid Power", "icon": "mdi:transmission-tower", "device_class": SensorDeviceClass.POWER, "unit": UnitOfPower.WATT},
        {"key": "battery_power", "name": "Battery Power", "icon": "mdi:battery-charging", "device_class": SensorDeviceClass.POWER, "unit": UnitOfPower.WATT},
        {"key": "battery_soc", "name": "Battery SOC", "icon": "mdi:battery", "device_class": SensorDeviceClass.BATTERY, "unit": PERCENTAGE},
    ]
    for desc in realtime_sensors:
        entities.append(
            SolarkCloudRealtimeSensor(
                coordinator=coordinator,
                key=desc["key"],
                name=desc["name"],
                icon=desc["icon"],
                device_class=desc["device_class"],
                unit=desc["unit"],
            )
        )

    async_add_entities(entities)


class SolarkCloudRealtimeSensor(CoordinatorEntity[SolarkCloudCoordinator], SensorEntity):
    """Sensor for real-time power readings (watts) and battery SOC (%)."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True
    _attr_suggested_display_precision = 0

    def __init__(
        self,
        coordinator: SolarkCloudCoordinator,
        key: str,
        name: str,
        icon: str,
        device_class: SensorDeviceClass,
        unit: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"solark_{coordinator.plant_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.plant_id)},
            "name": f"SolArk Plant {coordinator.plant_id} by Dresdencraft",
            "manufacturer": "Dresdencraft",
            "model": "SolArk Cloud Integration",
        }

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        realtime = self.coordinator.data.get("realtime", {})
        value = realtime.get(self._key)
        if value is not None:
            return round(float(value), 1)
        return None


class SolarkCloudEnergySensor(CoordinatorEntity[SolarkCloudCoordinator], SensorEntity):
    """Sensor entity for SolArk Cloud energy data."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_has_entity_name = True
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: SolarkCloudCoordinator,
        label: str,
        period: str,
        name: str,
        icon: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._label = label
        self._period = period
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"solark_{coordinator.plant_id}_{label.lower()}_{period}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.plant_id)},
            "name": f"SolArk Plant {coordinator.plant_id} by Dresdencraft",
            "manufacturer": "Dresdencraft",
            "model": "SolArk Cloud Integration",
        }

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        period_data = self.coordinator.data.get(self._period, {})
        value = period_data.get(self._label)
        if value is not None:
            return round(float(value), 1)
        return None
