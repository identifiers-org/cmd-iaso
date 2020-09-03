import os
import subprocess
import sys

from pathlib import Path
from subprocess import PIPE


def run_in_subprocess(cmd, *args, **kwargs):
    return subprocess.run(
        [arg for arg in cmd.split(" ") if len(arg) > 0], *args, **kwargs
    )


def main():
    devnull = open(os.devnull, "w")

    # Check if the cmd-iaso Docker image has been built already
    if (
        run_in_subprocess(
            "docker image inspect cmd-iaso", stdout=devnull, stderr=devnull
        ).returncode
        != 0
    ):
        print("Building docker image cmd-iaso ...")

        run_in_subprocess(f"docker build --tag cmd-iaso {Path()}")

    # Run cmd-iaso with the --docker option to generate the docker run command whilst binding
    #  stdin and stdout (stderr is used to return the command)
    cmd = run_in_subprocess(
        f"docker run -i --net=host --rm --init cmd-iaso --docker {Path().resolve()} {' '.join(sys.argv[1:])}",
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=subprocess.PIPE,
        text=True,
    )

    if cmd.returncode != 0 or not cmd.stderr.startswith("> docker run"):
        # There has been an error - forward it to stderr
        print(cmd.stderr, file=sys.stderr, end="")
    else:
        # Run the returned docker run command whilst binding stdin, stdout and stderr
        run_in_subprocess(
            cmd.stderr[2:],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )


if __name__ == "__main__":
    main()
