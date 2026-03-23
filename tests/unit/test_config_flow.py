"""Tests for the SolArk Cloud config flow."""

from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.loader import DATA_CUSTOM_COMPONENTS

from custom_components.solark_cloud.const import (
    CONF_BATTERY_COUNT,
    CONF_BATTERY_KWH,
    CONF_BATTERY_MAX_POWER,
    CONF_IMPORT_HISTORY,
    CONF_INVERTER_COUNT,
    CONF_INVERTER_RATING,
    CONF_MAX_PV_POWER,
    CONF_PANEL_COUNT,
    CONF_PANEL_WATTS,
    CONF_PLANT_ID,
    CONF_SCAN_INTERVAL_SECONDS,
    CONF_TIMEZONE,
    DOMAIN,
)


def _make_user_input(plant_id="999999"):
    return {
        CONF_USERNAME: "test@example.com",
        CONF_PASSWORD: "test-pass",
        CONF_PLANT_ID: plant_id,
        CONF_INVERTER_RATING: 12000,
        CONF_INVERTER_COUNT: 1,
        CONF_PANEL_COUNT: 10,
        CONF_PANEL_WATTS: 400,
        CONF_MAX_PV_POWER: 4000,
        CONF_BATTERY_COUNT: 1,
        CONF_BATTERY_KWH: 18.5,
        CONF_BATTERY_MAX_POWER: 8640,
        CONF_SCAN_INTERVAL_SECONDS: 60,
        CONF_TIMEZONE: "",
        CONF_IMPORT_HISTORY: False,
    }


async def _register_integration(hass: HomeAssistant) -> None:
    """Register the solark_cloud integration with the HA loader cache."""
    from homeassistant.loader import Integration, _get_custom_components

    custom = await hass.async_add_executor_job(_get_custom_components, hass)
    if DOMAIN not in custom:
        # Fallback: build manually from the manifest
        from pathlib import Path

        import custom_components.solark_cloud as mod

        integration = Integration(
            hass,
            f"custom_components.{DOMAIN}",
            Path(mod.__file__).parent,
            mod.manifest
            if hasattr(mod, "manifest")
            else {
                "domain": DOMAIN,
                "name": "SolArk Cloud by Dresdencraft",
                "config_flow": True,
                "documentation": "",
                "requirements": [],
                "version": "0.5.0",
            },
        )
        custom[DOMAIN] = integration
    hass.data[DATA_CUSTOM_COMPONENTS] = custom


class TestSolarkCloudConfigFlow:
    async def test_form_shown_on_init(self, hass: HomeAssistant):
        await _register_integration(hass)
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

    async def test_create_entry_on_success(self, hass: HomeAssistant):
        await _register_integration(hass)
        with patch("custom_components.solark_cloud.config_flow.SolarkCloudApiClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client

            result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input=_make_user_input(),
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["title"] == "SolArk Plant 999999"
            assert result["data"][CONF_PLANT_ID] == "999999"

    async def test_error_on_invalid_auth(self, hass: HomeAssistant):
        await _register_integration(hass)
        with patch("custom_components.solark_cloud.config_flow.SolarkCloudApiClient") as mock_client_cls:
            from custom_components.solark_cloud.api_client import SolarkCloudAuthError

            mock_client = AsyncMock()
            mock_client.async_authenticate.side_effect = SolarkCloudAuthError("bad creds")
            mock_client_cls.return_value = mock_client

            result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input=_make_user_input(),
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "invalid_auth"}

    async def test_error_on_connection_failure(self, hass: HomeAssistant):
        await _register_integration(hass)
        with patch("custom_components.solark_cloud.config_flow.SolarkCloudApiClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.async_authenticate.side_effect = Exception("network error")
            mock_client_cls.return_value = mock_client

            result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input=_make_user_input(),
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "cannot_connect"}

    async def test_duplicate_plant_aborts(self, hass: HomeAssistant):
        await _register_integration(hass)
        with patch("custom_components.solark_cloud.config_flow.SolarkCloudApiClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client

            # First entry
            result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
            await hass.config_entries.flow.async_configure(result["flow_id"], user_input=_make_user_input("111111"))

            # Second entry same plant
            result2 = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
            result2 = await hass.config_entries.flow.async_configure(
                result2["flow_id"], user_input=_make_user_input("111111")
            )
            assert result2["type"] == FlowResultType.ABORT
            assert result2["reason"] == "already_configured"
