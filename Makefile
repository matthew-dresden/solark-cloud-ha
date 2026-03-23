SHELL := /bin/bash
.DEFAULT_GOAL := help

ARGS ?=

.PHONY: help install dev test lint format format-check coverage clean pre-push-check

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
