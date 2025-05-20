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

<table><thead><tr><th width="360">Controls</th><th>Sensors</th></tr></thead><tbody><tr><td><a data-footnote-ref href="#user-content-fn-1"><mark style="color:blue;">Shutdown</mark></a></td><td><a data-footnote-ref href="#user-content-fn-2"><mark style="color:blue;">CPU</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-3"><mark style="color:blue;">Restart</mark></a></td><td><a data-footnote-ref href="#user-content-fn-4"><mark style="color:blue;">RAM</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-5"><mark style="color:blue;">Suspend</mark></a></td><td><a data-footnote-ref href="#user-content-fn-6"><mark style="color:blue;">GPU</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-7"><mark style="color:blue;">Boot select</mark></a></td><td><a data-footnote-ref href="#user-content-fn-8"><mark style="color:blue;">Battery</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-9"><mark style="color:blue;">Power Profile</mark></a></td><td><a data-footnote-ref href="#user-content-fn-10"><mark style="color:blue;">Restart required</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-11"><mark style="color:blue;">Speech Recognition</mark></a></td><td><a data-footnote-ref href="#user-content-fn-12"><mark style="color:blue;">Network Speed</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-13"><mark style="color:blue;">LNXlink Update</mark></a></td><td><a data-footnote-ref href="#user-content-fn-14"><mark style="color:blue;">System Updates</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-15"><mark style="color:blue;">Bluetooth</mark></a></td><td><a data-footnote-ref href="#user-content-fn-16"><mark style="color:blue;">Interfaces</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-17"><mark style="color:blue;">WOL</mark></a></td><td><a data-footnote-ref href="#user-content-fn-18"><mark style="color:blue;">Microphone used</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-19"><mark style="color:blue;">Logging Level</mark></a></td><td><a data-footnote-ref href="#user-content-fn-20"><mark style="color:blue;">Camera used</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-21"><mark style="color:green;">Bash commands</mark></a></td><td><a data-footnote-ref href="#user-content-fn-22"><mark style="color:blue;">Gamepad Used</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-23"><mark style="color:green;">SystemD</mark></a></td><td><a data-footnote-ref href="#user-content-fn-24"><mark style="color:blue;">Temperature</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-25"><mark style="color:green;">Docker</mark></a></td><td><a data-footnote-ref href="#user-content-fn-26"><mark style="color:blue;">WiFi</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-27"><mark style="color:green;">GPIO</mark></a></td><td><a data-footnote-ref href="#user-content-fn-28"><mark style="color:blue;">Webcam show</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-29"><mark style="color:green;">IR Remote</mark></a></td><td><a data-footnote-ref href="#user-content-fn-30"><mark style="color:blue;">Inference Time</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-31"><mark style="color:orange;">Keyboard Hotkeys</mark></a></td><td><a data-footnote-ref href="#user-content-fn-32"><mark style="color:blue;">Disk IO</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-33"><mark style="color:orange;">Notify</mark></a></td><td><a data-footnote-ref href="#user-content-fn-34"><mark style="color:green;">RESTful</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-35"><mark style="color:orange;">Open URL/File</mark></a></td><td><a data-footnote-ref href="#user-content-fn-36"><mark style="color:green;">Statistics</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-37"><mark style="color:orange;">Send Keys</mark></a></td><td><a data-footnote-ref href="#user-content-fn-38"><mark style="color:green;">Disk usage</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-39"><mark style="color:orange;">Mouse control</mark></a></td><td><a data-footnote-ref href="#user-content-fn-40"><mark style="color:orange;">Fullscreen</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-41"><mark style="color:orange;">Media</mark></a></td><td><a data-footnote-ref href="#user-content-fn-42"><mark style="color:orange;">Screenshot Show</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-43"><mark style="color:orange;">Screen On/Off</mark></a></td><td><a data-footnote-ref href="#user-content-fn-44"><mark style="color:orange;">Display environment</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-45"><mark style="color:orange;">Audio Select</mark></a></td><td><a data-footnote-ref href="#user-content-fn-46"><mark style="color:orange;">Idle time</mark></a></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-47"><mark style="color:orange;">Brightness</mark></a></td><td></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-48"><mark style="color:orange;">Keep Alive</mark></a></td><td></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-49"><mark style="color:orange;">Steam</mark></a></td><td></td></tr></tbody></table>

## Supported OS

Only Linux is supported and there is no plan on supporting Windows or MAC because it has many system dependencies that can't be ported. A recommended companion app for windows is [HASS.Agent](https://lab02-research.org/hassagent/) and a cross platform alternative is the [IoTuring](https://github.com/richibrics/IoTuring).

[^1]: ## 🔴 Shutdown

    Creates a button that shuts down the computer.

[^2]: ## 🧠 CPU

    Creates an entity with the current CPU usage.

[^3]: ## ⚪ Restart

    Creates a button that restarts the computer.

[^4]: ## 💾 RAM

    Creates an entity with the current RAM memory usage.

[^5]: ## 💤 Suspend

    Creates a button that puts the computer to sleep mode.

[^6]: ## 🖼️ GPU

    Creates entities for each NVIDIA or AMD GPU load usage.

[^7]: ## 🚀 Boot Select

    Creates a select entity that lets you choose which OS to boot on the next boot.

[^8]: ## 🔋 Battery

    Creates sensor entities for each device that reports it's battery usage in percentage.

    This supports auto-discovery, so it will create the sensor even if it is connected for the 1st time.

[^9]: ## ⚡ Power Profile

    Creates a select entity with all the available power profiles.

[^10]: ## ⚠️ Restart Required

    Creates a binary sensor that shows if the system needs to be restarted, most likely due to an update.

[^11]: ## 🗣️ Speech Recognition

    Listens to the user's input and sends the response as an attribute to the binary sensor of speech recognition entity

    [Usage](usage.md#voice-assistant)

[^12]: ## 📶 Network Speed

    Creates a sensor for upload speed and a sensor for download speed.

[^13]: ## 🌍 LNXlink Update

    Forces the LNXlink to update to the latest version. It supports installations via System or Development.

    [Usage](usage.md#install-update)

[^14]: ## 🔄 System Updates

    Creates a binary sensor that shows if an update is waiting to be installed and a sensor that shows the pending updates.

[^15]: ## 📱 Bluetooth

    Creates two types of switches:

    1. A **Bluetooth Power** switch that enables and disables the Bluetooth on the computer
    2. A **Bluetooth Device** switch for each connected device that disconnects and connects to the device.

    These are auto-discovered even when the app is running.

[^16]: ## 🌐 Interfaces

    Creates a sensor for each network interface found on the system with it's IP address.

[^17]: ## Wake On LAN

    Creates a switch for all network interfaces that support WOL and it can control if it is used or not.

[^18]: ## 🎤 Microphone Used

    Creates a binary sensor that shows if the microphone is used by any application.

[^19]: ## 📜 Logging Level

    Creates a select entity that lets the user select the debug type while running.

    Very useful for debugging an issue.

[^20]: ## 🎥 Camera Used

    Creates a binary sensor that shows if the camera is used by any application.

[^21]: ## 💲🐚 Bash

    One of the most powerful modules that let's you easily create any type of sensor:

    * sensors
    * binary\_sensors

    - buttons
    - switches

    [Settings](modules-settings.md#bash)

[^22]: ## 🎮 Gamepad Used

    Creates a binary sensor that shows if the gamepad is used in the last 40 seconds.

[^23]: ## ⚙️ SystemD

    Creates a switch for each systemd service which is configured and it can start or stop it.

    [Settings](modules-settings.md#systemd)

[^24]: ## 🌡️ Temperature

    Creates sensors for all the temperature sensors that are discoverd on the system.

[^25]: ## 🐳 Docker

    Creates a switch for each discovered docker container and a button that can prune all the unused images/containers/etc...

    [Settings](modules-settings.md#docker)

[^26]: ## 🛜 WiFi

    Creates a sensor with the WiFi signal and some basic information.

[^27]: ## 🧲 GPIO

    Used for Raspberry to create binary\_sensors and switches for the configured input and output pins.

    [Settings](modules-settings.md#gpio)

[^28]: ## 📷 Webcam Show

    Creates a switch that enables a camera entity to show the live video of the computer's webcam.

[^29]: ## 📺 IR Remote

    Used to control devices or receive IR signals. It creates the following entities:

    * Sensor entity for reading the decoded IR signals.
    * Text entity that sends any data provided.
    * Button entities that send the pre-configured data.

    [Settings](modules-settings.md#ir-remote)

[^30]: ## ⏳ Inference Time

    Creates a sensor to show how much time it took for the sensors to get a result.

    This is used for debugging purposes.

[^31]: ## ⌨️ Keyboard Hotkeys

    Creates a sensor that shows the key pressed based on the configured keys.

    [Settings](modules-settings.md#keyboard-hotkeys)

[^32]: ## 📥 Disk I/O

    Creates sensors for each disk and shows the Input/Output percentage of disk used.

[^33]: ## 📢 Notify

    This doesn't create any entity, so it must be used using MQTT commands.

    [Usage](usage.md#notification)

[^34]: ## 📮 RESTful

    Used to get information or control the system using HTTP requests.

    [Usage](usage.md#restful)

[^35]: ## 📂 Open URL/File

    Uses xdg\_open command to open files or URLs.

    [Usage](usage.md#open-a-url-or-file)

[^36]: ## 📊 Statistics

    Used to send anonymous data for measuring how many installations are used each day.

    [Usage](usage.md#statistics)

[^37]: ## 🔑 Send Keys

    Creates a text entity that can send a series of keys using the `xdotool`.

    [Usage](usage.md#keys-send)

[^38]: ## 📀 Disk/Mounts Usage

    Creates a sensor for showing the percentage of used space on each disk.

    [Usage](modules-settings.md#disk-usage)

[^39]: ## 🖱️ Mouse

    Creates buttons that can sends the mouse movement using `xdotool` by accelerating each second.

[^40]: ## ⛶ Fullscreen

    Creates a binary sensor that shows if a window is full screen and it's name.

[^41]: ## ⏯️ Media

    Creates a sensor with the current player status and the media info at it's attributes.

    It also creates buttons for controlling the player which by default are disabled.

    [Usage](media-player.md)

[^42]: ## 📸 Screenshot Show

    Creates a switch that enables a camera entity to show a stream of the desktop.

[^43]: ## 💡 Screen On/Off

    Creates a switch with the monitor status which can also be controlled using the xset command.

[^44]: ## 🪟 Display Variable

    Mend for all desktop environments.

[^45]: ## 🎧 Audio Select

    Creates select entities for selecting the speaker or microphone input device to use.

[^46]: ## ⌛ Idle Time

    Creates a sensor that measures how much time the computer is idle.

[^47]: ## 🔆 Brightness

    It creates a number entity for controlling the brightness of all displays, but also entities for each individual display.

[^48]: ## 🚥 Keep Alive

    Creates a switch that enables or disables the monitor idle with the system commands `xset` or `gsettings`.

[^49]: ## 🎮 Steam

    Creates a select entity with a list of all steam or non steam games.
