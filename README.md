---
description: Effortlessly manage your Linux machine
---

# 🌩️ LNXlink

<figure><img src=".gitbook/assets/logo.png" alt=""><figcaption></figcaption></figure>

## Welcome

Home Assistant companion app for linux that uses the MQTT integration to get info and control the PC.

## Features

* **Sensors:** Automatically discover sensors that monitor and control the system.
* **Home Assistant:** Uses MQTT Autodiscovery to create entities and shows if update is required.
* **No sudo required:** No need to be root user to install and use, unless used on server setup.
* **Easily expanded:** Any new module is automatically imported and custom modules can be added.

## Supported Modules

The <mark style="color:orange;">Orange</mark> indicate that they need a graphical interface for them to work and the ones in <mark style="color:green;">Green</mark> need or support manual configuration.

| Controls                                                                                                                          | Sensors                                                                |
| --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Shutdown                                                                                                                          | CPU                                                                    |
| Restart                                                                                                                           | RAM                                                                    |
| Suspend                                                                                                                           | GPU                                                                    |
| Boot select                                                                                                                       | Battery                                                                |
| Power Profile                                                                                                                     | Restart required                                                       |
| [Speech Recognition](examples.md#voice-assistant)                                                                                 | Network Speed                                                          |
| [LNXlink Update](examples.md#install-update)                                                                                      | Update required                                                        |
| [<mark style="color:green;">Bash commands</mark>](settings.md#bash)                                                               | Microphone used                                                        |
| [<mark style="color:green;">GPIO</mark>](settings.md#gpio) <mark style="color:green;">(inputs, outputs)</mark>                    | Camera used                                                            |
| [<mark style="color:green;">SystemD</mark>](settings.md#systemd)                                                                  | Gamepad Used                                                           |
| [<mark style="color:orange;">Keyboard Hotkeys</mark>](settings.md#keyboard-hotkeys)                                               | Temperature                                                            |
| [<mark style="color:orange;">Notify</mark>](examples.md#notification)                                                             | WiFi                                                                   |
| [<mark style="color:orange;">Open URL/File</mark>](examples.md#open-a-url-or-file) <mark style="color:orange;">(xdg\_open)</mark> | Webcam show                                                            |
| [<mark style="color:orange;">Send Keys</mark>](examples.md#keys-send)                                                             | Inference Time                                                         |
| <mark style="color:orange;">Mouse control</mark>                                                                                  | [Statistics](examples.md#statistics)                                   |
| [<mark style="color:orange;">Media Controls</mark>](media-player.md)                                                              | [<mark style="color:green;">Disk usage</mark>](settings.md#disk-usage) |
| <mark style="color:orange;">Screen On/Off</mark>                                                                                  | <mark style="color:orange;">Fullscreen</mark>                          |
| <mark style="color:orange;">Audio Select (microphone, speaker)</mark>                                                             | <mark style="color:orange;">Screenshot Show</mark>                     |
| <mark style="color:orange;">Brightness</mark>                                                                                     | <mark style="color:orange;">Display Variable</mark>                    |
| <mark style="color:orange;">Keep Alive</mark>                                                                                     | <mark style="color:orange;">Idle time</mark>                           |

## Supported OS

Only Linux is supported and there is no plan on supporting Windows or MAC because it has many system dependencies that can't be ported. A recommended companion app for windows is [HASS.Agent](https://lab02-research.org/hassagent/) and a cross platform alternative is the [IoTuring](https://github.com/richibrics/IoTuring).
