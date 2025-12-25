from pathlib import Path

from local_agent.commands import discover_commands, resolve_command, render_template


def test_discover_and_resolve_project_command(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    cmd_dir = repo / ".local-agent" / "commands"
    cmd_dir.mkdir(parents=True)
    (cmd_dir / "review.md").write_text("Do this: $ARGUMENTS", encoding="utf-8")

    specs = discover_commands(repo)
    assert any(s.name == "review" and s.scope == "project" for s in specs)

    spec = resolve_command(specs, "review")
    assert spec is not None
    assert spec.path.name == "review.md"

    text = spec.path.read_text(encoding="utf-8")
    out = render_template(text, "focus on errors")
    assert "focus on errors" in out
