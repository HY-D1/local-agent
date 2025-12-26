from typer.testing import CliRunner
import local_agent.cli as cli
from local_agent import __version__

runner = CliRunner()

def test_version_flag_prints_version():
    res = runner.invoke(cli.app, ["--version"])
    assert res.exit_code == 0
    assert __version__ in res.stdout

def test_no_args_prints_help():
    res = runner.invoke(cli.app, [])
    assert res.exit_code == 0
    assert "Usage:" in res.stdout
    assert "doctor" in res.stdout
