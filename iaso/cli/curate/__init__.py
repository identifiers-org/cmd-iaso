import click

from ...click.lazy import LazyCommandGroup, lazy_import
from ...click.mutex import ValidateMutex, MutexOption
from ...click.docker import wrap_docker
from ...click.chrome import ChromeChoice

lazy_import(
    globals(),
    """
from ..click.validators import list_validators
""",
)


@click.command(
    cls=ValidateMutex(LazyCommandGroup("iaso.cli.curate", ["start", "resume"]))
)
@click.pass_context
@click.option(
    "--controller",
    prompt=True,
    required=True,
    type=click.Choice(["terminal", "chrome"]),
    default="chrome",
    show_envvar=True,
)
@click.option(
    "--navigator",
    prompt=True,
    required=True,
    type=click.Choice(["terminal", "chrome"]),
    default="chrome",
    show_envvar=True,
)
@click.option(
    "--informant",
    prompt=True,
    required=True,
    type=click.Choice(["terminal", "chrome"]),
    default="terminal",
    show_envvar=True,
)
@click.option(
    "--chrome",
    prompt=True,
    type=ChromeChoice(),
    cls=MutexOption,
    not_required_if=["controller=terminal", "navigator=terminal", "informant=terminal"],
    default="launch",
    show_envvar=True,
)
@click.option(
    "--tags",
    type=click.Path(exists=False, writable=True, dir_okay=False),
    default="tags.gz",
    show_envvar=True,
)
@click.option(
    "--ignore",
    "-i",
    "ignored_tags",
    multiple=True,
    default=["fixed", "ignore"],
    show_envvar=True,
)
@click.option(
    "--list-validators",
    is_flag=True,
    callback=list_validators,
    expose_value=False,
    is_eager=True,
)
@wrap_docker(exit=False)
def curate(ctx, controller, navigator, informant, tags, ignored_tags, chrome=None):
    """
    Runs the interactive curation process in the terminal and/or a Chrome browser.
    
    \b
    You can start a new session using:
    > cmd-iaso curate [...] start [...]
    You can resume aan existing session using:
    > cmd-iaso curate [...] resume [...]
    
    The --controller, --navigator and --informant options define whether each of these
    components will be run in the terminal or inside Chrome. By default, curate uses
    --controller chrome --navigator chrome --informant terminal --chrome launch.
    
    The --chrome option must be provided iff at least one component uses Chrome.
    
    --chrome launch launches a new Chrome browser instance and closes it automatically
    after the curation session has finished.
    
    --chrome IPv4:PORT / --chrome IPv6:PORT / --chrome localhost:PORT connects to a
    running Chrome browser at the specified address. The browser will not automatically
    be closed after the curation session has finished.
    
    \b
    You can launch a new Chrome browser using:
    > chrome --remote-debugging-port=PORT

    --tags TAGS changes the path where the cross-session tags will be stored.
    By default, tags.gz will be used.

    --ignore TAG / -i TAG can be used to explicitly set the tags which will be
    ignored during the this run of cmd-iaso (more specifically, any suggested curation
    entry with this tag will not be shown). Note that this selection can be changed
    at any time while the interactive curation process is running.
    By default, 'fixed' and 'ignore' will be ignored.
    
    You can list the registered (not yet validated) validator modules using --list-validators.
    
    \b
    For more information on starting or resuming a curation session, use:
    > cmd-iaso curate start --help
    > cmd-iaso curate resume --help
    """

    pass
