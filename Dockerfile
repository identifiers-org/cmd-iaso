FROM python:3.7-slim-buster

COPY . /app

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get install -y --no-install-recommends python3-dev && \
    python3 setup.py install && \
    apt-get remove -y python3-dev && \
    apt-get remove -y gcc && \
    apt-get -y autoremove

ENTRYPOINT ["cmd-iaso"]

# docker build --tag cmd-iaso:0.0.0 .
# docker run --net=host cmd-iaso:0.0.0 curate datamine.json --controller chrome --navigator terminal --informant terminal --chrome localhost:9222
