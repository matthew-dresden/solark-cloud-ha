# SolArk Cloud -- Home Assistant Integration

> **WARNING: This integration is currently in testing. Expect breaking changes until a stable release is published.**

Home Assistant custom integration for [Sol-Ark](https://sol-ark.com/) solar inverter systems. Pulls real-time power readings, daily/monthly/yearly energy totals, and battery state of charge from the SolarkCloud monitoring API. All 23 sensor entities are grouped under a single device and update on a configurable polling interval.

**By [Dresdencraft](https://github.com/matthew-dresden)** -- not affiliated with Sol-Ark.

## Features

- 23 sensor entities: 5 real-time power/battery sensors + 18 energy totals (6 metrics x 3 periods)
- HA Energy dashboard compatible (daily energy sensors use `total_increasing` state class)
- Custom Lovelace card with Day/Month/Year/Total tabs and date navigation
- `fetch_energy` service for on-demand API queries
- Configurable polling interval (10 seconds to 24 hours, default: 60 seconds)
- System spec configuration (inverter rating, panel count, battery capacity)
- Reconfigurable settings (change polling interval, system specs, timezone without re-adding)
- Timezone-aware data (uses HA timezone or a custom IANA timezone)
- Config flow UI with credential validation
- Diagnostics support (downloadable diagnostics with sensitive data redacted)
- Historical data import (up to 5 years of monthly data on first setup)
- HACS compatible

## Installation

### HACS (recommended)

1. Open HACS in your Home Assistant instance.
2. Click the three-dot menu and select **Custom repositories**.
3. Add `https://github.com/matthew-dresden/solark-cloud-ha` as an **Integration**.
4. Search for "SolArk Cloud" and install.
5. Restart Home Assistant.
6. Go to **Settings > Devices & Services > Add Integration > SolArk Cloud**.

### Manual

1. Download the `src/custom_components/solark_cloud` directory from this repository.
2. Copy it into your Home Assistant `config/custom_components/` directory.
3. Restart Home Assistant.
4. Go to **Settings > Devices & Services > Add Integration > SolArk Cloud**.

## Configuration

The config flow prompts for the following fields:

| Field | Key | Required | Default | Description |
|-------|-----|----------|---------|-------------|
| Email | `username` | Yes | -- | SolarkCloud account email |
| Password | `password` | Yes | -- | SolarkCloud account password |
| Plant ID | `plant_id` | Yes | -- | Plant ID from your SolarkCloud URL |
| Inverter Rating | `inverter_rating` | No | 12000 | Inverter continuous output (W), 1000--100000 |
| Inverter Count | `inverter_count` | No | 1 | Number of inverters, 1--20 |
| Panel Count | `panel_count` | No | 0 | Number of solar panels, 0--500 |
| Panel Watts | `panel_watts` | No | 400 | Wattage per panel, 100--1000 |
| Max PV Power | `max_pv_power` | No | 12000 | Maximum DC PV input (W), 1000--500000 |
| Battery Count | `battery_count` | No | 0 | Number of batteries, 0--50 |
| Battery kWh | `battery_kwh` | No | 18.5 | Usable capacity per battery (kWh), 0--200 |
| Battery Max Power | `battery_max_power` | No | 8640 | Max charge/discharge per battery (W), 0--100000 |
| Update Interval | `scan_interval_seconds` | No | 60 | Polling interval in seconds, 10--86400 |
| Timezone | `timezone` | No | HA timezone | IANA timezone (e.g. `America/Detroit`) |
| Import History | `import_history` | No | true | Pull historical data on first setup |

### Finding Your Plant ID

Your plant ID is in your SolarkCloud URL: `https://www.solarkcloud.com/plants/overview/{PLANT_ID}/...`

## Entities

All 23 sensors are registered under a single device named "SolArk Plant {PLANT_ID}".

### Real-Time Power Sensors (5)

| Entity Name | Entity ID Suffix | Unit | Device Class | Description |
|-------------|-----------------|------|--------------|-------------|
| Solar Power | `pv_power` | W | power | Current solar panel output |
| Home Power | `load_power` | W | power | Current home consumption |
| Grid Power | `grid_power` | W | power | Grid power (+import / -export) |
| Battery Power | `battery_power` | W | power | Battery power (+discharge / -charge) |
| Battery SOC | `battery_soc` | % | battery | Battery state of charge |

### Energy Totals -- Today (6)

| Entity Name | Entity ID Suffix | Unit | Description |
|-------------|-----------------|------|-------------|
| Solar Production Today | `pv_today` | kWh | Solar energy generated today |
| Home Consumption Today | `load_today` | kWh | Energy consumed today |
| Grid Export Today | `export_today` | kWh | Energy exported to grid today |
| Grid Import Today | `import_today` | kWh | Energy imported from grid today |
| Battery Charge Today | `charge_today` | kWh | Energy stored in batteries today |
| Battery Discharge Today | `discharge_today` | kWh | Energy released from batteries today |

### Energy Totals -- This Month (6)

| Entity Name | Entity ID Suffix | Unit | Description |
|-------------|-----------------|------|-------------|
| Solar Production This Month | `pv_month` | kWh | Solar energy generated this month |
| Home Consumption This Month | `load_month` | kWh | Energy consumed this month |
| Grid Export This Month | `export_month` | kWh | Energy exported to grid this month |
| Grid Import This Month | `import_month` | kWh | Energy imported from grid this month |
| Battery Charge This Month | `charge_month` | kWh | Energy stored in batteries this month |
| Battery Discharge This Month | `discharge_month` | kWh | Energy released from batteries this month |

### Energy Totals -- This Year (6)

| Entity Name | Entity ID Suffix | Unit | Description |
|-------------|-----------------|------|-------------|
| Solar Production This Year | `pv_year_totals` | kWh | Solar energy generated this year |
| Home Consumption This Year | `load_year_totals` | kWh | Energy consumed this year |
| Grid Export This Year | `export_year_totals` | kWh | Energy exported to grid this year |
| Grid Import This Year | `import_year_totals` | kWh | Energy imported from grid this year |
| Battery Charge This Year | `charge_year_totals` | kWh | Energy stored in batteries this year |
| Battery Discharge This Year | `discharge_year_totals` | kWh | Energy released from batteries this year |

## Services

### `solark_cloud.fetch_energy`

Fetches energy data from the SolarkCloud API for a specific period and date. Returns response data only (no state change).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `period` | select | Yes | `day`, `month`, `year`, or `total` |
| `date` | string | Yes | `YYYY-MM-DD` for day/month, `YYYY` for year, ignored for total |

**Example service call:**

```yaml
service: solark_cloud.fetch_energy
data:
  period: day
  date: "2025-07-15"
```

The response contains a `series` object keyed by metric label (PV, Load, Export, Import, Charge, Discharge), each with an array of `{time, value}` records.

## Reconfiguration

After initial setup, you can change system specifications and polling settings without removing and re-adding the integration. Go to **Settings > Devices & Services > SolArk Cloud > Configure**. Credentials and plant ID cannot be changed through reconfiguration.

## Diagnostics

Download diagnostics data from **Settings > Devices & Services > SolArk Cloud > three-dot menu > Download diagnostics**. Passwords are automatically redacted from the output.

## Future Enhancements

- **Auto-detection of system specs:** The SolArk Cloud API does not currently expose a documented plant info endpoint for querying inverter models, panel counts, or battery configurations. Auto-detection of system specifications will be added when such an endpoint becomes available.

## Data Freshness

The Sol-Ark inverter dongle reports data to SolarkCloud every **5 minutes**. This is the upstream data resolution -- no matter how frequently this integration polls, the underlying readings advance in 5-minute steps. The default 60-second polling interval ensures new data appears promptly after SolarkCloud receives it.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development environment setup, testing, and code style guidelines.

## License

[Apache License 2.0](LICENSE)
