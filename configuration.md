# 📂 Configuration

## Config file location

Your config file is the file passed to `lnxlink -c`. The installer creates `lnxlink.yaml` in the directory where it was run. You can find the active config path from the systemd service:

{% tabs %}
{% tab title="Desktop" %}
```
cat ~/.config/systemd/user/lnxlink.service | grep -i ExecStart
```
{% endtab %}

{% tab title="Server" %}
```
cat /etc/systemd/system/lnxlink.service | grep -i ExecStart
```
{% endtab %}
{% endtabs %}

## Modules

If both `modules` and `exclude` are empty, all modules are automatically loaded:

```yaml
modules:
exclude:
```

The default template includes an `exclude` list for modules that need extra dependencies, permissions, hardware, or user setup. The easiest way to choose modules is the module selector:

```bash
lnxlink -m -c lnxlink.yaml
```

You can also edit the config manually. All supported modules can be found [here](https://github.com/bkbilly/lnxlink/blob/master/lnxlink/modules) and the configuration should look like this:

```yaml
modules:
- notify
- camera_used
- idle
- keep_alive
- shutdown
- brightness
```

## Custom module

You can create custom modules and import them to your configuration with their full path or a URL. Code examples can be found [here](https://github.com/bkbilly/lnxlink/blob/master/lnxlink/modules).

```yaml
custom_modules:
- /home/user/mytest.py
- https://raw.githubusercontent.com/bkbilly/lnxlink/master/lnxlink/modules/cpu.py
```

## Exclude Modules

In case you have empty modules config which auto loads all the available modules, you can have this option that excludes modules from auto loading:

```yaml
exclude:
- screenshot
- webcam
```

## Extra options

This is the default settings:

```yaml
mqtt:
  # Use "mqtt" for a direct broker connection, "homeassistant_api" to
  # publish/subscribe through the Home Assistant HTTP/WebSocket API, or "auto"
  # to try direct MQTT first and fall back to the Home Assistant API.
  transport: "mqtt"
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
  homeassistant:
    url: ""
    token: ""
    token_env: ""
    token_file: ""
    timeout: 20
    verify_ssl: true
    subscribe_commands: true
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
```

* **MQTT Topic:** This consists of the prefix and the clientId: `/lnxlink/DESKTOP-Linux`**.**
* **MQTT Transport:** `mqtt` connects directly to the broker, `homeassistant_api` publishes and receives MQTT messages through the Home Assistant API, and `auto` tries MQTT first before falling back to the Home Assistant API.
* **MQTT Encryption:** To use a secured MQTT broker, you will have to enable the `tls` option and optionally define the `keyfile`, `certfile`, `ca_certs` files.
* **Discovery Enabled:** It sends the settings for configuring Home Assistant entities.
* **Clear On Off:** Clears mqtt data from broker when stopped.
* **Home Assistant API:** When using `homeassistant_api` or `auto`, set `mqtt.homeassistant.url` and provide a long-lived access token with `token`, `token_env`, or `token_file`.
* **Update Interval:** Sets the interval in seconds for when the sensors are updated.
* **Update on change:** Sends an update to the MQTT broker when a change is detected or every 15 minutes.

### Environmental Options

If the following environment variables are defined, they replace the options from the configuration file:

```bash
LNXLINK_MQTT_PREFIX
LNXLINK_MQTT_CLIENTID
LNXLINK_MQTT_SERVER
LNXLINK_MQTT_PORT
LNXLINK_MQTT_USER
LNXLINK_MQTT_PASS
```
