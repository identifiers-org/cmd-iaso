""" HEADER fastentrypoints HEADER """

# noqa: D300,D400
# Copyright (c) 2016, Aaron Christianson
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
Monkey patch setuptools to write faster console_scripts with this format:

    import sys
    from mymodule import entry_function
    sys.exit(entry_function())

This is better.

(c) 2016, Aaron Christianson
http://github.com/ninjaaron/fast-entry_points
"""
import os
import re

from pathlib import Path

from setuptools import find_packages, setup
from setuptools.command import easy_install

TEMPLATE = r"""
# -*- coding: utf-8 -*-
# EASY-INSTALL-ENTRY-SCRIPT: '{3}','{4}','{5}'
__requires__ = '{3}'
import re
import sys

from {0} import {1}

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit({2}())
""".lstrip()


@classmethod
def get_args(cls, dist, header=None):  # noqa: D205,D400
    """
    Yield write_script() argument tuples for a distribution's
    console_scripts and gui_scripts entry points.
    """
    if header is None:
        # pylint: disable=E1101
        header = cls.get_header()
    spec = str(dist.as_requirement())
    for type_ in "console", "gui":
        group = type_ + "_scripts"
        for name, ep in dist.get_entry_map(group).items():
            # ensure_safe_name
            if re.search(r"[\\/]", name):
                raise ValueError("Path separators not allowed in script names")
            script_text = TEMPLATE.format(
                ep.module_name, ep.attrs[0], ".".join(ep.attrs), spec, group, name
            )
            # pylint: disable=E1101
            args = cls._get_script_args(type_, name, header, script_text)
            for res in args:
                yield res


# pylint: disable=E1101
easy_install.ScriptWriter.get_args = get_args

""" FOOTER fastentrypoints FOOTER """


setup_kwargs = dict()

try:
    from setuptools_rust import Binding, RustExtension

    setup_kwargs.update(
        rust_extensions=[
            RustExtension(
                "athena",
                path="athena/Cargo.toml",
                debug=False,
                binding=Binding.PyO3,
                optional=True,
            )
        ],
        setup_requires=["setuptools-rust",],
    )
except ImportError:
    print("Please install the setuptools-rust package using:")
    print("> pip install setuptools-rust")
    print()

with open(Path() / "VERSION") as file:
    version = file.read().strip()

setup_kwargs.update(
    name="cmd-iaso",
    version=version,
    author="Moritz Langenstein",
    license="MIT",
    description="cmd-iaso is a command-line tool to help the curators of the identifiers.org registry.",
    url="https://github.com/identifiers-org/cmd-iaso",
    entry_points={
        "console_scripts": ["cmd-iaso = iaso.cli:main"],
        "iaso.plugins": [
            "redirection-chain = iaso.curation.validators.redirect_chain:RedirectChain",
            "dns-error = iaso.curation.validators.redirect_flag_error:DNSError",
            "ssl-error = iaso.curation.validators.redirect_flag_error:SSLError",
            "invalid-response = iaso.curation.validators.redirect_flag_error:InvalidResponseError",
            "http-status-error = iaso.curation.validators.http_status_error:HTTPStatusError",
            "scheme-only-redirect = iaso.curation.validators.scheme_redirect_error:SchemeRedirectError",
        ],
    },
    packages=(find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"])),
    package_data={"iaso.curation.pyppeteer": ["*.js", "*.css"]},
    install_requires=[
        "aioconsole==0.1.16",
        "async-generator==1.10",
        "certifi==2020.4.5.1",
        "chardet==3.0.4",
        "click==7.1.2",
        "click-completion==0.5.2",
        "jsonschema==3.2.0",
        "filelock==3.0.12",
        "httpx==0.13.3",
        "psutil==5.7.0",
        "puremagic==1.8",
        "py-cpuinfo==5.0.0",
        "pycountry==20.7.3",
        "pyppeteer==0.0.25",
        "python-dotenv==0.13.0",
        "requests==2.23.0",
        "spacy==2.3.0",
        "tqdm==4.46.0",
        "urllib3==1.25.9",
        "xeger==0.3.5",
    ],
    setup_requires=(
        ["setuptools >= 40.8.0", "wheel",] + setup_kwargs.get("setup_requires", [])
    ),
    python_requires=">=3.6",
    zip_safe=False,
)

setup(**setup_kwargs)

try:
    import en_core_web_sm
except ImportError:
    os.system("python3 -m spacy download en_core_web_sm")

try:
    import xx_ent_wiki_sm
except ImportError:
    os.system("python3 -m spacy download xx_ent_wiki_sm")
