# ============================= DOCKER COMMANDS ============================= #
#                                                                             #
# BUILD: docker build --tag cmd-iaso:VERSION .                                #
#                                                                             #
# RUN: docker run -it --net=host cmd-iaso:VERSION                             #
#                                                                             #
# CURATE: docker run -it --net=host --mount \                                 #
#         type=bind,source=FILEPATH,target=/root/upload/FILENAME \            #
#         cmd-iaso:VERSION curate /root/upload/FILENAME                       #
#                                                                             #
# START: docker start cmd-iaso:VERSION                                        #
#                                                                             #
# TODO : docker exec COMMAND (TODO check net and mount arg)                   #
#                                                                             #
# STOP: docker stop cmd-iaso:VERSION                                          #
#                                                                             #
# ============================= DOCKER COMMANDS ============================= #

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

RUN pyppeteer-install

ENTRYPOINT ["cmd-iaso"]
