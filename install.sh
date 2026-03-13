#!/usr/bin/env bash
# =============================================================================
# Goose Google Docs Extension — Installer
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${BLUE}ℹ️  $*${RESET}"; }
success() { echo -e "${GREEN}✅ $*${RESET}"; }
warn()    { echo -e "${YELLOW}⚠️  $*${RESET}"; }
error()   { echo -e "${RED}❌ $*${RESET}"; exit 1; }
step()    { echo -e "\n${BOLD}── $* ──────────────────────────────────────${RESET}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
GOOSE_CONFIG="$HOME/.config/goose/config.yaml"
CREDS_DIR="$HOME/.config/goose/google-docs-extension"
SERVER_SCRIPT="$SCRIPT_DIR/server.py"

step "Checking requirements"
if ! command -v python3 &>/dev/null; then
    error "Python 3 is not installed."
fi
success "Python found"

step "Setting up virtual environment"
if command -v uv &>/dev/null; then
    uv venv "$VENV_DIR" --python python3 --quiet
    uv pip install --quiet --python "$VENV_DIR/bin/python" \
        "mcp>=1.0.0" "google-auth>=2.0.0" "google-auth-oauthlib>=1.0.0" \
        "google-auth-httplib2>=0.2.0" "google-api-python-client>=2.0.0"
else
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --quiet --upgrade pip
    "$VENV_DIR/bin/pip" install --quiet \
        "mcp>=1.0.0" "google-auth>=2.0.0" "google-auth-oauthlib>=1.0.0" \
        "google-auth-httplib2>=0.2.0" "google-api-python-client>=2.0.0"
fi
success "Dependencies installed"

step "Creating credentials directory"
mkdir -p "$CREDS_DIR"
success "Credentials directory: $CREDS_DIR"

step "Registering extension in Goose config"
PYTHON_BIN="$VENV_DIR/bin/python"
mkdir -p "$(dirname "$GOOSE_CONFIG")"

if grep -q "google-docs:" "$GOOSE_CONFIG" 2>/dev/null; then
    warn "Extension already registered."
else
    if ! grep -q "^extensions:" "$GOOSE_CONFIG"; then
        echo "" >> "$GOOSE_CONFIG"
        echo "extensions:" >> "$GOOSE_CONFIG"
    fi
    cat >> "$GOOSE_CONFIG" <<YAMLEOF

  google-docs:
    name: google-docs
    display_name: Google Docs
    description: "Read, write, create, and manage Google Docs and Drive files"
    cmd: "$PYTHON_BIN"
    args: ["$SERVER_SCRIPT"]
    enabled: true
    type: stdio
    timeout: 300
    bundled: false
YAMLEOF
    success "Registered in $GOOSE_CONFIG"
fi

echo ""
echo -e "${BOLD}${GREEN}✅ Installation complete! See README.md for next steps.${RESET}"
