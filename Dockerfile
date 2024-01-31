FROM ubuntu:20.04 as build
WORKDIR /opt/lnxlink

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update
RUN apt install -y libdbus-glib-1-dev libcairo2-dev libgirepository1.0-dev libglib2.0-dev
RUN apt install -y libasound2-dev upower xdotool xdg-utils python3-pyaudio

RUN apt install -y python3-pip
RUN pip install -U pip

COPY . /opt/lnxlink
RUN pip3 install -e /opt/lnxlink

ENTRYPOINT ["/usr/local/bin/lnxlink", "-ic", "/opt/lnxlink/config.yaml"]
