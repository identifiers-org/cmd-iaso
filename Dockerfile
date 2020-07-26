FROM python:3.7-slim-buster

# Copy the relevant resources
COPY ./LICENSE /app/LICENSE
COPY ./VERSION /app/VERSION
COPY ./setup.py /app/setup.py
COPY ./iaso /app/iaso
COPY ./athena /app/athena

WORKDIR /app

# Install cmd-iaso
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get install -y --no-install-recommends python3-dev && \
    apt-get install -y --no-install-recommends curl && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    python3 setup.py install && \
    curl https://sh.rustup.rs -sSf | sh -s -- --uninstall && \
    apt-get remove -y curl && \
    apt-get remove -y python3-dev && \
    apt-get remove -y gcc && \
    apt-get -y autoremove

# Install dependencies
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -yq curl libgconf-2-4 gnupg2 && \
    apt-get -y autoremove

# Install Google Chrome
RUN curl https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb stable main' >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-unstable --no-install-recommends && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get purge --auto-remove -y curl && \
    rm -rf /src/*.deb

ENTRYPOINT ["cmd-iaso"]
