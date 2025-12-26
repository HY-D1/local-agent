from pathlib import Path
from typer.testing import CliRunner

import local_agent.cli as cli


runner = CliRunner()


def test_quote_mode_no_hits_does_not_call_llm(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    monkeypatch.chdir(repo)

    # force no rg hits
    monkeypatch.setattr(cli, "_rg_search", lambda *a, **k: "")

    # if LLM is called, fail
    def boom(*a, **k):
        raise AssertionError("LLM should not be called in quote mode when no matches exist")

    monkeypatch.setattr(cli.OllamaClient, "chat", boom)

    res = runner.invoke(cli.app, ["ask", "Quote the exact line where we connect to Postgres."])
    assert res.exit_code == 0
    assert "I can't quote exact lines" in res.stdout


def test_quote_mode_with_hits_prints_hits(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    monkeypatch.chdir(repo)

    monkeypatch.setattr(cli, "_rg_search", lambda *a, **k: "src/db.py:12:conn = connect(...)")

    res = runner.invoke(cli.app, ["ask", "Quote the exact line where we connect to Postgres."])
    assert res.exit_code == 0
    assert "src/db.py:12:conn = connect(...)" in res.stdout
