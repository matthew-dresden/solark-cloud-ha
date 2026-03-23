"""Diagnostics support for SolArk Cloud integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import SolarkCloudCoordinator

REDACTED = "**REDACTED**"


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = dict(entry.data)
    if CONF_PASSWORD in data:
        data[CONF_PASSWORD] = REDACTED

    coordinator: SolarkCloudCoordinator = hass.data[DOMAIN][entry.entry_id]

    return {
        "config_entry": data,
        "coordinator_data": coordinator.data if coordinator.data else {},
        "last_update_success": coordinator.last_update_success,
        "plant_id": coordinator.plant_id,
    }
