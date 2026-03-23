# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Full engineering overhaul: src layout, 97% test coverage, comprehensive error handling
- Dev environment: devcontainer with Docker-in-Docker for nested HA instance
- fetch_energy service for on-demand API data retrieval (day/month/year/total)
- Custom Lovelace card with Day/Month/Year/Total tabs and date navigation
- Pre-commit hooks and pre-push validation
- Comprehensive documentation (README, CONTRIBUTING, CHANGELOG)

### Changed
- Repository restructured to Python src layout
- All hardcoded values extracted to const.py
- Coverage threshold raised to 90%
- Polling default changed to 60 seconds
- Ruff rules expanded (UP, B, SIM, RUF, T20)

## [0.5.0] - 2026-03-23

### Added
- Initial release with 23 sensor entities (real-time power + energy totals)
- SolarkCloud API client with async HTTP (httpx)
- Config flow with credential validation
- Configurable polling interval, timezone, system specs
- Historical data import (up to 5 years)
- HACS compatibility
