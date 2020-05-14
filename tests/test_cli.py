import traceback

from click.testing import CliRunner

from iaso.cli import cli


class TestCLI:
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
