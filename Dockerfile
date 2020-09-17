FROM python:3.8-slim-buster

# Copy the relevant resources
COPY ./LICENSE /app/LICENSE
COPY ./VERSION /app/VERSION
COPY ./setup.py /app/setup.py
COPY ./iaso /app/iaso
COPY ./athena /app/athena
COPY ./metis /app/metis

WORKDIR /app

SHELL ["/bin/bash", "-c"]

# Install cmd-iaso with athena-analysis support
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get install -y --no-install-recommends python3-dev && \
    apt-get install -y --no-install-recommends curl && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y --profile minimal && \
    source $HOME/.cargo/env && \
    pip install --upgrade pip && \
    pip install -e . && \
    rustup self uninstall -y && \
    apt-get remove -y curl && \
    apt-get remove -y python3-dev && \
    apt-get remove -y gcc && \
    apt-get -y autoremove

# Assert that cmd-iaso has been installed with athena-analysis support
RUN cmd-iaso dump2datamine --check-athena

# Pre-Install the correct Chromium version for scraping
RUN echo 'import os; os.environ["PYPPETEER_CHROMIUM_REVISION"] = "782078";' \
         'from pyppeteer.chromium_downloader import download_chromium;' \
         'download_chromium()' | python3

# Install the Chromium scraping dependencies
RUN apt-get update && \
    apt-get install -y libgtk2.0-0 libgtk-3-0 libnotify-dev \
                       libgconf-2-4 libnss3 libxss1 \
                       libasound2 libxtst6 xauth xvfb \
                       libgbm-dev && \
    apt-get -y autoremove

ENTRYPOINT ["cmd-iaso"]
