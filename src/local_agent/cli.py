from __future__ import annotations

import sys
import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from .config import load_config
from .context import RepoContext
from .ollama_client import OllamaClient
from .prompts import SYSTEM_ASK, SYSTEM_EDIT
from .safety import safe_apply
from .commands import discover_commands, resolve_command, render_template

import re
import subprocess

app = typer.Typer(add_completion=False, help="local-agent: local terminal coding assistant (via Ollama).")
console = Console()


def _read_stdin_if_piped(max_chars: int = 80_000) -> str:
    if sys.stdin is None or sys.stdin.isatty():
        return ""
    data = sys.stdin.read()
    if not data:
        return ""
    if len(data) <= max_chars:
        return data
    return data[: max_chars // 2] + "\n\n...<snip>...\n\n" + data[-max_chars // 2 :]

def _with_line_numbers(text: str, start_line: int = 1, max_lines: int = 400) -> tuple[str, int]:
    lines = text.splitlines()
    lines = lines[:max_lines]
    out = []
    ln = start_line
    for s in lines:
        out.append(f"{ln:>4} | {s}")
        ln += 1
    return "\n".join(out), (ln - 1)

def _force_include_paths(repo_root: Path, question: str) -> list[str]:
    q = question.lower()
    candidates: list[str] = []

    if any(k in q for k in ["entry point", "entrypoint", "cli entry", "typer", "console_scripts", "__main__"]):
        candidates += [
            "src/local_agent/cli.py",
            "src/local_agent/__main__.py",
            "pyproject.toml",
        ]

    if any(k in q for k in ["config", "configuration", "settings", "model", "ollama_host"]):
        candidates += [
            "src/local_agent/config.py",
            ".local-agent/config.toml",
        ]

    if any(k in q for k in ["commands", "slash", "custom commands"]):
        candidates += [
            "src/local_agent/commands.py",
        ]

    out: list[str] = []
    for rel in candidates:
        if (repo_root / rel).exists() and rel not in out:
            out.append(rel)
    return out

def _is_quote_mode(question: str) -> bool:
    q = question.lower()
    triggers = [
        "quote",
        "exact line",
        "exact lines",
        "relevant lines",
        "show the lines",
        "show me the lines",
        "line number",
        "line numbers",
    ]
    return any(t in q for t in triggers)

def _is_quote_request(question: str) -> bool:
    # Backward-compatible alias (some code still calls this)
    return _is_quote_mode(question)

def _quote_patterns(question: str) -> list[str]:
    q = question.lower()

    if any(k in q for k in ["postgres", "postgresql", "psycopg"]):
        return [
            r"postgres",
            r"postgresql",
            r"psycopg2",
            r"asyncpg",
            r"sqlalchemy",
            r"create_engine",
            r"DATABASE_URL",
            r"\bconnect\(",
        ]

    if any(k in q for k in ["entry point", "entrypoint", "typer", "console_scripts", "cli entry"]):
        return [
            r"typer\.Typer",
            r"\bapp\s*=\s*typer\.Typer",
            r"console_scripts",
            r"entry_points",
            r"__main__",
        ]

    # fallback: extract a few meaningful tokens
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", question)
    return tokens[:6]


def _rg_search(root: Path, patterns: list[str], extra_excludes: set[str], max_lines: int = 200) -> str:
    rg = shutil.which("rg")
    if not rg:
        return ""

    cmd: list[str] = [rg, "-n", "--hidden", "--no-heading", "--color", "never", "--glob", "!.git/*"]

    # ignore common build artifacts + user excludes
    for ex in sorted(extra_excludes):
        cmd += ["--glob", f"!{ex}/**"]
    cmd += ["--glob", "!dist/**", "--glob", "!build/**", "--glob", "!**/__pycache__/**", "--glob", "!**/*.egg-info/**"]

    for pat in patterns:
        cmd += ["-e", pat]

    cmd.append(str(root))

    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
    out = (r.stdout or "").strip()
    if not out:
        return ""
    lines = out.splitlines()[:max_lines]
    return "\n".join(lines)


def _quote_mode_response(repo: RepoContext, question: str, extra_excludes: set[str]) -> str:
    patterns = _quote_patterns(question)
    hits = _rg_search(repo.root, patterns, extra_excludes=extra_excludes)

    if not hits:
        pats = "|".join(patterns)
        return (
            "I can't quote exact lines because they were not provided in context.\n"
            f"(I also searched the repo with ripgrep patterns: {pats!r} and found no matches.)\n\n"
            "Try running:\n"
            f"  rg -n \"{pats}\" .\n"
        )

    return (
        "Here are the matching lines (verbatim) from the repository:\n\n"
        "```text\n"
        f"{hits}\n"
        "```\n"
        "\nIf you want, tell me which one to explain and I’ll walk through it."
    )

def build_ask_messages(tree: list[str], files: list[tuple[str, str]], question: str, stdin_text: str = ""):
    blob: list[str] = []
    blob.append("REPO FILE TREE (partial):")
    blob.extend(f"- {p}" for p in tree)

    blob.append("\nRELEVANT FILES:")
    for rel, text in files:
        numbered, end_line = _with_line_numbers(text, start_line=1)
        blob.append(f"\n--- FILE: {rel} (lines 1-{end_line}) ---\n{numbered}")

    if stdin_text.strip():
        blob.append("\nSTDIN (piped input):")
        blob.append(stdin_text)

    blob.append(f"\nUSER QUESTION:\n{question}")

    return [
        {"role": "system", "content": SYSTEM_ASK},
        {"role": "user", "content": "\n".join(blob)},
    ]


def build_edit_messages(file_path: str, file_content: str, instruction: str):
    return [
        {"role": "system", "content": SYSTEM_EDIT},
        {
            "role": "user",
            "content": (
                f"TARGET FILE PATH: {file_path}\n\n"
                f"INSTRUCTION:\n{instruction}\n\n"
                f"CURRENT FILE CONTENT:\n{file_content}"
            ),
        },
    ]

@app.command()
def doctor():
    """
    Environment checks (Claude Code-style 'am I ready to run?').
    """
    cfg = load_config()
    repo = RepoContext.from_cwd()

    client = OllamaClient(host=cfg.ollama_host, model=cfg.model, timeout_s=5.0)
    ok, msg = client.healthcheck()

    models: list[str] = []
    model_present = False
    if ok:
        try:
            models = client.list_models()
            model_present = cfg.model in models
        except Exception:
            pass

    table = Table(title="local-agent doctor")
    table.add_column("Check")
    table.add_column("Result")
    table.add_column("Details", overflow="fold")

    table.add_row("Repo root", "OK", str(repo.root))
    table.add_row("Ollama reachable", "OK" if ok else "FAIL", msg)
    table.add_row("Configured model present", "OK" if model_present else ("WARN" if ok else "SKIP"), cfg.model)

    rg = shutil.which("rg")
    table.add_row("ripgrep (rg)", "OK" if rg else "WARN", rg or "not found (search fallback will be slower)")

    git = shutil.which("git")
    table.add_row("git", "OK" if git else "WARN", git or "not found (not required)")

    console.print(table)

    if ok and not model_present:
        console.print(
            Panel(
                f"Your config model '{cfg.model}' is not listed in Ollama.\n"
                f"Try: ollama pull {cfg.model}\n"
                f"Or change .local-agent/config.toml",
                title="Next steps",
            )
        )

@app.command()
def commands():
    """
    List available custom slash commands.
    """
    repo = RepoContext.from_cwd()
    specs = discover_commands(repo.root)

    if not specs:
        console.print(
            Panel(
                "No custom commands found.\n\n"
                "Create project commands at:\n"
                "  ./.local-agent/commands/<name>.md\n\n"
                "Create user commands at:\n"
                "  ~/.local-agent/commands/<name>.md\n",
                title="Commands",
            )
        )
        raise typer.Exit(0)

    t = Table(title="Custom slash commands")
    t.add_column("Invoke as")
    t.add_column("Scope")
    t.add_column("File")

    for s in specs:
        invoke = f"/{s.name}"  # if unique; chat will require project:/user: if conflicts
        t.add_row(invoke, s.scope, str(s.path))

    console.print(t)


@app.command()
def ask(question: str = typer.Argument(..., help="Your coding question.")):
    cfg = load_config()
    repo = RepoContext.from_cwd()

    # ✅ Quote Mode: deterministic, no hallucinated quotes
    if _is_quote_mode(question):
        msg = _quote_mode_response(repo, question, extra_excludes=cfg.extra_excludes)
        console.print(Panel(msg, title="Quote mode", expand=True))
        raise typer.Exit(0)

    client = OllamaClient(host=cfg.ollama_host, model=cfg.model)

    stdin_text = _read_stdin_if_piped()
    tree = repo.file_tree(max_files=cfg.max_tree_files, extra_excludes=cfg.extra_excludes)
    rels = repo.select_relevant_files(question, max_files=cfg.max_context_files, extra_excludes=cfg.extra_excludes)
    rels = sorted(set(rels + _force_include_paths(repo.root, question)))
    files = [repo.read_file(r, max_chars=cfg.max_file_chars) for r in rels]

    out = client.chat(build_ask_messages(tree, files, question, stdin_text=stdin_text))
    console.print(Panel(out, title=f"Answer ({cfg.model})", expand=True))


@app.command()
def chat():
    """
    Interactive chat (repo-aware each turn) + slash commands.
    """
    cfg = load_config()
    repo = RepoContext.from_cwd()
    model_name = cfg.model
    client = OllamaClient(host=cfg.ollama_host, model=model_name)

    history = [{"role": "system", "content": SYSTEM_ASK}]

    console.print(
        Panel(
            "Type your question.\n"
            "Slash commands: /help /status /model <name> /config /exit\n"
            "Custom commands: put .md files in ./.local-agent/commands/ or ~/.local-agent/commands/\n",
            title="local-agent chat",
        )
    )

    while True:
        try:
            raw = console.input("\n[bold]You[/bold]> ").rstrip()
        except KeyboardInterrupt:
            console.print("\nBye.")
            raise typer.Exit(0)

        if not raw.strip():
            continue

        # Slash commands
        if raw.lstrip().startswith("/"):
            parts = raw.strip().split(maxsplit=1)
            cmd = parts[0].lstrip("/")
            args = parts[1] if len(parts) > 1 else ""

            if cmd in ("exit", "quit"):
                console.print("Bye.")
                raise typer.Exit(0)

            if cmd == "help":
                specs = discover_commands(repo.root)
                msg = [
                    "Built-in:",
                    "  /help",
                    "  /status",
                    "  /model <name>",
                    "  /config",
                    "  /exit",
                    "",
                    "Custom commands:",
                    "  Create project commands in ./.local-agent/commands/*.md",
                    "  Create user commands in ~/.local-agent/commands/*.md",
                    "  Use $ARGUMENTS inside the .md file to receive arguments.",
                ]
                if specs:
                    msg.append("")
                    msg.append("Found commands:")
                    for s in specs:
                        msg.append(f"  /{s.name}   ({s.scope})")
                console.print(Panel("\n".join(msg), title="Help"))
                continue

            if cmd == "status":
                console.print(
                    Panel(
                        f"Repo: {repo.root}\n"
                        f"Model: {model_name}\n"
                        f"Ollama host: {cfg.ollama_host}\n"
                        f"Excludes: {sorted(cfg.extra_excludes)}",
                        title="Status",
                    )
                )
                continue

            if cmd == "config":
                console.print(
                    Panel(
                        f"ollama_host = {cfg.ollama_host}\n"
                        f"model = {model_name}\n"
                        f"max_file_chars = {cfg.max_file_chars}\n"
                        f"max_context_files = {cfg.max_context_files}\n"
                        f"max_tree_files = {cfg.max_tree_files}\n"
                        f"extra_excludes = {sorted(cfg.extra_excludes)}\n\n"
                        "Config search order:\n"
                        "  ./.local-agent/config.toml\n"
                        "  <repo>/.local-agent/config.toml",
                        title="Effective config",
                    )
                )
                continue

            if cmd == "model":
                if not args.strip():
                    console.print(Panel("Usage: /model <ollama-model-name>", title="Model"))
                    continue
                model_name = args.strip()
                client = OllamaClient(host=cfg.ollama_host, model=model_name)
                console.print(Panel(f"Model set to: {model_name}", title="Model"))
                continue

            # Custom markdown commands
            specs = discover_commands(repo.root)
            spec = resolve_command(specs, cmd)
            if spec is None:
                # allow "project:cmd" / "user:cmd"
                spec = resolve_command(specs, f"{cmd}")  # already without leading slash
            if spec is None and ":" in cmd:
                spec = resolve_command(specs, cmd)

            if spec is None:
                console.print(Panel(f"Unknown command: /{cmd}\nTry /help", title="Error"))
                continue

            template = spec.path.read_text(encoding="utf-8", errors="replace")
            prompt = render_template(template, args)
            raw = prompt  # treat as user query and fall through

        # Normal question turn
        if _is_quote_mode(raw):
            msg = _quote_mode_response(repo, raw, extra_excludes=cfg.extra_excludes)
            console.print(Panel(msg, title="Quote mode", expand=True))
            continue

        tree = repo.file_tree(max_files=min(150, cfg.max_tree_files), extra_excludes=cfg.extra_excludes)
        rels = repo.select_relevant_files(raw, max_files=min(12, cfg.max_context_files), extra_excludes=cfg.extra_excludes)
        rels = sorted(set(rels + _force_include_paths(repo.root, raw)))
        files = [repo.read_file(r, max_chars=min(40_000, cfg.max_file_chars)) for r in rels]

        turn = build_ask_messages(tree, files, raw)[1]["content"]
        history.append({"role": "user", "content": turn})

        out = client.chat(history)
        history.append({"role": "assistant", "content": out})

        console.print(Panel(out, title=f"Assistant ({model_name})", expand=True))


@app.command()
def edit(
    path: str = typer.Argument(..., help="Repo-relative file path to edit."),
    instruction: str = typer.Option(..., "-i", "--instruction", help="What to change in the file."),
    apply: bool = typer.Option(False, "--apply", help="Write changes to disk (creates backup)."),
    no_backup: bool = typer.Option(False, "--no-backup", help="When applying, do not create backup."),
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation prompt when applying."),
):
    cfg = load_config()
    repo = RepoContext.from_cwd()
    client = OllamaClient(host=cfg.ollama_host, model=cfg.model)

    rel = path.strip().lstrip("./")
    abs_path = (repo.root / rel).resolve()
    if not abs_path.exists():
        raise typer.BadParameter(f"File does not exist: {rel}")

    current = abs_path.read_text(encoding="utf-8", errors="replace")
    updated = client.chat(build_edit_messages(rel, current, instruction))

    if not apply:
        console.print(Panel(updated, title=f"Proposed file content (not applied) — {rel}", expand=True))
        console.print("\nTip: re-run with [bold]--apply[/bold] to write changes.")
        raise typer.Exit(0)

    if not yes:
        ok = Confirm.ask(f"Apply changes to {rel}?", default=False)
        if not ok:
            console.print(Panel("Aborted (no changes applied).", title="Edit"))
            raise typer.Exit(1)

    safe_apply(abs_path, updated, make_backup=(not no_backup))
    console.print(Panel(f"Applied changes to {rel}", title="Done", expand=False))
