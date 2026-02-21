#!/bin/bash
# shell-integration.sh - Shell integration for local-agent
# 
# Installation:
#   Add this line to your ~/.bashrc or ~/.zshrc:
#   
#   source /path/to/local-agent/shell-integration.sh
#
# Usage:
#   local-agent-start    - Run setup and activate venv (from any directory)
#   la                   - Quick alias for local-agent (after activation)

# Determine the directory where this script is located
LOCAL_AGENT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

function local-agent-start() {
    # Save current directory
    local ORIGINAL_DIR="$(pwd)"
    
    # Change to local-agent directory
    cd "$LOCAL_AGENT_ROOT"
    
    # Run start.sh in current shell context (so venv activation persists)
    if [[ -f "./start.sh" ]]; then
        source ./start.sh
    else
        echo "Error: start.sh not found in $LOCAL_AGENT_ROOT"
        cd "$ORIGINAL_DIR"
        return 1
    fi
    
    # Return to original directory (unless user wants to stay)
    cd "$ORIGINAL_DIR"
}

function local-agent-venv() {
    # Just activate the venv without running full setup
    local VENV_PATH="$LOCAL_AGENT_ROOT/.venv/bin/activate"
    
    if [[ -f "$VENV_PATH" ]]; then
        source "$VENV_PATH"
        echo "✓ Activated local-agent virtual environment"
        echo "  Python: $(which python)"
        echo "  Version: $(python --version)"
    else
        echo "Error: Virtual environment not found at $VENV_PATH"
        echo "Run 'local-agent-start' first to set up."
        return 1
    fi
}

# Quick alias for local-agent (only if we're in the venv)
function la() {
    if [[ -z "$VIRTUAL_ENV" ]]; then
        echo "Virtual environment not active."
        echo "Run 'local-agent-venv' or 'local-agent-start' first."
        return 1
    fi
    local-agent "$@"
}

# Completion function for local-agent commands
function _local-agent-complete() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    local commands="doctor ask chat edit commands help --version --help"
    
    case "$prev" in
        local-agent|la)
            COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
            ;;
        edit)
            # Complete with files from current directory
            COMPREPLY=( $(compgen -f -- "$cur") )
            ;;
        *)
            COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
            ;;
    esac
}

# Register completion if available
if type complete &>/dev/null; then
    complete -F _local-agent-complete local-agent
    complete -F _local-agent-complete la
fi

# Show helpful message when sourced
echo "local-agent shell integration loaded."
echo "Available commands:"
echo "  local-agent-start   - Run setup and activate venv"
echo "  local-agent-venv    - Just activate the venv"
echo "  la                  - Shorthand for local-agent (after venv activation)"
echo ""
echo "Add to your ~/.bashrc or ~/.zshrc:"
echo "  source $LOCAL_AGENT_ROOT/shell-integration.sh"
