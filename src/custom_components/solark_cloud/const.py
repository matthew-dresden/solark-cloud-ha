"""Constants for the SolArk Cloud integration."""

DOMAIN = "solark_cloud"
CONF_PLANT_ID = "plant_id"
CONF_SCAN_INTERVAL_SECONDS = "scan_interval_seconds"
CONF_IMPORT_HISTORY = "import_history"
CONF_TIMEZONE = "timezone"

# System spec configs
CONF_INVERTER_COUNT = "inverter_count"
CONF_INVERTER_RATING = "inverter_rating"
CONF_MAX_PV_POWER = "max_pv_power"
CONF_PANEL_COUNT = "panel_count"
CONF_PANEL_WATTS = "panel_watts"
CONF_BATTERY_COUNT = "battery_count"
CONF_BATTERY_KWH = "battery_kwh"
CONF_BATTERY_MAX_POWER = "battery_max_power"

# Defaults
DEFAULT_SCAN_INTERVAL_SECONDS = 60
DEFAULT_IMPORT_HISTORY = True
DEFAULT_TIMEZONE = ""
DEFAULT_INVERTER_COUNT = 1
DEFAULT_INVERTER_RATING = 12000
DEFAULT_MAX_PV_POWER = 12000
DEFAULT_PANEL_COUNT = 0
DEFAULT_PANEL_WATTS = 400
DEFAULT_BATTERY_COUNT = 0
DEFAULT_BATTERY_KWH = 18.5
DEFAULT_BATTERY_MAX_POWER = 8640  # eVault MAX 18.5: 180A * 48V = 8640W per battery

API_BASE_URL = "https://api.solarkcloud.com"
API_CLIENT_ID = "csp-web"
API_GRANT_TYPE = "password"

ENERGY_LABELS = ["Load", "PV", "Export", "Import", "Charge", "Discharge"]

# Sol-Ark inverter profiles: model -> specs
# Sources: Official Sol-Ark datasheets and user manuals
# max_output: continuous AC output power (W)
# max_grid_export: maximum grid sell/export power per inverter (W)
# max_pv_input: maximum DC PV input power (W)
INVERTER_PROFILES = {
    "Sol-Ark 8K": {"max_output": 8000, "max_grid_export": 8000, "max_pv_input": 13000},
    "Sol-Ark 12K": {"max_output": 12000, "max_grid_export": 9600, "max_pv_input": 16500},
    "Sol-Ark 15K": {"max_output": 15000, "max_grid_export": 15000, "max_pv_input": 19500},
    "Sol-Ark 18K": {"max_output": 18000, "max_grid_export": 18000, "max_pv_input": 28800},
}

# Battery profiles: model -> specs
# Sources: Manufacturer datasheets
# kwh: usable energy capacity
# max_power: max continuous charge/discharge power (W)
BATTERY_PROFILES = {
    "Fortress eVault MAX 18.5": {"kwh": 18.5, "max_power": 8640},  # 180A x 48V
    "Fortress eVault 18.5": {"kwh": 18.5, "max_power": 7200},  # 150A x 48V
}
