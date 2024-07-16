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

3rd party custom modules:

* [GPU nvidia-settings](https://github.com/PW999/lnxlink\_gpu\_nvidia\_settings)
* [AM2302 Temperature and Humidity](https://github.com/bkbilly/lnxlink/discussions/81)

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
  auth:
    user: user
    pass: pass
    tls: false
    keyfile: ''
    certfile: ''
    ca_certs: ''
  discovery:
    enabled: true
  lwt:
    enabled: true
    qos: 1
    retain: false
update_interval: 5
update_on_change: false
```

* **MQTT Topic:** This consists of the prefix and the clientId: `/lnxlink/DESKTOP-Linux`**.**
* **MQTT Encryption:** To use a secured MQTT broker, you will have to enable the `tls` option and optionally define the `keyfile`, `certfile`, `ca_certs` files.
* **Discovery Enabled:** It sends the settings for configuring Home Assistant entities.
* **Retain:** Keeps the values of entities on MQTT broker.
* **Update Interval:** Sets the interval in seconds for when the sensors are updated.
* **Update on change:** Sends an update to the MQTT broker when a change is detected or every 15 minutes.
