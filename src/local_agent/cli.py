from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from .config import load_config
from .context import RepoContext
from .ollama_client import OllamaClient
from .prompts import SYSTEM_ASK, SYSTEM_EDIT
from .safety import safe_apply

app = typer.Typer(add_completion=False, help="local-agent: local terminal coding assistant (via Ollama).")
console = Console()


def build_ask_messages(tree: list[str], files: list[tuple[str, str]], question: str):
    blob: list[str] = []
    blob.append("REPO FILE TREE (partial):")
    blob.extend(f"- {p}" for p in tree)

    blob.append("\nRELEVANT FILES:")
    for rel, text in files:
        blob.append(f"\n--- FILE: {rel} ---\n{text}")

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
def ask(question: str = typer.Argument(..., help="Your coding question.")):
    cfg = load_config()
    repo = RepoContext.from_cwd()
    client = OllamaClient(host=cfg.ollama_host, model=cfg.model)

    tree = repo.file_tree(max_files=cfg.max_tree_files, extra_excludes=cfg.extra_excludes)
    rels = repo.select_relevant_files(question, max_files=cfg.max_context_files, extra_excludes=cfg.extra_excludes)
    files = [repo.read_file(r, max_chars=cfg.max_file_chars) for r in rels]

    out = client.chat(build_ask_messages(tree, files, question))
    console.print(Panel(out, title=f"Answer ({cfg.model})", expand=True))


@app.command()
def chat():
    """
    Interactive chat (repo-aware each turn, lightweight).
    """
    cfg = load_config()
    repo = RepoContext.from_cwd()
    client = OllamaClient(host=cfg.ollama_host, model=cfg.model)

    history = [{"role": "system", "content": SYSTEM_ASK}]

    console.print(Panel("Type your question. Ctrl+C to exit.", title="local-agent chat"))
    while True:
        try:
            q = console.input("\n[bold]You[/bold]> ").strip()
        except KeyboardInterrupt:
            console.print("\nBye.")
            raise typer.Exit(0)

        if not q:
            continue

        tree = repo.file_tree(max_files=min(150, cfg.max_tree_files), extra_excludes=cfg.extra_excludes)
        rels = repo.select_relevant_files(q, max_files=min(12, cfg.max_context_files), extra_excludes=cfg.extra_excludes)
        files = [repo.read_file(r, max_chars=min(40_000, cfg.max_file_chars)) for r in rels]

        turn = build_ask_messages(tree, files, q)[1]["content"]
        history.append({"role": "user", "content": turn})

        out = client.chat(history)
        history.append({"role": "assistant", "content": out})

        console.print(Panel(out, title=f"Assistant ({cfg.model})", expand=True))


@app.command()
def edit(
    path: str = typer.Argument(..., help="Repo-relative file path to edit."),
    instruction: str = typer.Option(..., "-i", "--instruction", help="What to change in the file."),
    apply: bool = typer.Option(False, "--apply", help="Write changes to disk (creates backup)."),
    no_backup: bool = typer.Option(False, "--no-backup", help="When applying, do not create backup."),
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

    safe_apply(abs_path, updated, make_backup=(not no_backup))
    console.print(Panel(f"Applied changes to {rel}", title="Done", expand=False))
