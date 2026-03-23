"""Constants for the SolArk Cloud integration."""

DOMAIN = "solark_cloud"
CONF_PLANT_ID = "plant_id"
CONF_SCAN_INTERVAL_SECONDS = "scan_interval_seconds"
CONF_IMPORT_HISTORY = "import_history"
CONF_TIMEZONE = "timezone"

DEFAULT_SCAN_INTERVAL_SECONDS = 30
DEFAULT_IMPORT_HISTORY = True
DEFAULT_TIMEZONE = ""  # Empty = use HA's configured timezone

API_BASE_URL = "https://api.solarkcloud.com"
API_CLIENT_ID = "csp-web"
API_GRANT_TYPE = "password"

ENERGY_LABELS = ["Load", "PV", "Export", "Import", "Charge", "Discharge"]
