FROM python:3.12-slim-bookworm

WORKDIR /opt/lnxlink

COPY . /opt/lnxlink
RUN apt update &&\
    apt install -y cmake gcc python3-dev libdbus-glib-1-dev libglib2.0-dev libcairo2-dev libgirepository1.0-dev dbus-x11 xdg-utils python3-gi &&\
    rm -rf /var/lib/apt/lists/* &&\
    pip --no-cache-dir install PyGObject dasbus numpy==1.26.4 dbus-networkdevices docker &&\
    pip --no-cache-dir install -e /opt/lnxlink

ENTRYPOINT ["/usr/local/bin/lnxlink", "-ie", "active_window,audio_select,bluetooth,boot_select,brightness,dbus_idle,display_env,fullscreen,gpu,idle,keep_alive,keyboard_hotkeys,media,mouse,notify,power_profile,screen_onoff,screenshot,send_keys,speech_recognition,steam,suspend,xdg_open"]
CMD ["-c", "/opt/lnxlink/config/config.yaml"]
