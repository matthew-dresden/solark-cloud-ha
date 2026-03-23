"""Tests for the fetch_energy service handler."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from homeassistant.core import HomeAssistant

from custom_components.solark_cloud import async_handle_fetch_energy
from custom_components.solark_cloud.const import DOMAIN
from custom_components.solark_cloud.coordinator import SolarkCloudCoordinator


def _mock_coordinator(plant_id: str = "999999") -> MagicMock:
    coord = MagicMock(spec=SolarkCloudCoordinator)
    coord.plant_id = plant_id
    coord.client = AsyncMock()
    coord.client._now = MagicMock(return_value=datetime(2025, 7, 15, tzinfo=UTC))
    return coord


def _mock_call(period: str, date: str) -> MagicMock:
    call = MagicMock()
    call.data = {"period": period, "date": date}
    return call


class TestFetchEnergyService:
    async def test_fetch_day(self, hass: HomeAssistant):
        coord = _mock_coordinator()
        coord.client.async_get_energy_day.return_value = {
            "data": {"infos": [{"label": "PV", "records": [{"time": "00:00", "value": "100"}]}]}
        }
        hass.data[DOMAIN] = {"entry1": coord}

        result = await async_handle_fetch_energy(hass, _mock_call("day", "2025-07-15"))

        assert result["period"] == "day"
        assert result["plant_id"] == "999999"
        assert "PV" in result["series"]
        assert result["series"]["PV"][0]["value"] == 100.0

    async def test_fetch_month(self, hass: HomeAssistant):
        coord = _mock_coordinator()
        coord.client.async_get_energy_month.return_value = {
            "data": {"infos": [{"label": "Load", "records": [{"time": "2025-07-01", "value": "250"}]}]}
        }
        hass.data[DOMAIN] = {"entry1": coord}

        result = await async_handle_fetch_energy(hass, _mock_call("month", "2025-07"))

        assert result["period"] == "month"
        assert "Load" in result["series"]

    async def test_fetch_year(self, hass: HomeAssistant):
        coord = _mock_coordinator()
        coord.client.async_get_energy_year.return_value = {
            "data": {
                "infos": [
                    {
                        "label": "PV",
                        "records": [{"time": "2025-01", "value": "1000"}, {"time": "2025-02", "value": "1500"}],
                    },
                ]
            }
        }
        hass.data[DOMAIN] = {"entry1": coord}

        result = await async_handle_fetch_energy(hass, _mock_call("year", "2025"))

        assert result["period"] == "year"
        assert "PV" in result["series"]
        assert len(result["series"]["PV"]) == 2

    async def test_fetch_total(self, hass: HomeAssistant):
        coord = _mock_coordinator()
        coord.client.async_get_year_energy.return_value = {
            "2025-01": {"PV": 1000.0, "Load": 2000.0},
            "2025-02": {"PV": 1500.0, "Load": 2500.0},
        }
        hass.data[DOMAIN] = {"entry1": coord}

        result = await async_handle_fetch_energy(hass, _mock_call("total", "all"))

        assert result["period"] == "total"
        assert "PV" in result["series"]
        assert "Load" in result["series"]

    async def test_fetch_total_sums_year(self, hass: HomeAssistant):
        coord = _mock_coordinator()
        coord.client.async_get_year_energy.return_value = {
            "2025-01": {"PV": 1000.0},
            "2025-02": {"PV": 1500.0},
        }
        hass.data[DOMAIN] = {"entry1": coord}

        result = await async_handle_fetch_energy(hass, _mock_call("total", "all"))

        pv_entries = result["series"]["PV"]
        assert len(pv_entries) >= 1
        # Each year entry should sum to 2500 (1000+1500), and there are multiple years
        for entry in pv_entries:
            assert entry["value"] == 2500.0

    async def test_fetch_no_coordinator(self, hass: HomeAssistant):
        hass.data[DOMAIN] = {}
        result = await async_handle_fetch_energy(hass, _mock_call("day", "2025-01-01"))
        assert "error" in result

    async def test_fetch_unknown_period(self, hass: HomeAssistant):
        coord = _mock_coordinator()
        hass.data[DOMAIN] = {"entry1": coord}

        result = await async_handle_fetch_energy(hass, _mock_call("unknown_period", "2025"))

        assert "error" in result

    async def test_fetch_no_domain_data(self, hass: HomeAssistant):
        # DOMAIN not in hass.data at all
        result = await async_handle_fetch_energy(hass, _mock_call("day", "2025-01-01"))
        assert "error" in result

    async def test_fetch_total_handles_api_error(self, hass: HomeAssistant):
        coord = _mock_coordinator()
        coord.client.async_get_year_energy.side_effect = Exception("API down")
        hass.data[DOMAIN] = {"entry1": coord}

        result = await async_handle_fetch_energy(hass, _mock_call("total", "all"))

        # Should return empty series, not crash
        assert result["period"] == "total"
        assert isinstance(result["series"], dict)
