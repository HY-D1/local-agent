# local-agent (v0.1.1)

A small, repo-aware terminal coding assistant that runs locally via **Ollama**.

It can:
- answer questions about the repo (`ask`)
- run an interactive, repo-aware chat (`chat`)
- propose and safely apply a single-file edit (`edit`)

## What’s new in v0.1.1

- `local-agent doctor` — verify Ollama + required tooling
- `local-agent commands` — list available custom slash commands
- `ask` supports piped stdin: `cat logs.txt | local-agent ask "summarize"`
- `chat` supports built-in slash commands: `/help /status /model /config /exit`
- Custom commands via:
  - project: `.local-agent/commands/*.md`
  - user: `~/.local-agent/commands/*.md`
  - templates support `$ARGUMENTS`
- `edit --apply` prompts for confirmation unless `--yes`

---

## Requirements

- Python **3.10+**
- **Ollama** installed and running (default: `http://localhost:11434`)
- Recommended:
  - `rg` (ripgrep) for fast searching
  - `git` for best repo detection

> This tool calls Ollama’s local API. If Ollama isn’t running, `ask/chat/edit` will fail.

---

## Quickstart

```bash
local-agent doctor
local-agent ask "Where is the database connection created?"
local-agent chat
```

## Install

### Option A — Install from source (recommended)

```bash
git clone https://github.com/HY-D1/local-agent.git
cd local-agent

python -m venv .venv
source .venv/bin/activate

python -m pip install -U pip
pip install -e .
```

Verify

```bash
local-agent --help
local-agent --version
```

### Option B — Install from a release wheel

1. Download the wheel from GitHub Releases (match the release version you downloaded).
2. Install it:

```bash
pip install local_agent-<VERSION>-py3-none-any.whl
```

Verify:

```bash
local-agent --version
local-agent --help
```

### Ollama setup

Pull a coding model (example):

```bash
ollama pull qwen2.5-coder:7b
```

Your default model is typically configured in `.local-agent/config.toml`.

## Usage

Run inside any repo you want to analyze:

### Ask a repo-aware question

```bash
local-agent ask "Where is the database connection created?"
```

Ask with piped input

```bash
cat logs.txt | local-agent ask "Summarize the error and suggest next steps."
```

### Interactive chat

```bash
local-agent chat
```

Built-in chat commands:

- `/help` — show help
- `/status` — show repo + model + excludes
- `/model <name>` — switch Ollama model for this session
- `/config` — show effective config
- `/exit` — quit

### Propose an edit (does NOT write changes)

```bash
local-agent edit path/to/file.py -i "Add type hints and improve error handling"
```

### Apply an edit (creates a backup by default)

```bash
local-agent edit path/to/file.py -i "Add type hints and improve error handling" --apply
```

- By default, applying creates a timestamped backup.
- To skip confirmation: `--yes`
- To disable backups (not recommended): `--no-backup`

### Configuration (optional)

Create a config file at:

- `<repo>/.local-agent/config.toml` (recommended)

Example:

```toml
ollama_host = "http://localhost:11434"
model = "qwen2.5-coder:7b"
max_file_chars = 120000
max_context_files = 35
max_tree_files = 250
extra_excludes = ["data", "logs"]
```

### Custom slash commands

Add markdown files:

- Project scope: `.local-agent/commands/<name>.md`
- User scope: `~/.local-agent/commands/<name>.md`

List them:

```bash
local-agent commands
```

Use them in chat as:

```text
/<name> some args here
```

Inside command templates, use `$ARGUMENTS` to receive the arguments.

### Development

Install dev tools:
```bash
pip install -e ".[dev]"
```

Common tasks:

```bash
make lint
make test
make build
make twine-check
make smoke
make all
```

## Notes

- For best results, install ripgrep (`rg`) so file search is faster.
- `edit` without `--apply` never writes files.

## License

MIT (see `LICENSE`)