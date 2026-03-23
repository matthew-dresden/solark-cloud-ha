#!/usr/bin/env bash

# Project-specific setup script for solark-cloud-ha
# This script runs after the main devcontainer setup is complete

set -euo pipefail

log_info "Running project-specific setup..."

# Install uv if not present
if ! command -v uv &> /dev/null; then
  log_info "Installing uv package manager..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
fi

# Install project dependencies
log_info "Installing project dependencies..."
uv sync

# Configure git hooks
log_info "Configuring git hooks..."
git config core.hooksPath .githooks

# Claude CLI aliases
SHELL_RC="${HOME}/.zshrc"
if ! grep -q 'alias claude-bedrock=' "${SHELL_RC}" 2>/dev/null; then
  log_info "Adding Claude CLI aliases to ${SHELL_RC}..."
  cat >> "${SHELL_RC}" <<'ALIASES'

# Claude CLI
alias claude-bedrock='claude --dangerously-skip-permissions'
alias claude-anthropic='CLAUDE_CODE_USE_BEDROCK=0 claude --dangerously-skip-permissions'
ALIASES
else
  log_info "Claude CLI aliases already present in ${SHELL_RC}, skipping."
fi

log_info "Project-specific setup complete"
