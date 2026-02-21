#!/bin/bash
# start.sh - Quick setup and start script for local-agent
# This script simplifies the setup process for new users
#
# Usage:
#   ./start.sh              - Run setup (venv activation won't persist)
#   source ./start.sh       - Run setup and stay in venv (if not already active)
#
# Note: We avoid 'set -e' because this script supports being sourced

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if we're already in a virtual environment
IN_VENV=0
if [[ -n "${VIRTUAL_ENV}" ]] || [[ -n "${CONDA_DEFAULT_ENV}" ]]; then
    IN_VENV=1
fi

# Check if we should show interactive menu (only for direct execution, not sourcing)
SHOW_MENU=0
if [[ -t 0 ]] && [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Running directly (not sourced) and have a TTY
    SHOW_MENU=1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           local-agent - Quick Setup Script                 ║${NC}"
echo -e "${BLUE}║     Local AI coding assistant powered by Ollama            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo

if [[ $IN_VENV -eq 1 ]]; then
    echo -e "${GREEN}✓ Already in a virtual environment${NC}"
fi

# Check Python version
echo -e "${BLUE}▶ Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    echo "Please install Python 3.10 or higher: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
else
    echo -e "${RED}✗ Python $PYTHON_VERSION is too old (requires 3.10+)${NC}"
    exit 1
fi

# Check if Ollama is installed and running
echo -e "${BLUE}▶ Checking Ollama...${NC}"
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama CLI found${NC}"
else
    echo -e "${YELLOW}⚠ Ollama CLI not found in PATH${NC}"
    echo "  Install from: https://ollama.com/download"
fi

# Check if Ollama server is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama server is running on localhost:11434${NC}"
else
    echo -e "${YELLOW}⚠ Ollama server not reachable at http://localhost:11434${NC}"
    echo "  Start Ollama with: ollama serve"
fi

# Setup virtual environment
echo
echo -e "${BLUE}▶ Setting up virtual environment...${NC}"
if [ -d ".venv" ]; then
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
else
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment (safely)
if [[ $IN_VENV -eq 0 ]]; then
    echo "Activating virtual environment..."
    # Use 'source' safely - don't exit on error
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate || {
            echo -e "${YELLOW}⚠ Could not activate venv automatically${NC}"
            echo "  Please run: source .venv/bin/activate"
        }
    fi
else
    echo -e "${GREEN}✓ Virtual environment already active${NC}"
fi

# Upgrade pip
echo "Upgrading pip..."
pip install -q --upgrade pip

# Install local-agent
echo
echo -e "${BLUE}▶ Installing local-agent...${NC}"
if pip install -q -e "."; then
    echo -e "${GREEN}✓ local-agent installed${NC}"
else
    echo -e "${RED}✗ Installation failed${NC}"
    exit 1
fi

# Create default config if not exists
echo
echo -e "${BLUE}▶ Checking configuration...${NC}"
CONFIG_DIR=".local-agent"
CONFIG_FILE="$CONFIG_DIR/config.toml"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating default configuration..."
    mkdir -p "$CONFIG_DIR"
    cat > "$CONFIG_FILE" << 'EOF'
# local-agent configuration
# See: https://github.com/HY-D1/local-agent

ollama_host = "http://localhost:11434"
model = "qwen2.5-coder:7b"
max_file_chars = 120000
max_context_files = 35
max_tree_files = 250
extra_excludes = ["data", "logs", ".venv", "node_modules"]
EOF
    echo -e "${GREEN}✓ Default config created at $CONFIG_FILE${NC}"
else
    echo -e "${GREEN}✓ Configuration exists${NC}"
fi

# Check for recommended model
echo
echo -e "${BLUE}▶ Checking recommended model...${NC}"
DEFAULT_MODEL="qwen2.5-coder:7b"

if curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q "$DEFAULT_MODEL"; then
    echo -e "${GREEN}✓ Model '$DEFAULT_MODEL' is available${NC}"
else
    echo -e "${YELLOW}⚠ Model '$DEFAULT_MODEL' not found${NC}"
    echo "  Pull it with: ollama pull $DEFAULT_MODEL"
    echo "  Or change model in $CONFIG_FILE"
fi

# Run doctor check
echo
echo -e "${BLUE}▶ Running environment check...${NC}"
local-agent doctor

# Success message
echo
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Setup Complete! 🎉                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo
# Check again if we're in a venv (might have changed during script)
if [[ -z "${VIRTUAL_ENV}" ]] && [[ -z "${CONDA_DEFAULT_ENV}" ]]; then
    echo -e "${YELLOW}⚠ Not in virtual environment${NC}"
    echo "To use local-agent, activate the virtual environment:"
    echo
    echo "  source .venv/bin/activate"
    echo
    echo "Or run this script with 'source' to auto-activate:"
    echo
    echo "  source ./start.sh"
    echo
fi

echo "Quick start commands:"
echo "  local-agent doctor       - Check environment"
echo "  local-agent ask \"...\"   - Ask a question about your code"
echo "  local-agent chat         - Start interactive chat"
echo "  local-agent --help       - Show all commands"
echo
echo "Configuration: $CONFIG_FILE"
echo
echo -e "${YELLOW}Tip: Make sure Ollama is running before using local-agent${NC}"
echo "     Start Ollama: ollama serve"
echo
echo "💡 Pro tip: Add shell integration to your ~/.bashrc or ~/.zshrc:"
echo "     source $(pwd)/shell-integration.sh"
echo "   Then use 'local-agent-start' from any directory!"
echo
# Interactive menu (only when running directly, not when sourced)
if [[ $SHOW_MENU -eq 1 ]]; then
    echo
    echo -e "${BLUE}What would you like to do next?${NC}"
    echo
    echo "  1) Start interactive chat (local-agent chat)"
    echo "  2) Run diagnostics (local-agent doctor)"
    echo "  3) Ask a question (local-agent ask)"
    echo "  4) Show help (local-agent --help)"
    echo "  5) Exit"
    echo
    read -p "Enter choice [1-5]: " choice
    
    case "$choice" in
        1)
            echo
            echo -e "${GREEN}Starting local-agent chat...${NC}"
            echo "Type /exit to quit, /help for commands"
            echo
            local-agent chat
            ;;
        2)
            echo
            local-agent doctor
            ;;
        3)
            echo
            read -p "Enter your question: " question
            echo
            local-agent ask "$question"
            ;;
        4)
            echo
            local-agent --help
            ;;
        5|*)
            echo
            echo "You're all set! Run 'local-agent --help' anytime."
            ;;
    esac
else
    # Not showing menu (sourced or non-interactive)
    echo
    echo "Setup complete! You can now use local-agent commands."
fi
