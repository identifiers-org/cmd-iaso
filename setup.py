import os

from setuptools import setup, find_packages

from pathlib import Path

with open(Path() / "VERSION") as file:
    version = file.read().strip()

setup(
    name="cmd-iaso",
    version=version,
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
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    package_data={"iaso.curation.pyppeteer": ["*.js", "*.css"]},
    install_requires=[
        "aioconsole==0.1.16",
        "async-generator==1.10",
        "certifi==2020.4.5.1",
        "chardet==3.0.4",
        "click==7.1.2",
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
    author="Moritz Langenstein",
    license="MIT License",
    python_requires=">=3.6",
)

try:
    import en_core_web_sm
except ImportError:
    os.system("python3 -m spacy download en_core_web_sm")

try:
    import xx_ent_wiki_sm
except ImportError:
    os.system("python3 -m spacy download xx_ent_wiki_sm")
