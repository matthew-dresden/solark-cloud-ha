# SolArk Cloud — Home Assistant Integration

> **⚠️ WARNING: This integration is currently in testing. Expect changes until a stable release is published.**

Home Assistant custom integration for [Sol-Ark](https://sol-ark.com/) solar inverter systems. Pulls real-time and historical energy data from the SolarkCloud monitoring API.

**By [Dresdencraft](https://github.com/matthew-dresden)** — not affiliated with Sol-Ark.

## Features

- **Real-time power monitoring** — Solar, Load, Grid, Battery power (watts) updated every 30 seconds
- **Battery state of charge** — Current battery percentage
- **Daily energy totals** — kWh for all metrics (today)
- **Monthly energy totals** — kWh for all metrics (current month)
- **Configurable polling** — 10 seconds to 24 hours (default: 30 seconds)
- **Timezone aware** — Uses your Home Assistant timezone or a custom IANA timezone
- **Config flow** — UI-based setup with credential validation
- **17 sensor entities** grouped under a single device

## Sensors

### Real-Time Power (updated every 30 seconds)

| Sensor | Unit | Description |
|--------|------|-------------|
| Solar Power | W | Current solar panel output |
| Home Power | W | Current home consumption |
| Grid Power | W | Grid power (+import / -export) |
| Battery Power | W | Battery power (+discharge / -charge) |
| Battery SOC | % | Battery state of charge |

### Energy Totals (Today & This Month)

| Sensor | Unit | Description |
|--------|------|-------------|
| Solar Production | kWh | Total solar energy generated |
| Home Consumption | kWh | Total energy consumed |
| Grid Export | kWh | Energy sent to the grid |
| Grid Import | kWh | Energy purchased from the grid |
| Battery Charge | kWh | Energy stored in batteries |
| Battery Discharge | kWh | Energy released from batteries |

## Installation

### HACS (recommended)

1. Open HACS in your Home Assistant instance
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/matthew-dresden/solark-cloud-ha` as an **Integration**
4. Search for "SolArk Cloud" and install
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration → SolArk Cloud**

### Manual Installation

1. Download the `custom_components/solark_cloud` directory from this repository
2. Copy it to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Go to **Settings → Devices & Services → Add Integration → SolArk Cloud**

## Configuration

During setup you'll be prompted for:

| Field | Description |
|-------|-------------|
| **Email** | Your SolarkCloud account email |
| **Password** | Your SolarkCloud account password |
| **Plant ID** | Your plant ID (from your SolarkCloud URL) |
| **Update interval** | Polling interval in seconds (default: 30, min: 10, max: 86400) |
| **Timezone** | IANA timezone (e.g. `America/Detroit`). Leave blank to use HA timezone. |
| **Import history** | Pull historical data on first setup |

### Finding Your Plant ID

Your plant ID is in your SolarkCloud URL: `https://www.solarkcloud.com/plants/overview/{PLANT_ID}/...`

## Dashboard

The integration creates a device with all 17 sensors. You can add them to any Lovelace dashboard. Recommended cards:

- **Gauge cards** for real-time power (Solar, Load, Grid, Battery)
- **Entity cards** for energy totals (Today, Month)
- **History graph** for power trends over time
- **Gauge card** for Battery SOC percentage

## License

Apache License 2.0
