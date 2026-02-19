#!/bin/bash

# Voice-to-Text System Startup Script
# Production-ready version with proper error handling and logging

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
LOG_FILE="${LOG_DIR}/startup_$(date +%Y%m%d_%H%M%S).log"
SERVER_HOST="100.107.71.56"
SERVER_PORT="8000"
SERVER_USER="al"
SERVER_PATH="voice_to_text_local"
CLIENT_SESSION="voice_client"
SERVER_SESSION="voice_server"
MAX_RETRIES=30
RETRY_INTERVAL=2

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }
log_success() { log "SUCCESS" "$@"; }

# Error handling
cleanup_on_error() {
    log_error "Script failed. Cleaning up..."

    # Kill tmux sessions if they exist
    tmux has-session -t "${CLIENT_SESSION}" 2>/dev/null && tmux kill-session -t "${CLIENT_SESSION}"

    # Try to kill server session on remote
    ssh "${SERVER_USER}@${SERVER_HOST}" "tmux has-session -t ${SERVER_SESSION} 2>/dev/null && tmux kill-session -t ${SERVER_SESSION}" 2>/dev/null || true

    exit 1
}

trap cleanup_on_error ERR

# Create log directory
mkdir -p "${LOG_DIR}"

log_info "Starting Voice-to-Text System..."
log_info "Script directory: ${SCRIPT_DIR}"
log_info "Log file: ${LOG_FILE}"

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if tmux is available
    if ! command -v tmux >/dev/null 2>&1; then
        log_error "tmux is not installed or not in PATH"
        exit 1
    fi

    # Check if nc (netcat) is available for port checking
    if ! command -v nc >/dev/null 2>&1; then
        log_error "netcat (nc) is not installed or not in PATH"
        exit 1
    fi

    # Check SSH connectivity
    if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "${SERVER_USER}@${SERVER_HOST}" "echo 'SSH connection test'" >/dev/null 2>&1; then
        log_error "Cannot connect to server via SSH. Check your SSH configuration."
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Start server on remote machine
start_server() {
    log_info "Starting server on ${SERVER_HOST}..."

    # Kill existing server session if it exists
    ssh "${SERVER_USER}@${SERVER_HOST}" "tmux has-session -t ${SERVER_SESSION} 2>/dev/null && tmux kill-session -t ${SERVER_SESSION}" 2>/dev/null || true

    # Start new server session
    ssh "${SERVER_USER}@${SERVER_HOST}" "
        cd ${SERVER_PATH} &&
        tmux new-session -d -s ${SERVER_SESSION} &&
        tmux send-keys -t ${SERVER_SESSION} 'source venv/bin/activate' Enter &&
        tmux send-keys -t ${SERVER_SESSION} 'python server.py' Enter
    "

    if [ $? -eq 0 ]; then
        log_success "Server session started"
    else
        log_error "Failed to start server session"
        exit 1
    fi
}

# Wait for server to be ready
wait_for_server() {
    log_info "Waiting for server to be ready on ${SERVER_HOST}:${SERVER_PORT}..."

    local retry_count=0

    while [ $retry_count -lt $MAX_RETRIES ]; do
        if nc -z "${SERVER_HOST}" "${SERVER_PORT}" 2>/dev/null; then
            log_success "Server is ready!"
            return 0
        else
            retry_count=$((retry_count + 1))
            log_info "Waiting for server... (${retry_count}/${MAX_RETRIES})"
            sleep $RETRY_INTERVAL
        fi
    done

    log_error "Server failed to start within $(($MAX_RETRIES * $RETRY_INTERVAL)) seconds"

    # Get server logs for debugging
    log_info "Fetching server logs for debugging..."
    ssh "${SERVER_USER}@${SERVER_HOST}" "tmux capture-pane -t ${SERVER_SESSION} -p" 2>/dev/null || log_warn "Could not fetch server logs"

    exit 1
}

# Start client
start_client() {
    log_info "Starting client..."

    # Kill existing client session if it exists
    tmux has-session -t "${CLIENT_SESSION}" 2>/dev/null && tmux kill-session -t "${CLIENT_SESSION}"

    # Check if we're in the right directory
    if [ ! -f "${SCRIPT_DIR}/client_simple_toggle.py" ]; then
        log_error "client_simple_toggle.py not found in ${SCRIPT_DIR}"
        exit 1
    fi

    # Start client session
    tmux new-session -d -s "${CLIENT_SESSION}" -c "${SCRIPT_DIR}"

    # Check if virtual environment exists
    if [ -d "${SCRIPT_DIR}/.venv" ]; then
        tmux send-keys -t "${CLIENT_SESSION}" 'source .venv/bin/activate' Enter
    elif [ -d "${SCRIPT_DIR}/venv" ]; then
        tmux send-keys -t "${CLIENT_SESSION}" 'source venv/bin/activate' Enter
    else
        log_warn "No virtual environment found, running with system Python"
    fi

    tmux send-keys -t "${CLIENT_SESSION}" 'python client_simple_toggle.py' Enter

    log_success "Client started in tmux session '${CLIENT_SESSION}'"
}

# Show status
show_status() {
    echo
    log_info "System Status:"
    echo -e "  ${GREEN}✓${NC} Server running on ${SERVER_HOST}:${SERVER_PORT}"
    echo -e "  ${GREEN}✓${NC} Client running in tmux session '${CLIENT_SESSION}'"
    echo
    echo "Commands:"
    echo "  View client: tmux attach-session -t ${CLIENT_SESSION}"
    echo "  View server logs: ssh ${SERVER_USER}@${SERVER_HOST} 'tmux attach-session -t ${SERVER_SESSION}'"
    echo "  Stop system: ./stop_voice_system.sh"
    echo
    log_success "Voice-to-Text System started successfully!"
}

# Main execution
main() {
    check_prerequisites
    start_server
    wait_for_server
    start_client
    show_status
}

# Run main function
main "$@"