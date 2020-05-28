from pathlib import Path

from click.testing import CliRunner

from iaso.cli import cli


class TestCLI:
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            args=["--version"],
            prog_name="cmd-iaso",
            color=True,
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        with open(Path().parent / "VERSION", "r") as file:
            assert result.output.strip() == f"cmd-iaso, version {file.read().strip()}"

    def test_environment(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            args=["environment"],
            prog_name="cmd-iaso",
            color=True,
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        print()
        print(" TESTING ENVIRONMENT ".center(80, "="))
        print(result.output, end="")
        print(" TESTING ENVIRONMENT ".center(80, "="))
