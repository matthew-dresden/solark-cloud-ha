"""Tests for SolArk Cloud constants."""

from custom_components.solark_cloud.const import (
    BATTERY_PROFILES,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    ENERGY_LABELS,
    INVERTER_PROFILES,
)


class TestConstants:
    def test_domain_is_set(self):
        assert DOMAIN == "solark_cloud"

    def test_energy_labels_complete(self):
        expected = {"Load", "PV", "Export", "Import", "Charge", "Discharge"}
        assert set(ENERGY_LABELS) == expected

    def test_inverter_profiles_have_required_keys(self):
        for name, specs in INVERTER_PROFILES.items():
            assert "max_output" in specs, f"{name} missing max_output"
            assert "max_grid_export" in specs, f"{name} missing max_grid_export"
            assert "max_pv_input" in specs, f"{name} missing max_pv_input"
            assert specs["max_output"] > 0
            assert specs["max_grid_export"] > 0

    def test_battery_profiles_have_required_keys(self):
        for name, specs in BATTERY_PROFILES.items():
            assert "kwh" in specs, f"{name} missing kwh"
            assert "max_power" in specs, f"{name} missing max_power"
            assert specs["kwh"] > 0
            assert specs["max_power"] > 0

    def test_default_scan_interval(self):
        assert DEFAULT_SCAN_INTERVAL_SECONDS == 60

    def test_solark_12k_grid_export(self):
        assert INVERTER_PROFILES["Sol-Ark 12K"]["max_grid_export"] == 9600

    def test_fortress_evault_max(self):
        assert BATTERY_PROFILES["Fortress eVault MAX 18.5"]["kwh"] == 18.5
        assert BATTERY_PROFILES["Fortress eVault MAX 18.5"]["max_power"] == 8640
