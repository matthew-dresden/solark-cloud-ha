"""Data update coordinator for SolArk Cloud."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api_client import SolarkCloudApiClient, SolarkCloudApiError
from .const import (
    CONF_IMPORT_HISTORY,
    CONF_SCAN_INTERVAL_SECONDS,
    DEFAULT_IMPORT_HISTORY,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    ENERGY_LABELS,
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
        self._history_imported = False

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the API."""
        try:
            # Import history on first run if enabled
            if not self._history_imported:
                import_history = self._entry.data.get(CONF_IMPORT_HISTORY, DEFAULT_IMPORT_HISTORY)
                if import_history:
                    await self._async_import_history()
                self._history_imported = True

            today_data = await self.client.async_get_today_energy(self.plant_id)
            month_data = await self.client.async_get_current_month_energy(self.plant_id)
            year_data = await self.client.async_get_current_year_energy(self.plant_id)
            realtime = await self.client.async_get_realtime_power(self.plant_id)

            now = self.client._now()
            return {
                "today": today_data,
                "month": month_data,
                "year_totals": year_data,
                "realtime": realtime,
                "year": str(now.year),
                "plant_id": self.plant_id,
                "last_updated": now.isoformat(),
            }
        except SolarkCloudApiError as err:
            raise UpdateFailed(f"Error fetching SolArk Cloud data: {err}") from err

    async def _async_import_history(self) -> None:
        """Import all available historical data as HA long-term statistics."""
        now = self.client._now()
        current_year = now.year

        # Import current year and up to 4 previous years
        years_to_import = [str(y) for y in range(current_year - 4, current_year + 1)]

        logger.info("Importing historical statistics for years: %s", years_to_import)

        for year in years_to_import:
            try:
                year_data = await self.client.async_get_year_energy(self.plant_id, year)
                if year_data:
                    self._import_year_statistics(year, year_data)
                    logger.info("Imported %d months of statistics for year %s", len(year_data), year)
            except SolarkCloudApiError:
                logger.debug("No data available for year %s", year)

    def _import_year_statistics(self, year: str, year_data: dict[str, dict[str, float]]) -> None:
        """Import a year of monthly data as HA long-term statistics."""
        for label in ENERGY_LABELS:
            statistic_id = f"{DOMAIN}:plant_{self.plant_id}_{label.lower()}_monthly"
            metadata = StatisticMetaData(
                has_mean=False,
                has_sum=True,
                name=f"SolArk {label} Monthly ({self.plant_id})",
                source=DOMAIN,
                statistic_id=statistic_id,
                unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            )

            statistics: list[StatisticData] = []
            cumulative = 0.0
            for month_key in sorted(year_data.keys()):
                month_data = year_data[month_key]
                value = month_data.get(label, 0.0)
                cumulative += value

                parts = month_key.split("-")
                month_dt = datetime(int(parts[0]), int(parts[1]), 1, tzinfo=timezone.utc)

                statistics.append(StatisticData(start=month_dt, sum=cumulative, state=value))

            if statistics:
                async_add_external_statistics(self.hass, metadata, statistics)
