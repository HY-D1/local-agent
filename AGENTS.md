# AGENTS.md — local-agent contributor instructions

This repo is a local terminal coding assistant built on Ollama.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e .
```

## Run
```bash
local-agent --help
local-agent doctor
local-agent chat
local-agent ask "Where is the database connection created?"
```

## Tests
```bash
pytest -q
```
Or using the Makefile:

```bash
make venv
make install
make test
```

## Style / Lint
We use `ruff` for linting.

```bash
ruff check .
```

## Repo conventions
- Core package: `src/local_agent/`
- CLI entry: `src/local_agent/cli.py` (Typer app)
- Ollama client: `src/local_agent/ollama_client.py`
- Prompts: `src/local_agent/prompts.py`
- Repo context collection: `src/local_agent/context.py`
- Custom commands:
    - Project scope: `./.local-agent/commands/*.md`
    - User scope: `~/.local-agent/commands/*.md`

## Safety
- `edit` does not write by default.
- `edit --apply` prompts for confirmation unless `--yes` is passed.