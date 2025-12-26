# AGENTS.md — local-agent contributor instructions

`local-agent` is a local terminal coding assistant powered by Ollama (HTTP API).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

## Run (CLI)
```bash
local-agent --help
local-agent doctor
local-agent chat
local-agent ask "Where is the database connection created?"
```
### Note on Ollama

Real `ask/chat/edit` runs require Ollama to be running and reachable (default: `http://localhost:11434`).
Use `local-agent doctor` to verify connectivity + model availability.

## Tests
Preferred (consistent with CI):

```bash
make test
```

Or directly:

```bash
python -m pytest -q
```

## Build / package checks

```bash
make build
make twine-check
make smoke
```

What these do:

- `build`: creates `dist/*.whl` and `dist/*.tar.gz`
- `twine-check`: validates packaging metadata
- `smoke`: installs the wheel into a fresh venv and runs:
    - `python -c "import local_agent"`
    - `local-agent --help`
    - `local-agent commands`

## Style / Lint

We use `ruff` for linting.

```bash
ruff check .
```

(If you add formatting later, keep it consistent repo-wide.)

## Repo conventions / layout

- Core package: `src/local_agent/`
- CLI entry: `src/local_agent/cli.py` (Typer app)
- Ollama client: `src/local_agent/ollama_client.py`
- Prompts: `src/local_agent/prompts.py`
- Repo context collection: `src/local_agent/context.py`

### Custom commands (slash commands)

Markdown command files can live in:

- Project scope: `./.local-agent/commands/*.md`
- User scope: `~/.local-agent/commands/*.md`

Templates may use:

- `$ARGUMENTS` to receive user-provided arguments.

## Behavior rules (important)

- **Quote/exact-lines requests must be deterministic.**
    - Prefer `rg` output and only present lines that exist in the repo.
    - If nothing matches, say you can’t quote exact lines and suggest the `rg` command to run.

## Safety

- `edit` does **not** write by default.
- `edit --apply` prompts for confirmation unless `--yes` is passed.
- Avoid destructive operations unless explicitly requested by the user.