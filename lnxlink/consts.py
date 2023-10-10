"""Constant variables to use"""

SERVICEHEADLESS = """[Unit]
Description=LNXlink
After=network-online.target

[Service]
Type=simple
Restart=always
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
  discovery:
    enabled: true
  lwt:
    enabled: true
    qos: 1
    retain: true
    connectMsg: 'ON'
    disconnectMsg: 'OFF'
update_interval: 5
modules:
custom_modules:
exclude:
"""
