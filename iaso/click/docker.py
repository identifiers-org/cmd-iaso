import sys

from functools import update_wrapper
from pathlib import Path

import click


def register_docker(ctx, param, value):
    ctx.ensure_object(dict)

    ctx.obj["docker"] = ["cmd-iaso"] if value else False
    ctx.obj["cwd"] = value

    if sys.argv[1:] == ["--docker", value]:
        click.echo(ctx.get_help())
        ctx.exit()


class DockerPathExists:
    def __bool__(self):
        return not click.get_current_context().obj["docker"]


DOCKER_CHROME_EXECUTABLE_PATH = "/usr/bin/google-chrome"


def docker_chrome_path():
    return (
        DOCKER_CHROME_EXECUTABLE_PATH
        if click.get_current_context().obj["docker"]
        else None
    )


def docker_transform_path(ctx, p, param, value):
    if not isinstance(param.type, click.Path):
        return value

    if value in ["-", DOCKER_CHROME_EXECUTABLE_PATH]:
        return value

    host = Path(value)

    if not host.is_absolute():
        host = (Path(ctx.obj["cwd"]) / host).resolve()

    docker = Path("/root/upload").joinpath(
        *ctx.command_path.split(" "), str(p), host.name
    )

    ctx.obj["docker"].insert(0, f"--mount type=bind,source={host},target={docker}")

    return str(docker)


def wrap_docker(exit=True):
    def init(f):
        def wrapper(ctx, *args, **kwargs):
            if not ctx.obj["docker"]:
                return f(ctx, *args, **kwargs)

            ctx.obj["docker"].append(ctx.command.name)

            for p, param in enumerate(ctx.command.params):
                value = kwargs.get(param.name, None)

                if not value:
                    continue

                if isinstance(param, click.Argument):
                    ctx.obj["docker"].append(
                        docker_transform_path(ctx, p, param, value)
                    )
                elif getattr(param, "is_flag", False):
                    ctx.obj["docker"].append(param.opts[0])
                elif param.multiple:
                    for val in value:
                        ctx.obj["docker"].append(param.opts[0])
                        ctx.obj["docker"].append(
                            docker_transform_path(ctx, p, param, val)
                        )
                else:
                    ctx.obj["docker"].append(param.opts[0])
                    ctx.obj["docker"].append(
                        docker_transform_path(ctx, p, param, value)
                    )

            if exit:
                click.echo(
                    f"> docker run -it --net=host --rm --init {' '.join(str(param) for param in ctx.obj['docker'])}",
                    err=True,
                    nl=False,
                )

                ctx.exit()

        return update_wrapper(wrapper, f)

    return init
