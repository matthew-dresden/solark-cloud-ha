# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Full engineering overhaul: src layout, 93% test coverage (100 tests), comprehensive error handling
- Day view area chart with gradient fill, multi-day date range picker (From/To/Go)
- Month/Year/Total bar chart views with all 6 energy metrics
- HA Energy dashboard integration (today sensors use total_increasing state class)
- Options flow for reconfiguring polling interval, system specs, timezone
- Diagnostics support with password redaction
- Automatic OAuth token refresh with refresh_token
- Circuit breaker (5 consecutive failures = 5-minute cooldown)
- HA Repairs integration (creates repair issues when API is unreachable)
- Sensor extra attributes: self_sufficiency_ratio, net_metering_kwh (today sensors)
- SolarkApiProtocol abstraction in core/interfaces.py
- Dev environment: devcontainer with Docker-in-Docker for nested HA instance
- GitHub Actions CI (Python 3.13 + 3.14 matrix)
- Pre-commit hooks and pre-push validation
- Comprehensive documentation (README, CONTRIBUTING, CHANGELOG, CLAUDE.md, LICENSE)

### Changed
- Repository restructured to Python src layout (src/custom_components/)
- All hardcoded values extracted to const.py with named constants
- Coverage threshold raised to 90% (actual: 93%)
- Polling default changed to 60 seconds
- Ruff rules expanded (UP, B, SIM, RUF, T20)
- Silent failures eliminated (all exception handlers log or re-raise)

## [0.5.0] - 2026-03-23

### Added
- Initial release with 23 sensor entities (real-time power + energy totals)
- SolarkCloud API client with async HTTP (httpx)
- Config flow with credential validation
- Configurable polling interval, timezone, system specs
- Historical data import (up to 5 years)
- HACS compatibility
