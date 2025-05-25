FROM python:3.12-slim-bookworm

WORKDIR /opt/lnxlink

COPY . /opt/lnxlink

RUN apt update
RUN apt install -y systemd dbus cmake gcc python3-dev xdg-utils
RUN apt install -y xdotool x11-xserver-utils
RUN rm -rf /var/lib/apt/lists/*

RUN pip --no-cache-dir install docker vdf flask waitress
RUN pip --no-cache-dir install jeepney dbus-mediaplayer dbus-notification dbus-idle
RUN pip --no-cache-dir install ewmh python-xlib xlib-hotkeys
RUN pip --no-cache-dir install nvsmi nvitop
RUN pip --no-cache-dir install -e /opt/lnxlink

ENTRYPOINT ["/usr/local/bin/lnxlink", "-ie", "audio_select,bluetooth,boot_select,keep_alive,power_profile,screen_onoff,screenshot,speech_recognition,webcam,wifi"]
CMD ["-c", "/opt/lnxlink/config/config.yaml"]
