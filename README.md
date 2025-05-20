---
description: Effortlessly manage your Linux machine
---

# 🌩️ LNXlink

<figure><img src=".gitbook/assets/logo.png" alt="" width="256"><figcaption></figcaption></figure>

## Welcome

This is a **Home Assistant companion app** for Linux that allows you to monitor and control your PC directly from Home Assistant. It integrates seamlessly using MQTT, enabling automatic discovery of entities and real-time communication between your system and Home Assistant.

## Features

* **Sensors:** Automatically discovers sensors that monitor and control the system.
* **Home Assistant:** Uses MQTT Autodiscovery to create entities and indicate if an update is required.
* **Minimal System Requirements:** Requires only basic system packages.
* **Easily Expanded:** Automatically imports new modules; custom modules can also be added.

## Supported Modules

Modules marked in <mark style="color:orange;">Orange</mark> require a graphical interface, while those in <mark style="color:green;">Green</mark> need require or support manual configuration.

* **✅ System Actions**
  * 🔴 [<mark style="color:blue;">Shutdown</mark>](#user-content-fn-1)[^1]
  * ⚪ [<mark style="color:blue;">Restart</mark>](#user-content-fn-2)[^2]
  * 💤 [<mark style="color:blue;">Suspend</mark>](#user-content-fn-3)[^3]
  * 🚀 [<mark style="color:blue;">Boot Select</mark>](#user-content-fn-4)[^4]
  * ⚡ [<mark style="color:blue;">Power Profile</mark>](#user-content-fn-5)[^5]
  * ⚙️ [<mark style="color:green;">SystemD</mark>](#user-content-fn-6)[^6]
  * 📢 [<mark style="color:orange;">Notify</mark>](#user-content-fn-7)[^7]
  * 📂 [<mark style="color:orange;">Open URL/File</mark>](#user-content-fn-8)[^8]
  * 🚥 [<mark style="color:orange;">Keep Alive</mark>](#user-content-fn-9)[^9]
* **🖥 System Information**
  * 🧠 [<mark style="color:blue;">CPU</mark>](#user-content-fn-10)[^10]
  * 💾 [<mark style="color:blue;">RAM</mark>](#user-content-fn-11)[^11]
  * 🖼️ [<mark style="color:blue;">GPU</mark>](#user-content-fn-12)[^12]
  * 🔋 [<mark style="color:blue;">Battery</mark>](#user-content-fn-13)[^13]
  * 🌡️ [<mark style="color:blue;">Temperature</mark>](#user-content-fn-14)[^14]
  * ⚠️ [<mark style="color:blue;">Restart required</mark>](#user-content-fn-15)[^15]
  * 🔄 [<mark style="color:blue;">System Updates</mark>](#user-content-fn-16)[^16]
  * 📥 [<mark style="color:blue;">Disk IO</mark>](#user-content-fn-17)[^17]
  * 📀 [<mark style="color:green;">Disk usage</mark>](#user-content-fn-18)[^18]
  * ⌛ [<mark style="color:orange;">Idle time</mark>](#user-content-fn-19)[^19]
* **📡 Network & Devices**
  * 📶 [<mark style="color:blue;">Network Speed</mark>](#user-content-fn-20)[^20]
  * 🌐 [<mark style="color:blue;">Interfaces</mark>](#user-content-fn-21)[^21]
  * 📱 [<mark style="color:blue;">Bluetooth</mark>](#user-content-fn-22)[^22]
  * 🛜 [<mark style="color:blue;">WiFi</mark>](#user-content-fn-23)[^23]
  * 🔌 [<mark style="color:blue;">Wake-on-LAN (WOL)</mark>](#user-content-fn-24)[^24]
* 🎚️ **Audio/Video**
  * 🎤 [<mark style="color:blue;">Microphone Used</mark>](#user-content-fn-25)[^25]
  * 🎥 [<mark style="color:blue;">Camera Used</mark>](#user-content-fn-26)[^26]
  * 📷 [<mark style="color:blue;">Webcam Show</mark>](#user-content-fn-27)[^27]
  * 🎶 [<mark style="color:orange;">Media</mark>](#user-content-fn-28)[^28]
  * 🔆 [<mark style="color:orange;">Brightness</mark>](#user-content-fn-29)[^29]
  * 💡 [<mark style="color:orange;">Screen On/Off</mark>](#user-content-fn-30)[^30]
  * &#x20;⛶ [<mark style="color:orange;">Fullscreen</mark>](#user-content-fn-31)[^31]
  * 📸 [<mark style="color:orange;">Screenshot Show</mark>](#user-content-fn-32)[^32]
  * 🎧 [<mark style="color:orange;">Audio Select</mark>](#user-content-fn-33)[^33]
* 🧮 **Input/Output**
  * 🎮 [<mark style="color:blue;">Gamepad Used</mark>](#user-content-fn-34)[^34]
  * ⌨️ [<mark style="color:orange;">Keyboard Hotkeys</mark>](#user-content-fn-35)[^35]
  * 🖱️ [<mark style="color:orange;">Mouse control</mark>](#user-content-fn-36)[^36]
  * 🔑 [<mark style="color:orange;">Send Keys</mark>](#user-content-fn-37)[^37]
* **🧰 Applications & Tools**
  * 🌍 [<mark style="color:blue;">LNXlink Update</mark>](#user-content-fn-38)[^38]
  * 🗣️ [<mark style="color:blue;">Speech Recognition</mark>](#user-content-fn-39)[^39]
  * 🧲 [<mark style="color:green;">GPIO</mark>](#user-content-fn-40)[^40]
  * 📺 [<mark style="color:green;">IR Remote</mark>](#user-content-fn-41)[^41]
  * 🎮 [<mark style="color:orange;">Steam</mark>](#user-content-fn-42)[^42]
* 🧩 **Advanced/Other**
  * ⏳ [<mark style="color:blue;">Inference Time</mark>](#user-content-fn-43)[^43]
  * 📜 [<mark style="color:blue;">Logging Level</mark>](#user-content-fn-44)[^44]
  * 🐚 [<mark style="color:green;">Bash commands</mark>](#user-content-fn-45)[^45]
  * 🐳 [<mark style="color:green;">Docker</mark>](#user-content-fn-46)[^46]
  * 📊 [<mark style="color:green;">Statistics</mark>](#user-content-fn-47)[^47]
  * 📮 [<mark style="color:green;">RESTful</mark>](#user-content-fn-48)[^48]
  * 🪟 [<mark style="color:orange;">Display Environment</mark>](#user-content-fn-49)[^49]

## Supported OS

Only Linux is supported. There is no plan on supporting Windows or MacOS due to system dependencies that can't be easily ported. For windows a recommended companion app is [HASS.Agent](https://lab02-research.org/hassagent/). A cross-platform alternative is [IoTuring](https://github.com/richibrics/IoTuring).

[^1]: ## Shutdown

    Creates a button that shuts down the computer.

[^2]: ## Restart

    Creates a button that restarts the computer.

[^3]: ## Suspend

    Creates a button that puts the computer to sleep mode.

[^4]: ## &#x20;Boot Select

    Creates a select entity that lets you choose which OS to boot on the next boot.

[^5]: ## &#x20;Power Profile

    Creates a select entity with all the available power profiles.

[^6]: ## &#x20;SystemD

    Creates a switch for each systemd service which is configured, allowing for status checks, starting or stopping Linux services.

    [Settings](modules-settings.md#systemd)

[^7]: ## &#x20;Notify

    This doesn't create any entity, so it must be used using MQTT commands.

    [Usage](usage.md#notification)

[^8]: ## &#x20;Open URL/File

    Uses xdg\_open command to open files or URLs.

    [Usage](usage.md#open-a-url-or-file)

[^9]: ## &#x20;Keep Alive

    Creates a switch that enables or disables the monitor idle with the system commands `xset` or `gsettings`.

[^10]: ## &#x20;CPU

    Creates an entity with the current CPU usage.

[^11]: ## &#x20;RAM

    Creates an entity with the current RAM memory usage.

[^12]: ## &#x20;GPU

    Creates entities for each NVIDIA or AMD GPU load usage.

[^13]: ## &#x20;Battery

    Creates sensor entities for each device that reports it's battery usage in percentage.

    This supports auto-discovery, so it will create the sensor even if it is connected for the 1st time.

[^14]: ## &#x20;Temperature

    Creates sensors for all the temperature sensors that are discoverd on the system.

[^15]: ## &#x20;Restart Required

    Creates a binary sensor that shows if the system needs to be restarted, most likely due to an update.

[^16]: ## &#x20;System Updates

    Creates a binary sensor that shows if an update is waiting to be installed and a sensor that shows the pending updates.

[^17]: ## &#x20;Disk I/O

    Creates sensors for each disk and shows the Input/Output percentage of disk used.

[^18]: ## &#x20;Disk/Mounts Usage

    Creates a sensor for showing the percentage of used space on each disk.

    [Usage](modules-settings.md#disk-usage)

[^19]: ## &#x20;Idle Time

    Creates a sensor that measures how much time the computer is idle.

[^20]: ## &#x20;Network Speed

    Creates a sensor for upload speed and a sensor for download speed.

[^21]: ## &#x20;Interfaces

    Creates a sensor for each network interface found on the system with it's IP address.

[^22]: ## &#x20;Bluetooth

    Creates two types of switches:

    1. A **Bluetooth Power** switch that enables and disables the Bluetooth on the computer
    2. A **Bluetooth Device** switch for each connected device that disconnects and connects to the device.

    These are auto-discovered even when the app is running.

[^23]: ## &#x20;WiFi

    Creates a sensor with the WiFi signal and some basic information.

[^24]: ## Wake on LAN

    Creates a switch for all network interfaces that support WOL which allows it to be allowed to be woken using Wake-On-LAN magic packets.

[^25]: ## &#x20;Microphone Used

    Creates a binary sensor that shows if the microphone is used by any application.

[^26]: ## &#x20;Camera Used

    Creates a binary sensor that shows if the camera is used by any application.

[^27]: ## &#x20;Webcam Show

    Creates a switch that enables a camera entity to show the live video of the computer's webcam.

[^28]: ## &#x20;Media

    Creates a sensor with the current player status and the media info at it's attributes.

    It also creates buttons for controlling the player which by default are disabled.

    [Usage](media-player.md)

[^29]: ## &#x20;Brightness

    It creates a number entity for controlling the brightness of all displays, but also entities for each individual display.

[^30]: ## &#x20;Screen On/Off

    Creates a switch with the monitor status which can also be controlled using the xset command.

[^31]: ## &#x20;Fullscreen

    Creates a binary sensor that shows if a window is full screen and it's name.

[^32]: ## &#x20;Screenshot Show

    Creates a switch that enables a camera entity to show a stream of the desktop.

[^33]: ## &#x20;Audio Select

    Creates select entities for selecting the speaker or microphone input device to use.

[^34]: ## &#x20;Gamepad Used

    Creates a binary sensor that shows if the gamepad is used in the last 40 seconds.

[^35]: ## &#x20;Keyboard Hotkeys

    Creates a sensor that shows the key pressed based on the configured keys.

    [Settings](modules-settings.md#keyboard-hotkeys)

[^36]: ## &#x20;Mouse

    Creates buttons that can sends the mouse movement using `xdotool` by accelerating each second.

[^37]: ## &#x20;Send Keys

    Creates a text entity that can send a series of keys using the `xdotool`.

    [Usage](usage.md#keys-send)

[^38]: ## &#x20;LNXlink Update

    Creates an update entity to update to the latest version. It supports installations via System or Development.

    [Usage](usage.md#install-update)

[^39]: ## Speech Recognition

    Listens to the user's input and sends the response as an attribute to the binary sensor of speech recognition entity

    [Usage](usage.md#voice-assistant)

[^40]: ## &#x20;GPIO

    Used for Raspberry to create binary\_sensors and switches for the configured input and output pins.

    [Settings](modules-settings.md#gpio)

[^41]: ## &#x20;IR Remote

    Used to control devices or receive IR signals. It creates the following entities:

    * Sensor entity for reading the decoded IR signals.
    * Text entity that sends any data provided.
    * Button entities that send the pre-configured data.

    [Settings](modules-settings.md#ir-remote)

[^42]: ## &#x20;Steam

    Creates a select entity with a list of all steam or non steam games.

[^43]: ## &#x20;Inference Time

    Creates a sensor to show how much time it took for the sensors to get a result.

    This is used for debugging purposes.

[^44]: ## &#x20;Logging Level

    Creates a select entity that lets the user select the debug type while running.

    Very useful for debugging an issue.

[^45]: ## &#x20;Bash

    One of the most powerful modules that let's you easily create any type of sensor:

    * sensors
    * binary\_sensors

    - buttons
    - switches

    [Settings](modules-settings.md#bash)

[^46]: ## &#x20;Docker

    Creates a switch for each discovered docker container and a button that can prune all the unused images/containers/etc...

    [Settings](modules-settings.md#docker)

[^47]: ## &#x20;Statistics

    Used to send anonymous data for measuring how many installations are used each day.

    [Usage](usage.md#statistics)

[^48]: ## &#x20;RESTful

    Used to get information or control the system using HTTP requests.

    [Usage](usage.md#restful)

[^49]: ## &#x20;Display Variable

    Mend for all desktop environments.
