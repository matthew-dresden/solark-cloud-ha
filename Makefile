SHELL := /bin/bash
.DEFAULT_GOAL := help

ARGS ?=

.PHONY: help install dev test lint format format-check coverage clean pre-push-check validate dev-up dev-down dev-restart dev-logs dev-status dev-shell

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	uv sync --no-dev

dev: ## Install all dependencies including dev
	uv sync

test: ## Run tests
	uv run pytest

lint: ## Run linter checks
	uv run ruff check src/ tests/

format: ## Format code
	uv run ruff format src/ tests/

format-check: ## Check code formatting without modifying files
	uv run ruff format --check src/ tests/

coverage: ## Run tests with coverage report
	uv run pytest --cov --cov-report=term-missing --cov-report=html

validate: lint format-check test ## Run every check (lint + format + all tests)
	@echo "All validations passed."

HA_COMPOSE := docker compose -f docker/docker-compose.ha.yml -p ha-solark-dev

dev-up: ## Start the Home Assistant dev container
	@echo "Starting Home Assistant dev instance..."
	$(HA_COMPOSE) up -d
	@echo "HA starting at http://localhost:8123"

dev-down: ## Stop the Home Assistant dev container
	$(HA_COMPOSE) down

dev-restart: ## Restart HA to pick up code changes
	$(HA_COMPOSE) restart homeassistant

dev-logs: ## Tail Home Assistant logs
	$(HA_COMPOSE) logs -f homeassistant

dev-status: ## Show HA dev container status
	@$(HA_COMPOSE) ps

dev-shell: ## Open a shell inside the HA container
	docker exec -it ha-dev bash

clean: ## Remove build artifacts and caches
	rm -rf dist build *.egg-info htmlcov .coverage .pytest_cache .ruff_cache __pycache__

pre-push-check: ## Run all validation checks (lint, format, tests with coverage)
	@echo "Running pre-push checks..."
	@echo "==> Lint"
	uv run ruff check src/ tests/
	@echo "==> Format check"
	uv run ruff format --check src/ tests/
	@echo "==> Tests with coverage"
	uv run pytest --cov --cov-report=term-missing
	@echo "All pre-push checks passed."
