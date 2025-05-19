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

| Controls                                                                                          | Sensors                                                                         |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| [<mark style="color:blue;">Shutdown</mark>](#user-content-fn-1)[^1]                               | [<mark style="color:blue;">CPU</mark>](#user-content-fn-2)[^2]                  |
| [<mark style="color:blue;">Restart</mark>](#user-content-fn-3)[^3]                                | [<mark style="color:blue;">RAM</mark>](#user-content-fn-4)[^4]                  |
| [<mark style="color:blue;">Suspend</mark>](#user-content-fn-5)[^5]                                | [<mark style="color:blue;">GPU</mark>](#user-content-fn-6)[^6]                  |
| [<mark style="color:blue;">Boot select</mark>](#user-content-fn-7)[^7]                            | [<mark style="color:blue;">Battery</mark>](#user-content-fn-8)[^8]              |
| [<mark style="color:blue;">Power Profile</mark>](#user-content-fn-9)[^9]                          | [<mark style="color:blue;">Restart required</mark>](#user-content-fn-10)[^10]   |
| [<mark style="color:blue;">Speech Recognition</mark>](#user-content-fn-11)[^11]                   | [<mark style="color:blue;">Network Speed</mark>](#user-content-fn-12)[^12]      |
| [<mark style="color:blue;">LNXlink Update</mark>](#user-content-fn-13)[^13]                       | [<mark style="color:blue;">Update required</mark>](#user-content-fn-14)[^14]    |
| [<mark style="color:blue;">Bluetooth</mark>](#user-content-fn-15)[^15]                            | [<mark style="color:blue;">Network Interfaces</mark>](#user-content-fn-16)[^16] |
| [<mark style="color:blue;">WOL</mark>](#user-content-fn-17)[^17]                                  | [<mark style="color:blue;">Microphone used</mark>](#user-content-fn-18)[^18]    |
| [<mark style="color:blue;">Logging Level</mark>](#user-content-fn-19)[^19]                        | [<mark style="color:blue;">Camera used</mark>](#user-content-fn-20)[^20]        |
| [<mark style="color:green;">Bash commands</mark>](#user-content-fn-21)[^21]                       | [<mark style="color:blue;">Gamepad Used</mark>](#user-content-fn-22)[^22]       |
| [<mark style="color:green;">SystemD</mark>](#user-content-fn-23)[^23]                             | [<mark style="color:blue;">Temperature</mark>](#user-content-fn-24)[^24]        |
| [<mark style="color:green;">Docker</mark>](#user-content-fn-25)[^25]                              | [<mark style="color:blue;">WiFi</mark>](#user-content-fn-26)[^26]               |
| [<mark style="color:green;">GPIO (inputs, outputs)</mark>](#user-content-fn-27)[^27]              | [<mark style="color:blue;">Webcam show</mark>](#user-content-fn-28)[^28]        |
| [<mark style="color:green;">IR Remote</mark>](#user-content-fn-29)[^29]                           | [<mark style="color:blue;">Inference Time</mark>](#user-content-fn-30)[^30]     |
| [<mark style="color:orange;">Keyboard Hotkeys</mark>](#user-content-fn-31)[^31]                   | <mark style="color:blue;">Disk IO</mark>                                        |
| [<mark style="color:orange;">Notify</mark>](#user-content-fn-32)[^32]                             | [<mark style="color:green;">RESTful</mark>](#user-content-fn-33)[^33]           |
| [<mark style="color:orange;">Open URL/File</mark>](#user-content-fn-34)[^34]                      | [<mark style="color:green;">Statistics</mark>](#user-content-fn-35)[^35]        |
| [<mark style="color:orange;">Send Keys</mark>](#user-content-fn-36)[^36]                          | [<mark style="color:green;">Disk/Mounts usage</mark>](#user-content-fn-37)[^37] |
| [<mark style="color:orange;">Mouse control</mark>](#user-content-fn-38)[^38]                      | [<mark style="color:orange;">Fullscreen</mark>](#user-content-fn-39)[^39]       |
| [<mark style="color:orange;">Media Controls</mark>](media-player.md)                              | [<mark style="color:orange;">Screenshot Show</mark>](#user-content-fn-40)[^40]  |
| [<mark style="color:orange;">Screen On/Off</mark>](#user-content-fn-41)[^41]                      | [<mark style="color:orange;">Display Variable</mark>](#user-content-fn-42)[^42] |
| [<mark style="color:orange;">Audio Select (microphone, speaker)</mark>](#user-content-fn-43)[^43] | [<mark style="color:orange;">Idle time</mark>](#user-content-fn-44)[^44]        |
| [<mark style="color:orange;">Brightness</mark>](#user-content-fn-45)[^45]                         |                                                                                 |
| [<mark style="color:orange;">Keep Alive</mark>](#user-content-fn-46)[^46]                         |                                                                                 |
| [<mark style="color:orange;">Steam</mark>](#user-content-fn-47)[^47]                              |                                                                                 |

## Supported OS

Only Linux is supported and there is no plan on supporting Windows or MAC because it has many system dependencies that can't be ported. A recommended companion app for windows is [HASS.Agent](https://lab02-research.org/hassagent/) and a cross platform alternative is the [IoTuring](https://github.com/richibrics/IoTuring).

[^1]: ## 🔴 Shutdown

    Creates a button that shuts down the computer.

[^2]: ## 🖥️ CPU

[^3]: ## ⚪ Restart

    Creates a button that restarts the computer.

[^4]: ## 🧠 RAM

[^5]: ## 💤 Suspend

    Creates a button that puts the computer to sleep mode.

[^6]: ## 🎮 GPU

[^7]: ## 🚀 Boot Select

    Creates a select entity that lets you choose which OS to boot on the next restart.

[^8]: ## 🔋 Battery

[^9]: ## ⚡ Power Profile

    Creates a select entity with all the available power profiles.

[^10]: ## 🛠️ Restart Required



[^11]: ## 🗣️ Speech Recognition

    Listens to the user's input and sends the response as an attribute to the binary sensor of speech recognition entity

    [Usage](examples.md#voice-assistant)

[^12]: ## 📶 Network Speed

[^13]: ## 🔧 Update

    Forces the LNXlink to update to the latest version. This supports installations via System or Development.

[^14]: ## 🔄 Update Required

[^15]: ## 📳 Bluetooth

    Creates two types of switches:

    1. A **Bluetooth Power** switch that enables and disables the Bluetooth on the computer
    2. A **Bluetooth Device** switch for each connected device that disconnects and connects to the device.

    These are auto-discovered even when the app is running.

[^16]: ## 🌐 Network Interfaces

[^17]: ## Wake On LAN

    Creates a switch for all network interfaces that support WOL and it can control if it is turned ON or OFF.

[^18]: ## 🎤 Microphone Used

[^19]: ## 📝 Logging Level

    Creates a select entity that lets the user select the debug type while running.

    Very useful for debugging an issue.

[^20]: ## 🎥 Camera Used



[^21]: ## 🐚 Bash

    One of the most powerful modules that let's you easily create any type of sensor:

    * sensors

    - binary\_sensors
    - buttons
    - switches

    [Usage](modules-settings.md#bash)

[^22]: ## 🎮 Gamepad Used

[^23]: ## ♻️ SystemD



    [Usage](modules-settings.md#systemd)

[^24]: ## 🌡️ Temperature

[^25]: ## 📦 Docker



    [Usage](modules-settings.md#docker)

[^26]: ## 📶 WiFi

[^27]: ## 🧲 GPIO



    [Usage](modules-settings.md#gpio)

[^28]: ## 📷 Webcam Show



[^29]: ## 🛰️ IR Remote



    [Usage](modules-settings.md#ir-remote)

[^30]: ## 📈 Inference Time

[^31]: ## ⌨️ Keyboard Hotkeys



    [Usage](modules-settings.md#keyboard-hotkeys)

[^32]: ## 📡 Notify



    [Usage](examples.md#notification)

[^33]: ## 📮 RESTful



    [Usage](examples.md#restful)

[^34]: ## 📁 Open URL/File

    Uses xdg\_open to open files.

    [Usage](examples.md#open-a-url-or-file)

[^35]: ## 📊 Statistics



    [Usage](examples.md#statistics)

[^36]: ## 🔑 Send Keys



    [Usage](examples.md#keys-send)

[^37]: ## 💽 Disk Usage



    [Usage](modules-settings.md#disk-usage)

[^38]: ## 🖱️ Mouse Control

[^39]: ## 🖼️ Fullscreen

[^40]:

[^41]: ## 💡 Screen On/Off

[^42]: ## 📺 Display Variable

[^43]: ## 🎧 Audio Select

[^44]: ## 🧭 Idle Time

[^45]: ## 🌞 Brightness

[^46]: ## 🚥 Keep Alive



[^47]: ## 🔥 Steam
