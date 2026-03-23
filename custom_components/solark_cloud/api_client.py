"""SolarkCloud API client for Home Assistant."""

import asyncio
import logging
from datetime import datetime, timezone
from functools import partial
from typing import Any
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import httpx

from .const import API_BASE_URL, API_CLIENT_ID, API_GRANT_TYPE

logger = logging.getLogger(__name__)


class SolarkCloudApiError(Exception):
    """Raised when the SolarkCloud API returns an error."""


class SolarkCloudAuthError(SolarkCloudApiError):
    """Raised when authentication fails."""


class SolarkCloudApiClient:
    """Async client for the SolarkCloud API."""

    def __init__(
        self,
        username: str,
        password: str,
        api_url: str = API_BASE_URL,
        tz_name: str = "",
    ) -> None:
        self._username = username
        self._password = password
        self._api_url = api_url.rstrip("/")
        self._tz_name = tz_name
        self._access_token: str | None = None
        self._client: httpx.AsyncClient | None = None

    def _now(self) -> datetime:
        """Get current time in the configured timezone."""
        if self._tz_name:
            return datetime.now(tz=ZoneInfo(self._tz_name))
        return datetime.now(tz=timezone.utc).astimezone()

    async def async_init(self) -> None:
        """Initialize the HTTP client (runs SSL setup in executor to avoid blocking)."""
        loop = asyncio.get_running_loop()
        self._client = await loop.run_in_executor(None, partial(httpx.AsyncClient, timeout=30))

    async def async_close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def async_authenticate(self) -> None:
        """Authenticate and store the access token."""
        if self._client is None:
            await self.async_init()

        url = f"{self._api_url}/oauth/token"
        payload = {
            "client_id": API_CLIENT_ID,
            "grant_type": API_GRANT_TYPE,
            "username": self._username,
            "password": self._password,
        }
        logger.info("Authenticating with SolarkCloud API")
        response = await self._client.post(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json;charset=UTF-8",
                "Origin": "https://www.solarkcloud.com",
                "Referer": "https://www.solarkcloud.com/",
            },
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            msg = f"Authentication failed: {data.get('msg', 'Unknown error')}"
            raise SolarkCloudAuthError(msg)
        self._access_token = data["data"]["access_token"]
        logger.info("Authentication successful")

    async def _async_get(self, url: str) -> dict[str, Any]:
        """Make an authenticated GET request."""
        if self._client is None:
            await self.async_init()
        if self._access_token is None:
            await self.async_authenticate()

        response = await self._client.get(
            url,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Accept": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            msg = f"API request failed: {data.get('msg', 'Unknown error')}"
            raise SolarkCloudApiError(msg)
        return data

    def _energy_url(self, plant_id: str, period: str, date: str) -> str:
        """Build an energy endpoint URL."""
        base = f"{self._api_url}/api/v1/plant/energy/{plant_id}/{period}"
        params = urlencode({"date": date, "id": plant_id, "lan": "en"})
        return f"{base}?{params}"

    async def async_get_energy_year(self, plant_id: str, year: str) -> dict[str, Any]:
        """Get yearly energy data (monthly breakdown)."""
        url = self._energy_url(plant_id, "year", year)
        logger.debug("Fetching year energy: %s", url)
        return await self._async_get(url)

    async def async_get_energy_month(self, plant_id: str, date: str) -> dict[str, Any]:
        """Get monthly energy data (daily breakdown)."""
        url = self._energy_url(plant_id, "month", date)
        logger.debug("Fetching month energy: %s", url)
        return await self._async_get(url)

    async def async_get_energy_day(self, plant_id: str, date: str) -> dict[str, Any]:
        """Get daily energy data (5-min intervals)."""
        url = self._energy_url(plant_id, "day", date)
        logger.debug("Fetching day energy: %s", url)
        return await self._async_get(url)

    async def async_get_current_month_energy(self, plant_id: str) -> dict[str, float]:
        """Get current month's energy totals."""
        now = self._now()
        year = str(now.year)
        month_key = now.strftime("%Y-%m")

        data = await self.async_get_energy_year(plant_id, year)
        totals: dict[str, float] = {}
        for info in data.get("data", {}).get("infos", []):
            label = info.get("label", "")
            for record in info.get("records", []):
                if record.get("time") == month_key:
                    totals[label] = float(record.get("value", 0))
        return totals

    async def async_get_current_year_energy(self, plant_id: str) -> dict[str, float]:
        """Get current year's energy totals (sum of all months)."""
        now = self._now()
        year = str(now.year)

        data = await self.async_get_energy_year(plant_id, year)
        totals: dict[str, float] = {}
        for info in data.get("data", {}).get("infos", []):
            label = info.get("label", "")
            year_sum = sum(float(r.get("value", 0)) for r in info.get("records", []))
            totals[label] = round(year_sum, 1)
        return totals

    async def async_get_today_energy(self, plant_id: str) -> dict[str, float]:
        """Get today's energy from the day endpoint (5-min intervals in watts).

        The day endpoint returns labels: PV, Battery, SOC, Grid, Load (in watts).
        - Grid positive = import, Grid negative = export
        - Battery positive = discharge, Battery negative = charge
        We derive Import/Export/Charge/Discharge from these raw values
        and convert W intervals to kWh (each 5-min = W * 5/60/1000).
        """
        now = self._now()
        date = now.strftime("%Y-%m-%d")

        data = await self.async_get_energy_day(plant_id, date)

        # Collect raw values by label
        raw: dict[str, list[float]] = {}
        for info in data.get("data", {}).get("infos", []):
            label = info.get("label", "")
            raw[label] = [float(r.get("value", 0)) for r in info.get("records", [])]

        interval_hours = 5 / 60  # 5 minutes in hours

        totals: dict[str, float] = {}

        # PV and Load map directly
        if "PV" in raw:
            totals["PV"] = round(sum(max(0, v) for v in raw["PV"]) * interval_hours / 1000, 1)
        if "Load" in raw:
            totals["Load"] = round(sum(max(0, v) for v in raw["Load"]) * interval_hours / 1000, 1)

        # Grid: positive = import, negative = export
        if "Grid" in raw:
            totals["Import"] = round(sum(max(0, v) for v in raw["Grid"]) * interval_hours / 1000, 1)
            totals["Export"] = round(sum(abs(min(0, v)) for v in raw["Grid"]) * interval_hours / 1000, 1)

        # Battery: positive = discharge, negative = charge
        if "Battery" in raw:
            totals["Discharge"] = round(sum(max(0, v) for v in raw["Battery"]) * interval_hours / 1000, 1)
            totals["Charge"] = round(sum(abs(min(0, v)) for v in raw["Battery"]) * interval_hours / 1000, 1)

        return totals

    async def async_get_realtime_power(self, plant_id: str) -> dict[str, float]:
        """Get the most recent power readings in watts from the day endpoint.

        Returns the last available 5-minute interval values:
        - pv_power: Solar panel output (W)
        - load_power: Home consumption (W)
        - grid_power: Grid power (positive=import, negative=export) (W)
        - battery_power: Battery power (positive=discharge, negative=charge) (W)
        - battery_soc: Battery state of charge (%)
        """
        now = self._now()
        date = now.strftime("%Y-%m-%d")
        data = await self.async_get_energy_day(plant_id, date)

        result: dict[str, float] = {}
        for info in data.get("data", {}).get("infos", []):
            label = info.get("label", "")
            records = info.get("records", [])
            if records:
                # Get the last non-zero record, or the very last record
                last_val = float(records[-1].get("value", 0))
                key_map = {
                    "PV": "pv_power",
                    "Load": "load_power",
                    "Grid": "grid_power",
                    "Battery": "battery_power",
                    "SOC": "battery_soc",
                }
                mapped = key_map.get(label)
                if mapped:
                    result[mapped] = last_val

        return result

    async def async_get_year_energy(self, plant_id: str, year: str) -> dict[str, dict[str, float]]:
        """Get full year energy data as {month: {label: value}}."""
        data = await self.async_get_energy_year(plant_id, year)
        result: dict[str, dict[str, float]] = {}
        for info in data.get("data", {}).get("infos", []):
            label = info.get("label", "")
            for record in info.get("records", []):
                month = record.get("time", "")
                if month not in result:
                    result[month] = {}
                result[month][label] = float(record.get("value", 0))
        return result
