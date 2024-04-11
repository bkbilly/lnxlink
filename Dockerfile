FROM python:3.9-slim-buster

RUN apt update && apt install -y gcc

WORKDIR /opt/lnxlink

COPY . /opt/lnxlink
RUN pip install -e /opt/lnxlink

ENTRYPOINT ["/usr/local/bin/lnxlink", "-ie", "keyboard_hotkeys,media,boot_select,display_env,fullscreen,brightness,mouse,send_keys,screenshot,keep_alive,battery,systemd,speech_recognition,notify,screen_onoff,webcam,idle,power_profile,gpu,audio_select,xdg_open,restart,shutdown,suspend"]
CMD ["-c", "/opt/lnxlink/config/config.yaml"]
