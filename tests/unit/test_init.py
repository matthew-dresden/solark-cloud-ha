"""Tests for SolArk Cloud integration setup."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.solark_cloud import async_setup_entry, async_unload_entry
from custom_components.solark_cloud.const import DOMAIN


@pytest.fixture
def mock_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "username": "test@example.com",
        "password": "test-pass",
        "plant_id": "999999",
        "scan_interval_seconds": 60,
        "timezone": "America/Detroit",
        "import_history": False,
    }
    entry.options = {}
    return entry


class TestIntegrationSetup:
    async def test_setup_entry(self, hass: HomeAssistant, mock_entry):
        with (
            patch("custom_components.solark_cloud.SolarkCloudApiClient") as mock_client_cls,
            patch("custom_components.solark_cloud.SolarkCloudCoordinator") as mock_coord_cls,
        ):
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client

            mock_coord = AsyncMock()
            mock_coord.client = mock_client
            mock_coord_cls.return_value = mock_coord

            with patch.object(hass.config_entries, "async_forward_entry_setups", new_callable=AsyncMock):
                result = await async_setup_entry(hass, mock_entry)

            assert result is True
            assert DOMAIN in hass.data
            assert mock_entry.entry_id in hass.data[DOMAIN]

    async def test_unload_entry(self, hass: HomeAssistant, mock_entry):
        mock_coord = AsyncMock()
        mock_coord.client = AsyncMock()
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][mock_entry.entry_id] = mock_coord

        with patch.object(hass.config_entries, "async_unload_platforms", new_callable=AsyncMock, return_value=True):
            result = await async_unload_entry(hass, mock_entry)

        assert result is True
        assert mock_entry.entry_id not in hass.data[DOMAIN]
        mock_coord.client.async_close.assert_called_once()
