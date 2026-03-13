#!/usr/bin/env bash
# Google Docs MCP Extension for Goose — Installer
# Built by Harold Moses (@hmoses)
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'
info()    { echo -e "${BLUE}\u2139\ufe0f  $*${RESET}"; }
success() { echo -e "${GREEN}\u2705 $*${RESET}"; }
warn()    { echo -e "${YELLOW}\u26a0\ufe0f  $*${RESET}"; }
error()   { echo -e "${RED}\u274c $*${RESET}"; exit 1; }
step()    { echo -e "\n${BOLD}\u2500\u2500 $* ${RESET}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
GOOSE_CONFIG="$HOME/.config/goose/config.yaml"
CREDS_DIR="$HOME/.config/goose/google-docs-extension"
SERVER_SCRIPT="$SCRIPT_DIR/server.py"

step "Checking Python"
if ! command -v python3 &>/dev/null; then error "Python 3.10+ required."; fi
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
success "Python $PYTHON_VERSION found"

step "Setting up virtual environment"
if command -v uv &>/dev/null; then
    uv venv "$VENV_DIR" --python python3 --quiet
    uv pip install --quiet --python "$VENV_DIR/bin/python" "mcp>=1.0.0" "google-auth>=2.0.0" "google-auth-oauthlib>=1.0.0" "google-auth-httplib2>=0.2.0" "google-api-python-client>=2.0.0"
else
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --quiet --upgrade pip
    "$VENV_DIR/bin/pip" install --quiet "mcp>=1.0.0" "google-auth>=2.0.0" "google-auth-oauthlib>=1.0.0" "google-auth-httplib2>=0.2.0" "google-api-python-client>=2.0.0"
fi
success "Dependencies installed"

step "Creating credentials directory"
mkdir -p "$CREDS_DIR"
success "Credentials directory: $CREDS_DIR"

step "Registering in Goose config"
mkdir -p "$(dirname "$GOOSE_CONFIG")"
if [[ ! -f "$GOOSE_CONFIG" ]]; then
    printf 'extensions:\n  google-docs:\n    name: google-docs\n    display_name: Google Docs\n    description: "Read, write, create, and manage Google Docs and Drive files"\n    cmd: "%s/bin/python"\n    args:\n      - "%s"\n    enabled: true\n    type: stdio\n    timeout: 300\n    bundled: false\n' "$VENV_DIR" "$SERVER_SCRIPT" > "$GOOSE_CONFIG"
elif ! grep -q 'google-docs:' "$GOOSE_CONFIG" 2>/dev/null; then
    printf '\n  google-docs:\n    name: google-docs\n    display_name: Google Docs\n    description: "Read, write, create, and manage Google Docs and Drive files"\n    cmd: "%s/bin/python"\n    args:\n      - "%s"\n    enabled: true\n    type: stdio\n    timeout: 300\n    bundled: false\n' "$VENV_DIR" "$SERVER_SCRIPT" >> "$GOOSE_CONFIG"
fi
success "Extension registered"

echo -e "\n${BOLD}${GREEN}\u2705 Installation complete!${RESET}\n"
echo -e "Next: Place credentials.json at ${BOLD}${CREDS_DIR}/credentials.json${RESET}"
echo -e "Then restart Goose and ask: \"authenticate with google docs\""
