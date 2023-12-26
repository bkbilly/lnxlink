---
description: Effortlessly manage your Linux machine
---

# 🌩 LNXlink

<figure><img src=".gitbook/assets/logo.png" alt=""><figcaption></figcaption></figure>

## Welcome

Home Assistant companion app for linux that uses the MQTT integration to get info and control the PC.

## Features

* **Sensors:** Automatically discover sensors that monitor and control the system.
* **Home Assistant:** Uses MQTT Autodiscovery to create entities and shows if update is required.
* **No sudo required:** No need to be root user to install and use, unless used on server setup.
* **Easily expanded:** Any new module is automatically imported and custom modules can be added.

## Supported Modules

| Sensors          | Controls                           |
| ---------------- | ---------------------------------- |
| CPU              | Shutdown                           |
| RAM              | Restart                            |
| GPU              | Suspend                            |
| Network Speed    | Notify                             |
| Media info       | Media Controls                     |
| Microphone used  | Send Keys                          |
| Camera used      | Mouse control                      |
| Idle time        | Screen On/Off                      |
| Battery          | Open URL/File                      |
| Disk usage       | Bash commands                      |
| Restart required | Keep Alive                         |
| Update required  | Brightness                         |
| Webcam           | Boot select                        |
| Screenshot       | Power Profile                      |
| Full Screen      | Speech Recognition                 |
| Inference Time   | Audio Select (microphone, speaker) |
| Display Variable | SystemD                            |

## Supported OS

Only Linux is supported and there is no plan on supporting Windows or MAC because it has many system dependencies that can't be ported. A recommended companion app for windows is [HASS.Agent](https://lab02-research.org/hassagent/).
