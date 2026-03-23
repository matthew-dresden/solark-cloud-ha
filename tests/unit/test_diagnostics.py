"""Tests for SolArk Cloud diagnostics support."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from custom_components.solark_cloud.const import CONF_PLANT_ID, DOMAIN
from custom_components.solark_cloud.diagnostics import (
    REDACTED,
    async_get_config_entry_diagnostics,
)


@pytest.fixture
def mock_coordinator():
    coordinator = MagicMock()
    coordinator.plant_id = "999999"
    coordinator.data = {
        "today": {"PV": 33.7, "Load": 59.0},
        "realtime": {"pv_power": 5000.0},
    }
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {
        CONF_USERNAME: "test@example.com",
        CONF_PASSWORD: "secret-password",
        CONF_PLANT_ID: "999999",
    }
    return entry


@pytest.fixture
def mock_hass(mock_coordinator):
    hass = MagicMock()
    hass.data = {DOMAIN: {"test_entry": mock_coordinator}}
    return hass


class TestDiagnostics:
    async def test_password_is_redacted(self, mock_hass, mock_entry):
        result = await async_get_config_entry_diagnostics(mock_hass, mock_entry)
        assert result["config_entry"][CONF_PASSWORD] == REDACTED

    async def test_username_is_preserved(self, mock_hass, mock_entry):
        result = await async_get_config_entry_diagnostics(mock_hass, mock_entry)
        assert result["config_entry"][CONF_USERNAME] == "test@example.com"

    async def test_plant_id_returned(self, mock_hass, mock_entry):
        result = await async_get_config_entry_diagnostics(mock_hass, mock_entry)
        assert result["plant_id"] == "999999"

    async def test_coordinator_data_included(self, mock_hass, mock_entry):
        result = await async_get_config_entry_diagnostics(mock_hass, mock_entry)
        assert "today" in result["coordinator_data"]
        assert result["coordinator_data"]["today"]["PV"] == 33.7

    async def test_last_update_success_included(self, mock_hass, mock_entry):
        result = await async_get_config_entry_diagnostics(mock_hass, mock_entry)
        assert result["last_update_success"] is True

    async def test_empty_coordinator_data(self, mock_hass, mock_entry, mock_coordinator):
        mock_coordinator.data = None
        result = await async_get_config_entry_diagnostics(mock_hass, mock_entry)
        assert result["coordinator_data"] == {}

    async def test_original_entry_data_not_mutated(self, mock_hass, mock_entry):
        original_password = mock_entry.data[CONF_PASSWORD]
        await async_get_config_entry_diagnostics(mock_hass, mock_entry)
        assert mock_entry.data[CONF_PASSWORD] == original_password
