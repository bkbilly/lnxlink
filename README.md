# LNX Link
LNX Link is a Linux service for integrating your system with an external application like Home Assistant using MQTT.
It is inspired by [IOT Link](https://iotlink.gitlab.io/).

# Features
 - **System control:** Shutdown, Send Keys, Notify, Media.
 - **System monitor:** CPU, Ram, Network, Media.
 - **No sudo required:** No need to be root user to install and use.
 - **Easily expanded:** Any new module is automatically imported as long as it meets the required format.

# Installation
One command install:
```shell
bash <(curl -s "https://raw.githubusercontent.com/bkbilly/lnxlink/master/install.sh")
```
Edit the configuration /opt/lnxlink/config.yaml and restart the service with the use of systemctl:
```shell
systemctl --user restart lnxlink.service
```

# Commands
  - **Shutdown System**
    - **Topic:** {prefix}/{clientId}/commands/shutdown
  - **Send Keys**
    - **Topic:** {prefix}/{clientId}/commands/send-keys
    - **Payload Type:** List or String
    - **Payload:** Each string can contain special keys '<ALT>+<CTRL>+<DELTE>', '<CTRL>+c'
  - **Notify**
    - **Topic:** {prefix}/{clientId}/commands/notify
    - **Payload Type:** JSON
    - **Payload:**
      - **title:** String
      - **message:** String
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
