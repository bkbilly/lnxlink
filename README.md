[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE.md)
[![OS - Linux](https://img.shields.io/badge/OS-Linux-blue?logo=linux&logoColor=white)]()
[![Python 3.5](https://img.shields.io/badge/Python-3.5-blue?logo=python&logoColor=white)]()
[![PyPI](https://img.shields.io/pypi/v/lnxlink?logo=pypi&logoColor=white)](https://pypi.python.org/pypi/lnxlink/)
[![Last commit](https://img.shields.io/github/last-commit/bkbilly/lnxlink?color=blue&logo=github&logoColor=white)]()

<img align="right" width="170" height="100" src="https://github.com/bkbilly/lnxlink/blob/master/logo.png?raw=true">

# LNXlink
This is a Linux companion app for integrating your system with an external application like Home Assistant using MQTT.
It's very usefull for remote controling a linux PC, receiving notifications and monitoring it's stats.

# Table of contents

 * [Features](#features)
 * [Installation](#installation)
 * [Headless Installation](#headless-installation)
 * [Examples](#examples)
 * [FAQ](#faq)


# Features
 - **System control:** Shutdown, Restart, Suspend, Send Keys, Notify, Media, Screen On/Off, open URL/File, bash, Keep Alive, Brightness, Boot select.
 - **System monitor:** CPU, Ram, Network, Media, Microphone, Idle, Battery, Disk usage, Required restart, Nvidia GPU, Camera, Memory, Update required, System updates, Webcam, Screenshot.
 - **Home Assistant:** Uses MQTT Autodiscovery to create entities and shows if update is required.
 - **No sudo required:** No need to be root user to install and use, unless used on server setup.
 - **Easily expanded:** Any new module is automatically imported and custom modules can be added.

# Installation
Install or update:
```shell
# For debian based distros:
sudo apt install patchelf meson libdbus-glib-1-dev libglib2.0-dev libasound2-dev python3-pip xdotool xprintidle xdg-utils
# For Red Hat based distros:
sudo dnf install python39-pip.noarch gcc cmake dbus-devel glib2-devel python39-devel alsa-lib-devel
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
sudo apt install patchelf meson libdbus-glib-1-dev libglib2.0-dev libasound2-dev python3-pip
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

### Send a command:
```yaml
service: mqtt.publish
data:
  topic: {prefix}/{clientId}/commands/bash
  payload: "ctrl+shift+t"
```

### Send a series of keys:
```yaml
service: mqtt.publish
data:
  topic: {prefix}/{clientId}/commands/send_keys
  payload: "ctrl+f H e l l o space W o r l d"
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

Supports playing remote or local media using `cvlc` which should be installed.
 - Text To Speach
```yaml
service: tts.google_say
data:
  entity_id: media_player.desktop_linux
  message: Hello world!
```
 - Play Media
```yaml
service: media_player.play_media
data:
  media_content_id: /home/user/imag.jpg
  media_content_type: media  # Not used, but required by home assistant
target:
  entity_id: media_player.desktop_linux
```
 - Camera Play Stream
```yaml
service: camera.play_stream
data:
  media_player: media_player.desktop_linux
target:
  entity_id: camera.demo_camera
```

### Create a custom module
You can create custom modules and import them to your configuration with their full path. Check out examples [here](lnxlink/modules) and this is an example of how to add the `mytest` module to your configuration.
```yaml
modules:
- /home/user/mytest.py
```


# FAQ
## Windows compatibility
Only Linux is supported and there is no plan on supporting Windows. A recomended companion app for windows is [HASS.Agent](https://github.com/LAB02-Research/HASS.Agent).

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

## One of my integration is not working
By default all modules are automatically loaded. This happens when the modules section is empty like this:
```yaml
modules:
```
You should select the ones you want to load. All supported modules can be found [here](lnxlink/modules) and the configuration should look like this:
```yaml
modules:
- notify
- camera_used
- idle
- keep_alive
- shutdown
- brightness
```

## LNXlink doesn't become unavailable after shutdown
Just before LNXlink stops, it sends to MQTT an OFF command, but sometimes it doesn't stop gracefouly.
To fix this, you will have to create an automation on Home Assistant which checks for when was the last time one of the sensors got a value and if it exceeds it sends the OFF command to the MQTT server.

This is an example of the automation which checks events for the idle sensor:
```yaml
alias: lnxlink powered down
description: ""
mode: single
trigger:
  - platform: template
    value_template: >-
      {{ (now() | as_timestamp -
      states.sensor.desktop_linux_idle.last_changed | as_timestamp) >
      10 }}
condition: []
action:
  - service: mqtt.publish
    data:
      qos: 0
      retain: true
      topic: lnxlink/desktop-linux/lwt
      payload: "OFF"
```

## Use Boot Select addon
This control needs to run as root, but it's not recomended to run lnxlink as a super user. To fix this, you need to allow the command `grub-reboot` to run without asking for password:
```bash
# Edit the sudoers file:
sudo visudo
# Add this line at the end (replace USER with your username):
USER ALL=(ALL) NOPASSWD: /usr/sbin/grub-reboot
```

## How to help the development
In case you have found the solution to a bug or you want to create a new feature, follow these instructions to get you started:
```bash
# Install system dependencies
sudo apt install git patchelf meson libdbus-glib-1-dev libglib2.0-dev libasound2-dev python3-pip
# Fork my repository and then download it
git clone git@github.com:<yourusername>/lnxlink.git
# Install lnxlink as editable package
cd lnxlink
pip3 install -e .
# Run it manually
lnxlink -c config.yaml
```
