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
- bash
- bluetooth_battery
- cpu
- disk_usage
- idle
- keep_alive
- media
- memory
- microphone
- network_download
- network_upload
- notify
- nvidia_gpu
- required_restart
- restart
- screen_onoff
- send_keys
- shutdown
- suspend
- update
- xdg_open
"""
