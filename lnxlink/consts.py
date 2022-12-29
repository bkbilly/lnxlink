service_headless = """[Unit]
Description=LNXLink
After=network-online.target

[Service]
Type=simple
Restart=always
User=root

ExecStart={exec_cmd}

[Install]
WantedBy=default.target
"""

service_user = """[Unit]
Description=LNXLink
After=network-online.target multi-user.target graphical.target
PartOf=graphical-session.target
 
[Service]
Type=simple
Restart=always

ExecStart={exec_cmd}
 
[Install]
WantedBy=default.target
"""

config_temp = """
mqtt:
  prefix: 'lnxlink'
  clientId: 'DESKTOP-Linux'
  statsPrefix: 'monitor/stats'
  server: '192.168.1.1'
  port: 1883
  auth:
    user: 'user'
    pass: 'pass'
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
- shutdown
- restart
- send_keys
- notify
- cpu
- memory
- network_upload
- network_download
- media
- microphone
- idle
- bluetooth_battery
- screen_onoff
- suspend
- keep_alive
- xdg_open
- bash
"""
