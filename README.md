[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE.md)
[![OS - Linux](https://img.shields.io/badge/OS-Linux-blue?logo=linux&logoColor=white)]()
[![Python 3.5](https://img.shields.io/badge/Python-3.5-blue?logo=python&logoColor=white)]()
[![Last commit](https://img.shields.io/github/last-commit/bkbilly/lnxlink?color=blue&logo=github&logoColor=white)]()

<img align="right" width="170" height="100" src="https://github.com/bkbilly/lnxlink/blob/master/logo.png?raw=true">

# LNX link
This is a Linux service for integrating your system with an external application like Home Assistant using MQTT.
It is inspired by [IOT Link](https://iotlink.gitlab.io/).

# Features
 - **System control:** Shutdown, Restart, Send Keys, Notify, Media.
 - **System monitor:** CPU, Ram, Network, Media, Microphone, Idle.
 - **Home Assistant:** Uses MQTT Autodiscovery to create entities.
 - **No sudo required:** No need to be root user to install and use.
 - **Easily expanded:** Any new module is automatically imported.

# Installation
One command install and update:
```shell
bash <(curl -s "https://raw.githubusercontent.com/bkbilly/lnxlink/master/install.sh")
```
You can manually update the configuration file `/opt/lnxlink/config.yaml` and restart the service with the use of systemctl:
```shell
systemctl --user restart lnxlink.service
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
  topic: {prefix}/{clientId}/commands/send-keys
  payload: "<CTRL>+t"
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






<details>

# Expanding
To expand the supported features, create a new python file on **modules** folder and use this template:
```python
class Addon():
    service = 'example'
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
