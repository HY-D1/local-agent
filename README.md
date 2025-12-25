# local-agent (v0.1.1)

A small terminal coding assistant that runs locally using **Ollama**.  
It can:

- answer repo-aware questions (`ask`)
- run an interactive chat (`chat`)
- edit a single file safely (`edit`)

## New in v0.1.1

- `local-agent doctor` — check Ollama + tooling
- `local-agent commands` — list custom slash commands
- `ask` supports piped stdin: `cat logs.txt | local-agent ask "explain"`
- `chat` supports slash commands: `/help /status /model /config /exit`
- Custom commands via `.local-agent/commands/*.md` and `~/.local-agent/commands/*.md` with `$ARGUMENTS`
- `edit --apply` prompts for confirmation unless `--yes`

---

## Requirements

- Python **3.10+**
- **Ollama** installed and running (`http://localhost:11434`)

> This tool calls Ollama’s local API. If Ollama isn’t running, commands like `ask/chat/edit` will fail.

---

## Install

### Option A — Install from source (recommended for development)
```bash
git clone https://github.com/HY-D1/local-agent.git
cd local-agent

python -m venv .venv
source .venv/bin/activate

python -m pip install -U pip
pip install -e .
```

Now you can run:
```bash
local-agent --help
```

### Option B — Install from a release wheel (easy on other devices)
1. Download the .whl from GitHub Releases (v0.1.0)

2. Install it:
```bash
pip install local_agent-0.1.0-py3-none-any.whl
```

Then:
```bash
local-agent --help
```

### Ollama setup

Pull a coding model (example):
```bash
ollama pull qwen2.5-coder:7b
```

(Your default model is configured as `qwen2.5-coder:7b.`)

## Usage

Run inside any repo you want to analyze:

### Ask a repo-aware question
```bash
local-agent ask "Where is the database connection created?"
```

### Interactive chat
```bash
local-agent chat
```

### Propose an edit (does NOT write changes)
```bash
local-agent edit path/to/file.py -i "Add type hints and improve error handling"
```

### Apply an edit (creates a backup by default)
```bash
local-agent edit path/to/file.py -i "Add type hints and improve error handling" --apply
```

Disable backups (not recommended):
```bash
local-agent edit path/to/file.py -i "..." --apply --no-backup
```

### Configuration (optional)

Create a config file at:

- `<your-repo>/.local-agent/config.toml`(recommended), or
- `./.local-agent/config.toml`

Example:
```toml
ollama_host = "http://localhost:11434"
model = "qwen2.5-coder:7b"
max_file_chars = 120000
max_context_files = 35
max_tree_files = 250
extra_excludes = ["data", "logs"]
```

## Notes
- `edit` without `--apply` never writes files.
- `edit --apply` creates a timestamped backup of the original file.
- For best results, install `ripgrep` (`rg`) so file search is faster.

## License
### MIT