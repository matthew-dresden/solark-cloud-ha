"""Data update coordinator for SolArk Cloud."""

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api_client import SolarkCloudApiClient, SolarkCloudApiError
from .const import (
    CONF_SCAN_INTERVAL_SECONDS,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
)

logger = logging.getLogger(__name__)


class SolarkCloudCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching SolArk Cloud data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: SolarkCloudApiClient,
        plant_id: str,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL_SECONDS,
            entry.data.get(CONF_SCAN_INTERVAL_SECONDS, DEFAULT_SCAN_INTERVAL_SECONDS),
        )
        super().__init__(
            hass,
            logger,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.plant_id = plant_id
        self._entry = entry

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the API."""
        try:
            today_data = await self.client.async_get_today_energy(self.plant_id)
            month_data = await self.client.async_get_current_month_energy(self.plant_id)
            realtime = await self.client.async_get_realtime_power(self.plant_id)

            now = self.client._now()
            return {
                "today": today_data,
                "month": month_data,
                "realtime": realtime,
                "year": str(now.year),
                "plant_id": self.plant_id,
                "last_updated": now.isoformat(),
            }
        except SolarkCloudApiError as err:
            raise UpdateFailed(f"Error fetching SolArk Cloud data: {err}") from err
