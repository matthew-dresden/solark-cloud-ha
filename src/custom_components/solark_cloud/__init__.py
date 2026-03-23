"""SolArk Cloud integration for Home Assistant."""

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse

from .api_client import SolarkCloudApiClient
from .const import CONF_PLANT_ID, CONF_TIMEZONE, DEFAULT_TIMEZONE, DOMAIN, HISTORY_IMPORT_YEARS
from .coordinator import SolarkCloudCoordinator

logger = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

SERVICE_FETCH_ENERGY = "fetch_energy"
SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("period"): vol.In(["day", "month", "year", "total"]),
        vol.Required("date"): str,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SolArk Cloud from a config entry."""
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

    # Register the fetch_energy service for the custom card
    async def handle_fetch_energy(call: ServiceCall) -> ServiceResponse:
        """Fetch energy data from SolarkCloud API on demand."""
        period = call.data["period"]
        date = call.data["date"]

        # Find the first coordinator
        for coord in hass.data.get(DOMAIN, {}).values():
            if isinstance(coord, SolarkCloudCoordinator):
                plant_id = coord.plant_id
                if period == "day":
                    raw = await coord.client.async_get_energy_day(plant_id, date)
                elif period == "month":
                    raw = await coord.client.async_get_energy_month(plant_id, date)
                elif period == "year":
                    raw = await coord.client.async_get_energy_year(plant_id, date)
                elif period == "total":
                    # Fetch all available years and aggregate yearly totals

                    now = coord.client._now()
                    current_year = now.year
                    series: dict[str, list[dict[str, object]]] = {}
                    for yr in range(current_year - HISTORY_IMPORT_YEARS, current_year + 1):
                        try:
                            yr_data = await coord.client.async_get_year_energy(plant_id, str(yr))
                            if yr_data:
                                for month_vals in yr_data.values():
                                    for label in month_vals:
                                        if label not in series:
                                            series[label] = []
                                # Sum each year's totals
                                year_totals: dict[str, float] = {}
                                for month_vals in yr_data.values():
                                    for label, value in month_vals.items():
                                        year_totals[label] = year_totals.get(label, 0) + value
                                for label, total in year_totals.items():
                                    if label not in series:
                                        series[label] = []
                                    series[label].append({"time": str(yr), "value": round(total, 1)})
                        except Exception:
                            pass
                    return {"period": "total", "date": "all", "plant_id": plant_id, "series": series}
                else:
                    return {"error": f"Unknown period: {period}"}

                # Flatten the response for the frontend
                series: dict[str, list[dict[str, object]]] = {}
                for info in raw.get("data", {}).get("infos", []):
                    label = info.get("label", "")
                    series[label] = [
                        {"time": r.get("time", ""), "value": float(r.get("value", 0))} for r in info.get("records", [])
                    ]

                return {"period": period, "date": date, "plant_id": plant_id, "series": series}

        return {"error": "No SolArk Cloud integration configured"}

    if not hass.services.has_service(DOMAIN, SERVICE_FETCH_ENERGY):
        hass.services.async_register(
            DOMAIN,
            SERVICE_FETCH_ENERGY,
            handle_fetch_energy,
            schema=SERVICE_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.client.async_close()
    return unload_ok
