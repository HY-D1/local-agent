from pathlib import Path
from typer.testing import CliRunner

import local_agent.cli as cli


runner = CliRunner()


class FakeOllama:
    def __init__(self, host: str, model: str, timeout_s: float = 120.0):
        self.host = host
        self.model = model
        self.timeout_s = timeout_s
        self.last_messages = None

    def healthcheck(self):
        return True, "OK"

    def list_models(self):
        return [self.model]

    def chat(self, messages):
        # capture messages so we can assert stdin got included
        self.last_messages = messages
        return "FAKE_RESPONSE"


def test_doctor_runs(tmp_path: Path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    monkeypatch.chdir(repo)

    monkeypatch.setattr(cli, "OllamaClient", FakeOllama)

    res = runner.invoke(cli.app, ["doctor"])
    assert res.exit_code == 0
    assert "local-agent doctor" in res.stdout
    assert "Ollama reachable" in res.stdout


def test_commands_no_custom_commands(tmp_path: Path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    monkeypatch.chdir(repo)

    res = runner.invoke(cli.app, ["commands"])
    assert res.exit_code == 0
    assert "No custom commands found" in res.stdout


def test_ask_includes_piped_stdin(tmp_path: Path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    monkeypatch.chdir(repo)

    fake = FakeOllama("http://localhost:11434", "test-model")

    # patch constructor to return our instance so we can inspect last_messages
    def _fake_ctor(host: str, model: str, timeout_s: float = 120.0):
        fake.host = host
        fake.model = model
        fake.timeout_s = timeout_s
        return fake

    monkeypatch.setattr(cli, "OllamaClient", _fake_ctor)

    # simulate piped stdin: Click's runner supports input=...
    res = runner.invoke(cli.app, ["ask", "summarize"], input="some logs\nline2\n")
    assert res.exit_code == 0
    assert "FAKE_RESPONSE" in res.stdout

    # Assert stdin text made it into the prompt we sent to the model
    assert fake.last_messages is not None
    user_msg = fake.last_messages[-1]["content"]
    assert "STDIN" in user_msg
    assert "some logs" in user_msg
