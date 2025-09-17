#!/bin/bash

# Voice-to-Text System Stop Script
# Gracefully stops both client and server

set -euo pipefail

# Configuration
SERVER_HOST="192.168.0.105"
SERVER_USER="al"
CLIENT_SESSION="voice_client"
SERVER_SESSION="voice_server"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "[INFO] $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

log_info "Stopping Voice-to-Text System..."

# Stop client
if tmux has-session -t "${CLIENT_SESSION}" 2>/dev/null; then
    tmux kill-session -t "${CLIENT_SESSION}"
    log_success "Client session stopped"
else
    log_warn "Client session not found"
fi

# Stop server
if ssh "${SERVER_USER}@${SERVER_HOST}" "tmux has-session -t ${SERVER_SESSION} 2>/dev/null"; then
    ssh "${SERVER_USER}@${SERVER_HOST}" "tmux kill-session -t ${SERVER_SESSION}"
    log_success "Server session stopped"
else
    log_warn "Server session not found"
fi

log_success "Voice-to-Text System stopped"