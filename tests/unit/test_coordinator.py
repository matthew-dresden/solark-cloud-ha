"""Tests for the SolArk Cloud data coordinator."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from custom_components.solark_cloud.api_client import SolarkCloudApiError
from custom_components.solark_cloud.const import CONF_IMPORT_HISTORY, CONF_SCAN_INTERVAL_SECONDS
from custom_components.solark_cloud.coordinator import SolarkCloudCoordinator


@pytest.fixture
def mock_client():
    client = AsyncMock()
    client.async_get_today_energy.return_value = {"PV": 33.7, "Load": 59.0}
    client.async_get_current_month_energy.return_value = {"PV": 1900.0, "Load": 1700.0}
    client.async_get_current_year_energy.return_value = {"PV": 4600.0, "Load": 7500.0}
    client.async_get_realtime_power.return_value = {"pv_power": 5000.0, "battery_soc": 78.0}
    # _now is a sync method — use MagicMock, not AsyncMock
    client._now = MagicMock(return_value=datetime(2026, 3, 23, 12, 0, 0, tzinfo=timezone.utc))
    client.async_get_year_energy.return_value = {
        "2026-01": {"PV": 400.0, "Load": 2800.0},
        "2026-02": {"PV": 2300.0, "Load": 2500.0},
    }
    return client


@pytest.fixture
def mock_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {
        CONF_SCAN_INTERVAL_SECONDS: 60,
        CONF_IMPORT_HISTORY: False,
    }
    entry.options = {}
    return entry


@pytest.fixture
def coordinator(hass, mock_client, mock_entry):
    return SolarkCloudCoordinator(
        hass=hass,
        client=mock_client,
        plant_id="999999",
        entry=mock_entry,
    )


class TestSolarkCloudCoordinator:
    async def test_update_data_returns_all_keys(self, coordinator, mock_client):
        data = await coordinator._async_update_data()
        assert "today" in data
        assert "month" in data
        assert "year_totals" in data
        assert "realtime" in data
        assert "plant_id" in data
        assert "last_updated" in data
        assert data["plant_id"] == "999999"

    async def test_update_data_calls_all_endpoints(self, coordinator, mock_client):
        await coordinator._async_update_data()
        mock_client.async_get_today_energy.assert_called_once_with("999999")
        mock_client.async_get_current_month_energy.assert_called_once_with("999999")
        mock_client.async_get_current_year_energy.assert_called_once_with("999999")
        mock_client.async_get_realtime_power.assert_called_once_with("999999")

    async def test_update_raises_update_failed_on_api_error(self, coordinator, mock_client):
        from homeassistant.helpers.update_coordinator import UpdateFailed

        mock_client.async_get_today_energy.side_effect = SolarkCloudApiError("fail")
        with pytest.raises(UpdateFailed, match="Error fetching SolArk Cloud data"):
            await coordinator._async_update_data()

    async def test_history_not_imported_when_disabled(self, coordinator, mock_client, mock_entry):
        mock_entry.data[CONF_IMPORT_HISTORY] = False
        await coordinator._async_update_data()
        mock_client.async_get_year_energy.assert_not_called()
        assert coordinator._history_imported is True

    async def test_history_imported_when_enabled(self, hass, mock_client, mock_entry):
        mock_entry.data[CONF_IMPORT_HISTORY] = True
        coord = SolarkCloudCoordinator(hass=hass, client=mock_client, plant_id="999999", entry=mock_entry)

        with patch("custom_components.solark_cloud.coordinator.async_add_external_statistics"):
            await coord._async_update_data()

        assert coord._history_imported is True
        # Should have called async_get_year_energy for each year (up to 5)
        assert mock_client.async_get_year_energy.call_count >= 1

    async def test_history_only_imported_once(self, hass, mock_client, mock_entry):
        mock_entry.data[CONF_IMPORT_HISTORY] = True
        coord = SolarkCloudCoordinator(hass=hass, client=mock_client, plant_id="999999", entry=mock_entry)

        with patch("custom_components.solark_cloud.coordinator.async_add_external_statistics"):
            await coord._async_update_data()
            first_count = mock_client.async_get_year_energy.call_count
            await coord._async_update_data()
            # Second call should NOT re-import history
            assert mock_client.async_get_year_energy.call_count == first_count

    async def test_history_import_handles_api_error(self, hass, mock_client, mock_entry):
        mock_entry.data[CONF_IMPORT_HISTORY] = True
        mock_client.async_get_year_energy.side_effect = SolarkCloudApiError("no data")
        coord = SolarkCloudCoordinator(hass=hass, client=mock_client, plant_id="999999", entry=mock_entry)

        # Should not raise — API errors during history import are logged, not fatal
        await coord._async_update_data()
        assert coord._history_imported is True

    async def test_import_year_statistics(self, hass, mock_client, mock_entry):
        mock_entry.data[CONF_IMPORT_HISTORY] = False
        coord = SolarkCloudCoordinator(hass=hass, client=mock_client, plant_id="999999", entry=mock_entry)

        year_data = {
            "2025-01": {
                "PV": 1400.0,
                "Load": 2800.0,
                "Export": 2200.0,
                "Import": 1900.0,
                "Charge": 570.0,
                "Discharge": 470.0,
            },
            "2025-02": {
                "PV": 1500.0,
                "Load": 2700.0,
                "Export": 460.0,
                "Import": 1840.0,
                "Charge": 590.0,
                "Discharge": 490.0,
            },
        }

        with patch("custom_components.solark_cloud.coordinator.async_add_external_statistics") as mock_import:
            coord._import_year_statistics("2025", year_data)
            # Called once per label (6 labels)
            assert mock_import.call_count == 6

    def test_scan_interval_from_entry(self, hass, mock_client, mock_entry):
        mock_entry.data[CONF_SCAN_INTERVAL_SECONDS] = 120
        coord = SolarkCloudCoordinator(hass=hass, client=mock_client, plant_id="999999", entry=mock_entry)
        assert coord.update_interval.total_seconds() == 120

    def test_scan_interval_from_options(self, hass, mock_client, mock_entry):
        mock_entry.options = {CONF_SCAN_INTERVAL_SECONDS: 30}
        coord = SolarkCloudCoordinator(hass=hass, client=mock_client, plant_id="999999", entry=mock_entry)
        assert coord.update_interval.total_seconds() == 30
