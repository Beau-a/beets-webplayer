#!/usr/bin/env bash
# install.sh — beets-webplayer setup script
# Run once after cloning to configure and install dependencies.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/backend/app/config.py"
ENV_FILE="$SCRIPT_DIR/backend/.env"

# ── Colours ────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║       beets-webplayer installer      ║${NC}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════╝${NC}"
    echo ""
}

print_step() { echo -e "${BOLD}▶ $1${NC}"; }
print_ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
print_warn() { echo -e "  ${YELLOW}⚠${NC}  $1"; }
print_err()  { echo -e "  ${RED}✗${NC} $1"; }

# ── Checks ─────────────────────────────────────────────────────────────────
check_dependencies() {
    print_step "Checking system dependencies"

    local missing=()

    if ! command -v python3 &>/dev/null; then
        missing+=("python3")
    else
        print_ok "python3 $(python3 --version 2>&1 | awk '{print $2}')"
    fi

    if ! command -v pip3 &>/dev/null && ! python3 -m pip --version &>/dev/null 2>&1; then
        missing+=("pip")
    else
        print_ok "pip"
    fi

    if ! command -v node &>/dev/null; then
        missing+=("node")
    else
        print_ok "node $(node --version)"
    fi

    if ! command -v npm &>/dev/null; then
        missing+=("npm")
    else
        print_ok "npm $(npm --version)"
    fi

    if ! command -v beet &>/dev/null; then
        print_warn "beet CLI not found in PATH — beets must be installed and configured before importing music."
    else
        print_ok "beet $(beet version 2>/dev/null | head -1)"
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        echo ""
        print_err "Missing required dependencies: ${missing[*]}"
        echo "    Please install them and re-run this script."
        exit 1
    fi

    echo ""
}

# ── User prompts ────────────────────────────────────────────────────────────
gather_config() {
    print_step "Configuration"
    echo ""

    # Beets DB path
    local default_db=""
    # Try to detect from beets config if available
    if command -v beet &>/dev/null; then
        default_db=$(beet config 2>/dev/null | grep '^library:' | awk '{print $2}' || true)
    fi
    [ -z "$default_db" ] && default_db="$HOME/.config/beets/musiclibrary.db"

    while true; do
        echo -e "  ${BOLD}Beets library database path${NC}"
        echo -e "  This is the SQLite .db file beets uses to store your music library."
        read -rp "  Path [$default_db]: " input_db
        BEETS_DB="${input_db:-$default_db}"

        if [ -f "$BEETS_DB" ]; then
            print_ok "Found: $BEETS_DB"
            break
        else
            echo ""
            print_warn "$BEETS_DB does not exist."
            read -rp "  Use this path anyway? (beets will create it on first import) [y/N]: " yn
            case "$yn" in
                [Yy]*) break ;;
                *) echo "" ;;
            esac
        fi
    done
    echo ""

    # Music base path (for streaming security check)
    local default_music="/mnt/nfs/ml"
    echo -e "  ${BOLD}Music library root directory${NC}"
    echo -e "  All audio files must live under this path (used for playback security)."
    read -rp "  Path [$default_music]: " input_music
    MUSIC_BASE="${input_music:-$default_music}"
    if [ -d "$MUSIC_BASE" ]; then
        print_ok "Found: $MUSIC_BASE"
    else
        print_warn "$MUSIC_BASE does not exist — make sure it's mounted before starting the server."
    fi
    echo ""

    # Import base path
    local default_import
    default_import=$(dirname "$MUSIC_BASE")
    echo -e "  ${BOLD}Import base directory${NC}"
    echo -e "  Directory tree allowed for browser-based imports (parent of music root)."
    read -rp "  Path [$default_import]: " input_import
    IMPORT_BASE="${input_import:-$default_import}"
    print_ok "Import base: $IMPORT_BASE"
    echo ""

    # Backend port
    echo -e "  ${BOLD}Backend port${NC}"
    read -rp "  Port [5000]: " input_port
    BACKEND_PORT="${input_port:-5000}"
    print_ok "Port: $BACKEND_PORT"
    echo ""
}

# ── Write config ────────────────────────────────────────────────────────────
write_env() {
    print_step "Writing backend configuration"

    cat > "$ENV_FILE" <<EOF
BEETS_DB_PATH=$BEETS_DB
MUSIC_BASE_PATH=$MUSIC_BASE
IMPORT_BASE_PATH=$IMPORT_BASE
PORT=$BACKEND_PORT
EOF

    print_ok "Written to $ENV_FILE"
    echo ""
}

# ── Python virtualenv + deps ─────────────────────────────────────────────────
install_backend() {
    print_step "Installing backend dependencies"

    cd "$SCRIPT_DIR/backend"

    if [ ! -d "venv" ]; then
        echo "  Creating Python virtualenv..."
        python3 -m venv venv
        print_ok "Virtualenv created"
    else
        print_ok "Virtualenv already exists"
    fi

    echo "  Installing Python packages..."
    venv/bin/pip install --quiet --upgrade pip
    venv/bin/pip install --quiet -r requirements.txt
    print_ok "Python packages installed"
    echo ""

    cd "$SCRIPT_DIR"
}

# ── Node deps ────────────────────────────────────────────────────────────────
install_frontend() {
    print_step "Installing frontend dependencies"

    cd "$SCRIPT_DIR/frontend"
    npm install --silent
    print_ok "Node packages installed"
    echo ""

    cd "$SCRIPT_DIR"
}

# ── Done ─────────────────────────────────────────────────────────────────────
print_done() {
    echo -e "${BOLD}${GREEN}╔══════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${GREEN}║        Installation complete!        ║${NC}"
    echo -e "${BOLD}${GREEN}╚══════════════════════════════════════╝${NC}"
    echo ""
    echo "  To start the application:"
    echo ""
    echo -e "    ${CYAN}# Backend (terminal 1)${NC}"
    echo -e "    ${BOLD}make backend${NC}"
    echo ""
    echo -e "    ${CYAN}# Frontend dev server (terminal 2)${NC}"
    echo -e "    ${BOLD}make frontend${NC}"
    echo ""
    echo -e "  Or build the frontend for production:"
    echo -e "    ${BOLD}cd frontend && npm run build${NC}"
    echo -e "  Then the backend serves everything at ${BOLD}http://localhost:${BACKEND_PORT}${NC}"
    echo ""
}

# ── Main ─────────────────────────────────────────────────────────────────────
main() {
    print_header
    check_dependencies
    gather_config
    write_env
    install_backend
    install_frontend
    print_done
}

main "$@"
