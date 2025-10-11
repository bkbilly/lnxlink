"""Constant variables to use"""

SERVICEHEADLESS = """[Unit]
Description=LNXlink
After=network-online.target

[Service]
Type=simple
Restart=always
RestartSec=5
User=root

ExecStart={exec_cmd}

[Install]
WantedBy=default.target
"""

SERVICEUSER = """[Unit]
Description=LNXlink
After=network-online.target multi-user.target graphical.target
PartOf=graphical-session.target

[Service]
Type=simple
Restart=always
RestartSec=5

ExecStart={exec_cmd}

[Install]
WantedBy=default.target
"""

CONFIGTEMP = """
mqtt:
  prefix: 'lnxlink'
  clientId: 'DESKTOP-Linux'
  server: '192.168.1.1'
  port: 1883
  auth:
    user: 'user'
    pass: 'pass'
    tls: false
    keyfile: ""
    certfile: ""
    ca_certs: ""
  discovery:
    enabled: true
    prefix: "homeassistant"
  lwt:
    enabled: true
    qos: 1
  clear_on_off: true
update_interval: 5
update_on_change: false
modules:
custom_modules:
exclude:
  - audio_select
  - battery
  - beacondb
  - boot_select
  - brightness
  - fullscreen
  - gpio
  - gpu
  - idle
  - inference_time
  - ir_remote
  - keep_alive
  - keyboard_hotkeys
  - media
  - mouse
  - notify
  - power_profile
  - restful
  - screen_onoff
  - screenshot
  - send_keys
  - speech_recognition
  - systemd
  - webcam
  - xdg_open
settings:
  statistics: "https://analyzer.bkbilly.workers.dev"
"""
