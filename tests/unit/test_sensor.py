"""Tests for SolArk Cloud sensor entities."""

from unittest.mock import MagicMock

import pytest
from custom_components.solark_cloud.const import DOMAIN, ENERGY_LABELS
from custom_components.solark_cloud.sensor import (
    SolarkCloudEnergySensor,
    SolarkCloudRealtimeSensor,
    async_setup_entry,
)


@pytest.fixture
def mock_coordinator():
    coordinator = MagicMock()
    coordinator.plant_id = "999999"
    coordinator.data = {
        "today": {"PV": 33.7, "Load": 59.0, "Export": 6.0, "Import": 41.3, "Charge": 34.4, "Discharge": 26.8},
        "month": {"PV": 1904.8, "Load": 1703.3, "Export": 716.5, "Import": 711.3, "Charge": 657.4, "Discharge": 553.0},
        "year_totals": {
            "PV": 4650.0,
            "Load": 7595.0,
            "Export": 1602.2,
            "Import": 5154.1,
            "Charge": 1660.1,
            "Discharge": 1368.1,
        },
        "realtime": {
            "pv_power": 5000.0,
            "load_power": 2800.0,
            "grid_power": -700.0,
            "battery_power": 3500.0,
            "battery_soc": 78.0,
        },
    }
    return coordinator


class TestSolarkCloudEnergySensor:
    def test_today_sensor_value(self, mock_coordinator):
        sensor = SolarkCloudEnergySensor(
            coordinator=mock_coordinator,
            label="PV",
            period="today",
            name="Solar Production Today",
            icon="mdi:solar-power-variant",
        )
        assert sensor.native_value == 33.7

    def test_month_sensor_value(self, mock_coordinator):
        sensor = SolarkCloudEnergySensor(
            coordinator=mock_coordinator,
            label="PV",
            period="month",
            name="Solar Production This Month",
            icon="mdi:solar-power-variant",
        )
        assert sensor.native_value == 1904.8

    def test_year_sensor_value(self, mock_coordinator):
        sensor = SolarkCloudEnergySensor(
            coordinator=mock_coordinator,
            label="PV",
            period="year_totals",
            name="Solar Production This Year",
            icon="mdi:solar-power-variant",
        )
        assert sensor.native_value == 4650.0

    def test_returns_none_when_no_data(self, mock_coordinator):
        mock_coordinator.data = None
        sensor = SolarkCloudEnergySensor(
            coordinator=mock_coordinator, label="PV", period="today", name="Test", icon="mdi:flash"
        )
        assert sensor.native_value is None

    def test_returns_none_for_missing_label(self, mock_coordinator):
        sensor = SolarkCloudEnergySensor(
            coordinator=mock_coordinator, label="Nonexistent", period="today", name="Test", icon="mdi:flash"
        )
        assert sensor.native_value is None

    def test_unique_id(self, mock_coordinator):
        sensor = SolarkCloudEnergySensor(
            coordinator=mock_coordinator, label="PV", period="today", name="Test", icon="mdi:flash"
        )
        assert sensor.unique_id == "solark_999999_pv_today"

    def test_device_info(self, mock_coordinator):
        sensor = SolarkCloudEnergySensor(
            coordinator=mock_coordinator, label="PV", period="today", name="Test", icon="mdi:flash"
        )
        assert (DOMAIN, "999999") in sensor.device_info["identifiers"]
        assert sensor.device_info["manufacturer"] == "Dresdencraft"

    @pytest.mark.parametrize(
        "label,period,expected",
        [
            pytest.param("Load", "today", 59.0, id="load-today"),
            pytest.param("Export", "month", 716.5, id="export-month"),
            pytest.param("Import", "year_totals", 5154.1, id="import-year"),
            pytest.param("Charge", "today", 34.4, id="charge-today"),
            pytest.param("Discharge", "month", 553.0, id="discharge-month"),
        ],
    )
    def test_all_labels_and_periods(self, mock_coordinator, label, period, expected):
        sensor = SolarkCloudEnergySensor(
            coordinator=mock_coordinator, label=label, period=period, name="Test", icon="mdi:flash"
        )
        assert sensor.native_value == expected


class TestSolarkCloudRealtimeSensor:
    def test_realtime_pv_power(self, mock_coordinator):
        sensor = SolarkCloudRealtimeSensor(
            coordinator=mock_coordinator,
            key="pv_power",
            name="Solar Power",
            icon="mdi:solar-power-variant",
            device_class=None,
            unit="W",
        )
        assert sensor.native_value == 5000.0

    def test_realtime_battery_soc(self, mock_coordinator):
        sensor = SolarkCloudRealtimeSensor(
            coordinator=mock_coordinator,
            key="battery_soc",
            name="Battery SOC",
            icon="mdi:battery",
            device_class=None,
            unit="%",
        )
        assert sensor.native_value == 78.0

    def test_realtime_grid_negative(self, mock_coordinator):
        sensor = SolarkCloudRealtimeSensor(
            coordinator=mock_coordinator,
            key="grid_power",
            name="Grid Power",
            icon="mdi:transmission-tower",
            device_class=None,
            unit="W",
        )
        assert sensor.native_value == -700.0

    def test_returns_none_when_no_data(self, mock_coordinator):
        mock_coordinator.data = None
        sensor = SolarkCloudRealtimeSensor(
            coordinator=mock_coordinator,
            key="pv_power",
            name="Test",
            icon="mdi:flash",
            device_class=None,
            unit="W",
        )
        assert sensor.native_value is None

    def test_unique_id(self, mock_coordinator):
        sensor = SolarkCloudRealtimeSensor(
            coordinator=mock_coordinator,
            key="pv_power",
            name="Test",
            icon="mdi:flash",
            device_class=None,
            unit="W",
        )
        assert sensor.unique_id == "solark_999999_pv_power"

    @pytest.mark.parametrize(
        "key,expected",
        [
            pytest.param("pv_power", 5000.0, id="pv"),
            pytest.param("load_power", 2800.0, id="load"),
            pytest.param("grid_power", -700.0, id="grid"),
            pytest.param("battery_power", 3500.0, id="battery"),
            pytest.param("battery_soc", 78.0, id="soc"),
        ],
    )
    def test_all_realtime_keys(self, mock_coordinator, key, expected):
        sensor = SolarkCloudRealtimeSensor(
            coordinator=mock_coordinator,
            key=key,
            name="Test",
            icon="mdi:flash",
            device_class=None,
            unit="W",
        )
        assert sensor.native_value == expected


class TestAsyncSetupEntry:
    async def test_creates_expected_number_of_entities(self, mock_coordinator):
        """async_setup_entry should create 18 energy sensors (6 labels x 3 periods) + 5 realtime = 23."""
        hass = MagicMock()
        hass.data = {DOMAIN: {"test_entry": mock_coordinator}}

        entry = MagicMock()
        entry.entry_id = "test_entry"

        added_entities: list = []

        await async_setup_entry(hass, entry, added_entities.extend)

        expected_energy = len(ENERGY_LABELS) * 3
        expected_realtime = 5
        assert len(added_entities) == expected_energy + expected_realtime

        energy_sensors = [e for e in added_entities if isinstance(e, SolarkCloudEnergySensor)]
        realtime_sensors = [e for e in added_entities if isinstance(e, SolarkCloudRealtimeSensor)]
        assert len(energy_sensors) == expected_energy
        assert len(realtime_sensors) == expected_realtime

    async def test_all_unique_ids_are_unique(self, mock_coordinator):
        hass = MagicMock()
        hass.data = {DOMAIN: {"test_entry": mock_coordinator}}
        entry = MagicMock()
        entry.entry_id = "test_entry"

        added: list = []
        await async_setup_entry(hass, entry, added.extend)

        unique_ids = [e.unique_id for e in added]
        assert len(unique_ids) == len(set(unique_ids)), "Duplicate unique_ids found"
