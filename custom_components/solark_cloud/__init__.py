"""SolArk Cloud integration for Home Assistant."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant

from .api_client import SolarkCloudApiClient
from .const import CONF_PLANT_ID, CONF_TIMEZONE, DEFAULT_TIMEZONE, DOMAIN
from .coordinator import SolarkCloudCoordinator

logger = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SolArk Cloud from a config entry."""
    # Resolve timezone: config entry > HA config > OS default
    tz_name = entry.data.get(CONF_TIMEZONE, DEFAULT_TIMEZONE)
    if not tz_name:
        tz_name = hass.config.time_zone or ""

    client = SolarkCloudApiClient(
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        tz_name=tz_name,
    )
    await client.async_init()

    coordinator = SolarkCloudCoordinator(
        hass=hass,
        client=client,
        plant_id=entry.data[CONF_PLANT_ID],
        entry=entry,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.client.async_close()
    return unload_ok
