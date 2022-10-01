<img align="right" width="170" height="100" src="https://github.com/bkbilly/lnxlink/blob/master/logo.png?raw=true">

# LNX link
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE.md)
[![OS - Linux](https://img.shields.io/badge/OS-Linux-blue?logo=linux&logoColor=white)]()
[![Python 3.5](https://img.shields.io/badge/Python-3.5-blue?logo=python&logoColor=white)]()
[![Last commit](https://img.shields.io/github/last-commit/bkbilly/lnxlink?color=blue&logo=github&logoColor=white)]()



This is a Linux service for integrating your system with an external application like Home Assistant using MQTT.
It is inspired by [IOT Link](https://iotlink.gitlab.io/).

# Features
 - **System control:** Shutdown, Restart, Send Keys, Notify, Media.
 - **System monitor:** CPU, Ram, Network, Media, Microphone is used.
 - **No sudo required:** No need to be root user to install and use.
 - **Easily expanded:** Any new module is automatically imported as long as it meets the required format.

# Installation
One command install and update:
```shell
bash <(curl -s "https://raw.githubusercontent.com/bkbilly/lnxlink/master/install.sh")
```
You can manually update the configuration file `/opt/lnxlink/config.yaml` and restart the service with the use of systemctl:
```shell
systemctl --user restart lnxlink.service
```

# Home Assistant integration
LNX Link is using MQTT Autodiscovery to create entities to the frontend.

Supported entities:
  - button.shutdown
  - button.restart
  - sensor.cpu_usage
  - sensor.memory_usage
  - sensor.network_download
  - sensor.network_upload
  - sensor.microphone_used

Unsupported entities that need manual configuration:
  - media (check this: [mqtt-mediaplayer](https://github.com/bkbilly/hass-mqtt-mediaplayer))
  - notify
  - send-keys

# Examples

Send a notification with an image as a preview:
```yaml
service: mqtt.publish
data:
  topic: {prefix}/{clientId}/commands/notify
  payload: >-
    { "title": "Notification Title",
      "message": "Testing notification",
      "iconUrl": "http://hass.local:8123/local/myimage.jpg" }
```

Send a series of keys:
```yaml
service: mqtt.publish
data:
  topic: {prefix}/{clientId}/commands/send-keys
  payload: "<CTRL>+t"
```

<details>
  <summary>Technical Notes (click to expand)</summary>

# Commands
  - **Shutdown System**
    - **Topic:** {prefix}/{clientId}/commands/shutdown
  - **Restart System**
    - **Topic:** {prefix}/{clientId}/commands/restart
  - **Send Keys**
    - **Topic:** {prefix}/{clientId}/commands/send-keys
    - **Payload Type:** List or String
    - **Payload:** Each string can contain special keys '\<ALT>+\<CTRL>+\<DELTE>', '\<CTRL>+c'
  - **Notify**
    - **Topic:** {prefix}/{clientId}/commands/notify
    - **Payload Type:** JSON
    - **Payload:**
      - **title:** String
      - **message:** String
      - **iconUrl:** String
  - **Media**
    - **Topic:** {prefix}/{clientId}/commands/media/{media_action}
    - **media_action:**
      - **volume_set:** payload is integer or float with values 0-1 or 0-100
      - **playpause**
      - **previous**
      - **next**

# Monitoring
  - **Power status**
    - **Topic:** {prefix}/{clientId}/lwt
    - **Payload Type:** ON/OFF {connectMsg}/{disconnectMsg}
  - **CPU**
    - **Topic:** {prefix}/{clientId}/{statsPrefix}/cpu/usage
    - **Payload Type:** Integer
  - **Memory RAM**
    - **Topic:** {prefix}/{clientId}/{statsPrefix}/memory/usage
    - **Payload Type:** Integer
  - **Network**
    - **Topic:** {prefix}/{clientId}/{statsPrefix}/network/0/speed
    - **Payload Type:** JSON Mbps
    - **Example:**: {"download": 0.8, "upload": 0.1}
  - **Media**
    - **Topic:** {prefix}/{clientId}/{statsPrefix}/media/info
    - **Payload Type:** JSON
    - **Example:**: {"title": "Hakuna Matata", "artist": "disney", "album": "", "status": "playing", "volume": 51, "playing": true}

# Expanding
To expand the supported features, create a new python file on **modules** folder and use this template:
```python
class Addon():
    service = 'example'
    name = 'Example'

    def startControl(self, topic, data):
        ''' topic is a list with all topics after commands '''
        print(topic, data)

    def getInfo(self):
        ''' Returns any type that can be converted to JSON '''
        return 15
```
</details>
