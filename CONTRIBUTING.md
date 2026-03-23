# Contributing to SolArk Cloud HA

## Development Environment Setup

### Devcontainer (recommended)

Open the repository in VS Code or GitHub Codespaces. The devcontainer includes Python, Docker-in-Docker (for running a nested Home Assistant instance), and all required tooling.

### Local Setup

Requirements: Python 3.13+, [uv](https://docs.astral.sh/uv/)

```bash
uv sync          # Install all dependencies including dev
```

Pre-commit hooks are configured for the repository. Install them with:

```bash
pre-commit install
```

## Running a Dev Home Assistant Instance

The project includes a Docker Compose setup that runs a Home Assistant instance with the integration source bind-mounted into `custom_components/` for live reload.

| Command | Description |
|---------|-------------|
| `make dev-up` | Start the HA dev container (available at `http://localhost:8123`) |
| `make dev-restart` | Restart HA to pick up code changes |
| `make dev-logs` | Tail Home Assistant logs |
| `make dev-down` | Stop the HA dev container |
| `make dev-status` | Show container status |
| `make dev-shell` | Open a shell inside the HA container |

## Running Tests

| Command | Description |
|---------|-------------|
| `make test` | Run all tests |
| `make coverage` | Run tests with coverage report (HTML + terminal) |
| `make validate` | Run lint + format check + all tests |
| `make pre-push-check` | Full validation including coverage |

Tests are organized as:

- `tests/unit/` -- Unit tests
- `tests/integration/` -- Integration tests
- `tests/conftest.py` -- Shared fixtures

Coverage threshold is set to 90% in `pyproject.toml`.

## Code Style

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting.

| Command | Description |
|---------|-------------|
| `make lint` | Run ruff lint checks |
| `make format` | Auto-format code |
| `make format-check` | Check formatting without modifying files |

Ruff rules enabled: `E`, `F`, `W`, `I`, `UP`, `B`, `SIM`, `RUF`, `T20`. Line length is 120.

Pre-commit hooks run `ruff --fix` and `ruff-format` automatically on staged files.

## Pull Request Process

1. Create a feature branch from `main`.
2. Make your changes. Keep commits focused and atomic.
3. Run `make validate` to confirm lint, format, and tests all pass.
4. Open a pull request against `main`.
5. Ensure all CI checks pass.
6. A maintainer will review and merge.

## Project Structure

```
solark-cloud-ha/
  src/
    custom_components/
      solark_cloud/
        __init__.py          # Integration setup, service registration
        api_client.py        # Async SolarkCloud API client (httpx)
        config_flow.py       # UI-based config flow with credential validation
        const.py             # All constants, defaults, and profiles
        coordinator.py       # DataUpdateCoordinator for polling
        sensor.py            # 23 sensor entities (power + energy)
        services.yaml        # fetch_energy service definition
        manifest.json        # HACS / HA integration manifest
        strings.json         # UI strings
        translations/
          en.json            # English translations
        www/
          solark-energy-card.js  # Custom Lovelace card
  tests/
    conftest.py
    unit/
    integration/
  docker/
    docker-compose.ha.yml    # Dev HA instance
  Makefile                   # All dev/test/lint commands
  pyproject.toml             # Project metadata, tool config
  hacs.json                  # HACS repository metadata
```
