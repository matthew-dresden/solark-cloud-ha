"""Config flow for SolArk Cloud integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .api_client import SolarkCloudApiClient, SolarkCloudAuthError
from .const import (
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
    DEFAULT_BATTERY_COUNT,
    DEFAULT_BATTERY_KWH,
    DEFAULT_BATTERY_MAX_POWER,
    DEFAULT_IMPORT_HISTORY,
    DEFAULT_INVERTER_COUNT,
    DEFAULT_INVERTER_RATING,
    DEFAULT_MAX_PV_POWER,
    DEFAULT_PANEL_COUNT,
    DEFAULT_PANEL_WATTS,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DEFAULT_TIMEZONE,
    DOMAIN,
    MAX_BATTERY_COUNT,
    MAX_BATTERY_KWH,
    MAX_BATTERY_POWER_WATTS,
    MAX_INVERTER_COUNT,
    MAX_INVERTER_RATING_WATTS,
    MAX_PANEL_COUNT,
    MAX_PANEL_WATTS,
    MAX_PV_POWER_WATTS,
    MAX_SCAN_INTERVAL_SECONDS,
    MIN_INVERTER_RATING_WATTS,
    MIN_PANEL_WATTS,
    MIN_PV_POWER_WATTS,
    MIN_SCAN_INTERVAL_SECONDS,
)

logger = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_PLANT_ID): str,
        vol.Optional(CONF_INVERTER_RATING, default=DEFAULT_INVERTER_RATING): vol.All(
            int, vol.Range(min=MIN_INVERTER_RATING_WATTS, max=MAX_INVERTER_RATING_WATTS)
        ),
        vol.Optional(CONF_INVERTER_COUNT, default=DEFAULT_INVERTER_COUNT): vol.All(
            int, vol.Range(min=1, max=MAX_INVERTER_COUNT)
        ),
        vol.Optional(CONF_PANEL_COUNT, default=DEFAULT_PANEL_COUNT): vol.All(
            int, vol.Range(min=0, max=MAX_PANEL_COUNT)
        ),
        vol.Optional(CONF_PANEL_WATTS, default=DEFAULT_PANEL_WATTS): vol.All(
            int, vol.Range(min=MIN_PANEL_WATTS, max=MAX_PANEL_WATTS)
        ),
        vol.Optional(CONF_MAX_PV_POWER, default=DEFAULT_MAX_PV_POWER): vol.All(
            int, vol.Range(min=MIN_PV_POWER_WATTS, max=MAX_PV_POWER_WATTS)
        ),
        vol.Optional(CONF_BATTERY_COUNT, default=DEFAULT_BATTERY_COUNT): vol.All(
            int, vol.Range(min=0, max=MAX_BATTERY_COUNT)
        ),
        vol.Optional(CONF_BATTERY_KWH, default=DEFAULT_BATTERY_KWH): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=MAX_BATTERY_KWH)
        ),
        vol.Optional(CONF_BATTERY_MAX_POWER, default=DEFAULT_BATTERY_MAX_POWER): vol.All(
            int, vol.Range(min=0, max=MAX_BATTERY_POWER_WATTS)
        ),
        vol.Optional(CONF_SCAN_INTERVAL_SECONDS, default=DEFAULT_SCAN_INTERVAL_SECONDS): vol.All(
            int, vol.Range(min=MIN_SCAN_INTERVAL_SECONDS, max=MAX_SCAN_INTERVAL_SECONDS)
        ),
        vol.Optional(CONF_TIMEZONE, default=DEFAULT_TIMEZONE): str,
        vol.Optional(CONF_IMPORT_HISTORY, default=DEFAULT_IMPORT_HISTORY): bool,
    }
)


class SolarkCloudConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SolArk Cloud."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            client = SolarkCloudApiClient(
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
            )
            try:
                await client.async_authenticate()
                await client.async_close()
            except SolarkCloudAuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                logger.exception("Unexpected error during authentication")
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(user_input[CONF_PLANT_ID])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"SolArk Plant {user_input[CONF_PLANT_ID]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        if user_input is not None:
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(),
                data_updates=user_input,
            )

        entry = self._get_reconfigure_entry()
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL_SECONDS,
                    default=entry.data.get(CONF_SCAN_INTERVAL_SECONDS, DEFAULT_SCAN_INTERVAL_SECONDS),
                ): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL_SECONDS, max=MAX_SCAN_INTERVAL_SECONDS)),
                vol.Optional(
                    CONF_TIMEZONE,
                    default=entry.data.get(CONF_TIMEZONE, DEFAULT_TIMEZONE),
                ): str,
                vol.Optional(
                    CONF_INVERTER_RATING,
                    default=entry.data.get(CONF_INVERTER_RATING, DEFAULT_INVERTER_RATING),
                ): vol.All(int, vol.Range(min=MIN_INVERTER_RATING_WATTS, max=MAX_INVERTER_RATING_WATTS)),
                vol.Optional(
                    CONF_INVERTER_COUNT,
                    default=entry.data.get(CONF_INVERTER_COUNT, DEFAULT_INVERTER_COUNT),
                ): vol.All(int, vol.Range(min=1, max=MAX_INVERTER_COUNT)),
                vol.Optional(
                    CONF_PANEL_COUNT,
                    default=entry.data.get(CONF_PANEL_COUNT, DEFAULT_PANEL_COUNT),
                ): vol.All(int, vol.Range(min=0, max=MAX_PANEL_COUNT)),
                vol.Optional(
                    CONF_PANEL_WATTS,
                    default=entry.data.get(CONF_PANEL_WATTS, DEFAULT_PANEL_WATTS),
                ): vol.All(int, vol.Range(min=MIN_PANEL_WATTS, max=MAX_PANEL_WATTS)),
                vol.Optional(
                    CONF_MAX_PV_POWER,
                    default=entry.data.get(CONF_MAX_PV_POWER, DEFAULT_MAX_PV_POWER),
                ): vol.All(int, vol.Range(min=MIN_PV_POWER_WATTS, max=MAX_PV_POWER_WATTS)),
                vol.Optional(
                    CONF_BATTERY_COUNT,
                    default=entry.data.get(CONF_BATTERY_COUNT, DEFAULT_BATTERY_COUNT),
                ): vol.All(int, vol.Range(min=0, max=MAX_BATTERY_COUNT)),
                vol.Optional(
                    CONF_BATTERY_KWH,
                    default=entry.data.get(CONF_BATTERY_KWH, DEFAULT_BATTERY_KWH),
                ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=MAX_BATTERY_KWH)),
                vol.Optional(
                    CONF_BATTERY_MAX_POWER,
                    default=entry.data.get(CONF_BATTERY_MAX_POWER, DEFAULT_BATTERY_MAX_POWER),
                ): vol.All(int, vol.Range(min=0, max=MAX_BATTERY_POWER_WATTS)),
            }
        )
        return self.async_show_form(step_id="reconfigure", data_schema=schema)
