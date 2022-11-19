[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE.md)
[![OS - Linux](https://img.shields.io/badge/OS-Linux-blue?logo=linux&logoColor=white)]()
[![Python 3.5](https://img.shields.io/badge/Python-3.5-blue?logo=python&logoColor=white)]()
[![PyPI](https://img.shields.io/pypi/v/lnxlink?logo=pypi&logoColor=white)](https://pypi.python.org/pypi/lnxlink/)
[![Last commit](https://img.shields.io/github/last-commit/bkbilly/lnxlink?color=blue&logo=github&logoColor=white)]()

<img align="right" width="170" height="100" src="https://github.com/bkbilly/lnxlink/blob/master/logo.png?raw=true">

# LNX link
This is a Linux service for integrating your system with an external application like Home Assistant using MQTT.
It is inspired by [IOT Link](https://iotlink.gitlab.io/).

# Features
 - **System control:** Shutdown, Restart, Send Keys, Notify, Media, Screen On/Off, open URL/File, bash.
 - **System monitor:** CPU, Ram, Network, Media, Microphone, Idle, Bluetooth battery.
 - **Home Assistant:** Uses MQTT Autodiscovery to create entities.
 - **No sudo required:** No need to be root user to install and use, unless used on server setup.
 - **Easily expanded:** Any new module is automatically imported.

# Installation
Install or update:
```shell
sudo apt install patchelf meson libdbus-glib-1-dev libglib2.0-dev libasound2-dev
pip3 install -U lnxlink
# When asked, it's recommended to install as a user service.
lnxlink -c config.yaml
```

You can manually update the configuration file `config.yaml` and restart the service with the use of systemctl:
```shell
systemctl --user restart lnxlink.service
```

# Headless Installation
The headless installation is used for linux environments that don't use a Graphical Interface like servers.
```shell
sudo apt install patchelf meson libdbus-glib-1-dev libglib2.0-dev libasound2-dev
sudo pip3 install -U lnxlink
# When asked, it's recommended to answer false on install as a user service.
sudo lnxlink -c config.yaml
```
Some modules depend on graphical interface, so if you choose to use this option for installation, you will have to find which ones stop lnxlink from starting and remove them from the config file.
```shell
sudo systemctl restart lnxlink.service
```


# Examples

### Send a notification with an image as a preview:
```yaml
service: mqtt.publish
data:
  topic: {prefix}/{clientId}/commands/notify
  payload: >-
    { "title": "Notification Title",
      "message": "Testing notification",
      "iconUrl": "http://hass.local:8123/local/myimage.jpg" }
```

### Send a series of keys:
```yaml
service: mqtt.publish
data:
  topic: {prefix}/{clientId}/commands/send_keys
  payload: "<CTRL>+t"
```

### Send a command:
```yaml
service: mqtt.publish
data:
  topic: {prefix}/{clientId}/commands/bash
  payload: "xdotool key ctrl+t"
```

### Open a URL or a File
```yaml
service: mqtt.publish
data:
  topic: lnxlink/desktop-linux/commands/xdg_open
  payload: "https://www.google.com"  # or "myimg.jpeg" for file
```

### Combine with [Wake on Lan](https://www.home-assistant.io/integrations/wake_on_lan/) to control your PC with one switch:
```yaml
switch:
  - platform: template
    switches:
      my_pc:
        friendly_name: "My PC"
        unique_id: my_pc
        value_template: "{{ not is_state('button.shutdown', 'unavailable') }}"
        turn_on:
          service: switch.turn_on
          data:
            entity_id: switch.pc_wol
        turn_off:
          service: button.press
          data:
            entity_id: button.shutdown
```

### Create a media player using [mqtt-mediaplayer](https://github.com/bkbilly/hass-mqtt-mediaplayer) using the information collected from the media sensor:

![image](https://user-images.githubusercontent.com/518494/193397441-f18bb5fa-de37-4d95-9158-32cd81b31c72.png)


# FAQ
## Config file location
Your config file is located at the directory you were when you first run lnxlink. This can be anything you write instead of the `config.yaml` that I suggested. You can find where it is from the systemd service:
```shell
cat ~/.config/systemd/user/lnxlink.service  | grep -i ExecStart
```

## Reinitiate systemd service
If you want to create the service from scratch, you will have to disable the running service and start lnxlink again:
```shell
systemctl --user disable lnxlink.service
lnxlink -c config.yaml
```

## Idle time not working
Idle time module is dependend on [idle-time](https://pypi.org/project/idle-time/) which only supports __Gnome Mutter__ for now.
If you want support for this, you can install the newest version from my github:
```shell
pip3 uninstall idle_time
pip3 install 'idle_time @ git+https://github.com/bkbilly/idle_time.git'
systemctl --user restart lnxlink.service
```



<details><summary>Technical Notes (click to expand)</summary>

# Creating new senosr
To expand the supported features, create a new python file on **modules** folder and use this template:
```python
class Addon():
    name = 'Example'
    icon = 'mdi:home-assistant'
    unit = ''

    def startControl(self, topic, data):
        ''' When a command is sent, it will run this method '''
        print(topic, data)

    def getInfo(self):
        ''' Returns any type that can be converted to JSON '''
        return 15

    def exposedControls(self):
        ''' Optional method which exposes an entity '''
        return {
            "mybutton": {
                "type": "button",
                "icon": "mdi:button-cursor",
            }
        }
```

</details>
