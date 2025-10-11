# 📂 Configuration

## Config file location

Your config file is located at the directory you were when you first run LNXlink. This can be anything you write like of the `config.yaml` that I suggested. You can find where it is from the systemd service:

{% tabs %}
{% tab title="Desktop" %}
```
cat ~/.config/systemd/user/lnxlink.service | grep -i ExecStart
```
{% endtab %}

{% tab title="Server" %}
```
cat /etc/systemd/lnxlink.service | grep -i ExecStart
```
{% endtab %}
{% endtabs %}

## Modules

By default all modules are automatically loaded. This happens when the modules section is empty like this:

```yaml
modules:
```

You should select the ones you want to load. All supported modules can be found [here](https://github.com/bkbilly/lnxlink/blob/master/lnxlink/modules) and the configuration should look like this:

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
  prefix: lnxlink
  clientId: DESKTOP-Linux
  server: server
  port: 1883
  clear_on_off: true
  auth:
    user: user
    pass: pass
    tls: false
    keyfile: ''
    certfile: ''
    ca_certs: ''
  discovery:
    enabled: true
    prefix: homeassistant
  lwt:
    enabled: true
    qos: 1
update_interval: 5
update_on_change: false
modules: []
custom_modules: []
exclude: []
settings: []
```

* **MQTT Topic:** This consists of the prefix and the clientId: `/lnxlink/DESKTOP-Linux`**.**
* **MQTT Encryption:** To use a secured MQTT broker, you will have to enable the `tls` option and optionally define the `keyfile`, `certfile`, `ca_certs` files.
* **Discovery Enabled:** It sends the settings for configuring Home Assistant entities.
* **Clear On Off:** Clears mqtt data from broker when stopped.
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
LNXLINK_HASS_URL
LNXLINK_HASS_API
```
