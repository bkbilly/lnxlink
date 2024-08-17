---
description: Effortlessly manage your Linux machine
---

# 🌩️ LNXlink

<figure><img src=".gitbook/assets/logo.png" alt="" width="256"><figcaption></figcaption></figure>

## Welcome

Home Assistant companion app for linux that uses the MQTT integration to get info and control the PC.

## Features

* **Sensors:** Automatically discover sensors that monitor and control the system.
* **Home Assistant:** Uses MQTT Autodiscovery to create entities and shows if update is required.
* **No sudo required:** No need to be root user to install and use, unless used on server setup.
* **Easily expanded:** Any new module is automatically imported and custom modules can be added.

## Supported Modules

The <mark style="color:orange;">Orange</mark> indicate that they need a graphical interface for them to work and the ones in <mark style="color:green;">Green</mark> need or support manual configuration.

| Controls                                                                                                                          | Sensors                                                                               |
| --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| <mark style="color:blue;">Shutdown</mark>                                                                                         | <mark style="color:blue;">CPU</mark>                                                  |
| <mark style="color:blue;">Restart</mark>                                                                                          | <mark style="color:blue;">RAM</mark>                                                  |
| <mark style="color:blue;">Suspend</mark>                                                                                          | <mark style="color:blue;">GPU</mark>                                                  |
| <mark style="color:blue;">Boot select</mark>                                                                                      | <mark style="color:blue;">Battery</mark>                                              |
| <mark style="color:blue;">Power Profile</mark>                                                                                    | <mark style="color:blue;">Restart required</mark>                                     |
| [<mark style="color:blue;">Speech Recognition</mark>](examples.md#voice-assistant)                                                | <mark style="color:blue;">Network Speed</mark>                                        |
| [<mark style="color:blue;">LNXlink Update</mark>](examples.md#install-update)                                                     | <mark style="color:blue;">Update required</mark>                                      |
| <mark style="color:blue;">Bluetooth</mark>                                                                                        | <mark style="color:blue;">Network Interfaces</mark>                                   |
| [<mark style="color:green;">Bash commands</mark>](modules-settings.md#bash)                                                       | <mark style="color:blue;">Microphone used</mark>                                      |
| [<mark style="color:green;">SystemD</mark>](modules-settings.md#systemd)                                                          | <mark style="color:blue;">Camera used</mark>                                          |
| [<mark style="color:green;">Docker</mark>](modules-settings.md#docker)                                                            | <mark style="color:blue;">Gamepad Used</mark>                                         |
| [<mark style="color:green;">GPIO</mark>](modules-settings.md#gpio) <mark style="color:green;">(inputs, outputs)</mark>            | <mark style="color:blue;">Temperature</mark>                                          |
| [<mark style="color:green;">IR Remote</mark>](modules-settings.md#ir-remote)                                                      | <mark style="color:blue;">WiFi</mark>                                                 |
| [<mark style="color:orange;">Keyboard Hotkeys</mark>](modules-settings.md#keyboard-hotkeys)                                       | <mark style="color:blue;">Webcam show</mark>                                          |
| [<mark style="color:orange;">Notify</mark>](examples.md#notification)                                                             | <mark style="color:blue;">Inference Time</mark>                                       |
| [<mark style="color:orange;">Open URL/File</mark>](examples.md#open-a-url-or-file) <mark style="color:orange;">(xdg\_open)</mark> | [<mark style="color:green;">Statistics</mark>](examples.md#statistics)                |
| [<mark style="color:orange;">Send Keys</mark>](examples.md#keys-send)                                                             | [<mark style="color:green;">Disk/Mounts usage</mark>](modules-settings.md#disk-usage) |
| <mark style="color:orange;">Mouse control</mark>                                                                                  | <mark style="color:orange;">Fullscreen</mark>                                         |
| [<mark style="color:orange;">Media Controls</mark>](media-player.md)                                                              | <mark style="color:orange;">Screenshot Show</mark>                                    |
| <mark style="color:orange;">Screen On/Off</mark>                                                                                  | <mark style="color:orange;">Display Variable</mark>                                   |
| <mark style="color:orange;">Audio Select (microphone, speaker)</mark>                                                             | <mark style="color:orange;">Idle time</mark>                                          |
| <mark style="color:orange;">Brightness</mark>                                                                                     |                                                                                       |
| <mark style="color:orange;">Keep Alive</mark>                                                                                     |                                                                                       |

## Supported OS

Only Linux is supported and there is no plan on supporting Windows or MAC because it has many system dependencies that can't be ported. A recommended companion app for windows is [HASS.Agent](https://lab02-research.org/hassagent/) and a cross platform alternative is the [IoTuring](https://github.com/richibrics/IoTuring).
