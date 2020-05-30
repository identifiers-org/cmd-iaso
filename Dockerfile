FROM python:3.7-slim-buster

COPY ./LICENSE /app/LICENSE
COPY ./VERSION /app/VERSION
COPY ./setup.py /app/setup.py
COPY ./iaso /app/iaso

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get install -y --no-install-recommends python3-dev && \
    python3 setup.py install && \
    apt-get remove -y python3-dev && \
    apt-get remove -y gcc && \
    apt-get -y autoremove

RUN apt-get install dumb-init

RUN pyppeteer-install

ENTRYPOINT ["dumb-init", "--", "cmd-iaso"]
