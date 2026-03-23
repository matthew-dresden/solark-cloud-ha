"""Config flow for SolArk Cloud integration."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .api_client import SolarkCloudApiClient, SolarkCloudAuthError
from .const import (
    CONF_IMPORT_HISTORY,
    CONF_PLANT_ID,
    CONF_SCAN_INTERVAL_SECONDS,
    CONF_TIMEZONE,
    DEFAULT_IMPORT_HISTORY,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DEFAULT_TIMEZONE,
    DOMAIN,
)

logger = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_PLANT_ID): str,
        vol.Optional(CONF_SCAN_INTERVAL_SECONDS, default=DEFAULT_SCAN_INTERVAL_SECONDS): vol.All(
            int, vol.Range(min=10, max=86400)
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
            # Validate credentials by attempting authentication
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
                # Prevent duplicate entries for the same plant
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
