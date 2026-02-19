#!/bin/bash

# Voice-to-Text System Status Script
# Check status of both client and server

set -euo pipefail

# Configuration
SERVER_HOST="100.107.71.56"
SERVER_PORT="8000"
SERVER_USER="al"
CLIENT_SESSION="voice_client"
SERVER_SESSION="voice_server"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_client() {
    if tmux has-session -t "${CLIENT_SESSION}" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Client running (session: ${CLIENT_SESSION})"
        return 0
    else
        echo -e "  ${RED}✗${NC} Client not running"
        return 1
    fi
}

check_server() {
    local server_running=false
    local port_open=false

    # Check if server tmux session exists
    if ssh "${SERVER_USER}@${SERVER_HOST}" "tmux has-session -t ${SERVER_SESSION} 2>/dev/null"; then
        server_running=true
    fi

    # Check if port is accessible
    if nc -z "${SERVER_HOST}" "${SERVER_PORT}" 2>/dev/null; then
        port_open=true
    fi

    if [ "$server_running" = true ] && [ "$port_open" = true ]; then
        echo -e "  ${GREEN}✓${NC} Server running (${SERVER_HOST}:${SERVER_PORT})"
        return 0
    elif [ "$server_running" = true ]; then
        echo -e "  ${YELLOW}⚠${NC} Server session exists but port not accessible"
        return 1
    else
        echo -e "  ${RED}✗${NC} Server not running"
        return 1
    fi
}

echo "Voice-to-Text System Status:"
echo

client_status=0
server_status=0

check_client || client_status=1
check_server || server_status=1

echo

if [ $client_status -eq 0 ] && [ $server_status -eq 0 ]; then
    echo -e "${GREEN}System is fully operational${NC}"
    echo
    echo "Commands:"
    echo "  View client: tmux attach-session -t ${CLIENT_SESSION}"
    echo "  View server: ssh ${SERVER_USER}@${SERVER_HOST} 'tmux attach-session -t ${SERVER_SESSION}'"
    echo "  Stop system: ./stop_voice_system.sh"
elif [ $client_status -eq 1 ] && [ $server_status -eq 1 ]; then
    echo -e "${RED}System is not running${NC}"
    echo "  Start with: ./start_voice_system.sh"
else
    echo -e "${YELLOW}System is partially running${NC}"
    echo "  Restart with: ./stop_voice_system.sh && ./start_voice_system.sh"
fi