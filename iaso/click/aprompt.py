import click

from aioconsole import ainput


async def aprompt(
    text,
    default=None,
    confirmation_prompt=False,
    type=None,
    value_proc=None,
    prompt_suffix=": ",
    show_default=True,
    err=False,
    show_choices=True,
):
    """Prompts a user for input.  This is a convenience function that can
    be used to prompt a user for input later.
    If the user aborts the input by sending a interrupt signal, this
    function will catch it and raise a :exc:`Abort` exception.
    .. versionadded:: 7.0
       Added the show_choices parameter.
    .. versionadded:: 6.0
       Added unicode support for cmd.exe on Windows.
    .. versionadded:: 4.0
       Added the `err` parameter.
    :param text: the text to show for the prompt.
    :param default: the default value to use if no input happens.  If this
                    is not given it will prompt until it's aborted.
    :param hide_input: if this is set to true then the input value will
                       be hidden.
    :param confirmation_prompt: asks for confirmation for the value.
    :param type: the type to use to check the value against.
    :param value_proc: if this parameter is provided it's a function that
                       is invoked instead of the type conversion to
                       convert a value.
    :param prompt_suffix: a suffix that should be added to the prompt.
    :param show_default: shows or hides the default value in the prompt.
    :param err: if set to true the file defaults to ``stderr`` instead of
                ``stdout``, the same as with echo.
    :param show_choices: Show or hide choices if the passed type is a Choice.
                         For example if type is a Choice of either day or week,
                         show_choices is true and text is "Group by" then the
                         prompt will be "Group by (day, week): ".
    """
    result = None

    async def prompt_func(text):
        try:
            # Write the prompt separately so that we get nice
            # coloring through colorama on Windows
            click.echo(text, nl=False, err=err)

            return await ainput("")
        except (KeyboardInterrupt, EOFError):
            # getpass doesn't print a newline if the user aborts input with ^C.
            # Allegedly this behavior is inherited from getpass(3).
            # A doc bug has been filed at https://bugs.python.org/issue24711
            click.echo(None, err=err)
            raise click.exceptions.Abort()

    if value_proc is None:
        value_proc = click.types.convert_type(type, default)

    prompt = click.termui._build_prompt(
        text, prompt_suffix, show_default, default, show_choices, type
    )

    while 1:
        while 1:
            value = await prompt_func(prompt)
            if value:
                break
            elif default is not None:
                if isinstance(value_proc, click.types.Path):
                    # validate Path default value(exists, dir_okay etc.)
                    value = default
                    break
                return default
        try:
            result = value_proc(value)
        except click.exceptions.UsageError as e:
            click.echo(f"Error: {e.message}", err=err)  # noqa: B306
            continue
        if not confirmation_prompt:
            return result
        while 1:
            value2 = prompt_func("Repeat for confirmation: ")
            if value2:
                break
        if value == value2:
            return result
        click.echo("Error: the two entered values do not match", err=err)
