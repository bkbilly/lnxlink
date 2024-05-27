FROM python:3.9-slim-buster

WORKDIR /opt/lnxlink

COPY . /opt/lnxlink
RUN apt update &&\
    apt install -y gcc git &&\
    rm -rf /var/lib/apt/lists/* &&\
    pip --no-cache-dir install -e /opt/lnxlink

ENTRYPOINT ["/usr/local/bin/lnxlink", "-ie", "active_window,keyboard_hotkeys,media,boot_select,display_env,fullscreen,brightness,mouse,send_keys,screenshot,keep_alive,battery,systemd,speech_recognition,notify,screen_onoff,webcam,idle,power_profile,gpu,audio_select,xdg_open,restart,shutdown,suspend"]
CMD ["-c", "/opt/lnxlink/config/config.yaml"]
