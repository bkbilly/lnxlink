---
description: Effortlessly manage your Linux machine
metaLinks: {}
---

# 🌩️ LNXlink

<figure><img src=".gitbook/assets/logo.png" alt="" width="256"><figcaption></figcaption></figure>

## Welcome

LNXlink is a **Home Assistant companion app** for Linux that bridges the gap between your PC and your smart home ecosystem. By leveraging MQTT and Autodiscovery, it allows you to monitor system stats and trigger remote commands in real-time with zero manual entity configuration.

## Features

* **Automated Sensors:** Discovers and exposes system metrics and controls automatically.
* **MQTT Autodiscovery:** Integrates instantly with Home Assistant with update notifications.
* **Lightweight:** Built to run with minimal system dependencies.
* **Extensible:** Supports a modular architecture; easily import or create custom modules.

## Supported Modules

### 🧮 Graphical Interface

| Module              | Description                                                                                                                       |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| 📢 Notify           | **Send** rich desktop notifications via `notify.send_message`. [Usage](usage.md#notification)                                     |
| 📂 Open URL/File    | **Remotely** l**aunch** websites, files, or folders. [Usage](usage.md#open-a-url-or-file)                                         |
| 🚥 Keep Alive       | **Prevent** monitor sleep or idle states.                                                                                         |
| ⌛ Idle time         | **Monitor** user inactivity duration with a dedicated sensor.                                                                     |
| 🎶 Media            | **Control** playback and track metadata for active media. [Setup](media-player.md)                                                |
| 🔆 Brightness       | **Adjust** hardware display luminance for monitors via number entities.                                                           |
| 💡 Screen On/Off    | **Toggle** monitor power states                                                                                                   |
| ⛶ Fullscreen        | **Detect** if a window is currently in fullscreen mode and view its name.                                                         |
| 📸 Screenshot       | **Stream** your desktop directly to Home Assistant via an image entity.                                                           |
| 🎧 Audio Select     | **Switch** between available speaker or microphone input devices.                                                                 |
| ⌨️ Keyboard Hotkeys | **Capture** specific keypresses for automation triggers (Not for Wayland). [Settings](modules-settings.md#keyboard-hotkeys)       |
| 🖱️ Mouse control   | **Simulate** mouse movement and clicks. Works with the [LNXlink Touchpad Card](https://github.com/bkbilly/lnxlink-touchpad-card). |
| 🔑 Send Keys        | **Broadcast** keystrokes or complex combinations. [Usage](usage.md#keys-send)                                                     |
| 🎮 Steam            | **Launch** Steam or non-Steam games from a dropdown list.                                                                         |
| 🪟 Display Env      | **Identify** the current display environment (e.g., `:0`).                                                                        |
| 🗔 Active Window    | **Monitor** the name and title of the currently focused window.                                                                   |
| 📋 Clipboard        | **View or update** the system clipboard content.                                                                                  |
| 👤 Current Users    | **Monitor** active, unlocked graphical users while ignoring SSH and locked sessions.                                               |

### **✅ System Actions**

| Module          | Description                                                                                                     |
| --------------- | --------------------------------------------------------------------------------------------------------------- |
| 🔴 Shutdown     | **Shut down** the computer instantly from your dashboard.                                                       |
| ⚪ Restart       | **Reboot** the system remotely.                                                                                 |
| 💤 Suspend      | **Trigger** sleep mode to save power when not in use.                                                           |
| 🚀 Boot Select  | **Choose** which operating system to load on the next boot.                                                     |
| ⚡ Power Profile | **Toggle** between performance, balanced, or power-saver profiles.                                              |
| ⚙️ SystemD      | **Manage** Linux services; check status, start, or stop specific units. [Settings](modules-settings.md#systemd) |

### **🖥 System Information**

| Module              | Description                                                                                        |
| ------------------- | -------------------------------------------------------------------------------------------------- |
| 🧠 CPU              | **Monitor** real-time CPU load and performance.                                                    |
| 💾 RAM              | **Track** memory usage and availability.                                                           |
| 🖼️ GPU             | **Monitor** load and usage for NVIDIA or AMD graphics cards.                                       |
| 🔋 Battery          | **Track** battery levels for all connected devices.                                                |
| 🌡️ Temperature     | **Monitor** thermal data from all discovered system sensors.                                       |
| ⚠️ Restart Required | **Detect** if a system reboot is needed (usually after kernel updates).                            |
| 🔄 System Updates   | **Track** pending updates in real-time.                                                            |
| 📥 Disk IO          | **Measure** read/write throughput for each physical disk.                                          |
| 📀 Disk Usage       | **Monitor** storage capacity and percentage used per disk. [Usage](modules-settings.md#disk-usage) |
| 🖴 Mounts           | **View** space usage for all currently mounted volumes. [Usage](modules-settings.md#mounts-usage)  |

### **📡 Network & Devices**

| Module           | Description                                                                                                    |
| ---------------- | -------------------------------------------------------------------------------------------------------------- |
| 📶 Network Speed | **Monitor** real-time upload and download speeds.                                                              |
| 🌐 Interfaces    | **List** active network interfaces and their assigned IP addresses.                                            |
| 📱 Bluetooth     | **Control** global Bluetooth power, connect/disconnect specific devices and their battery.                     |
| 🛜 WiFi          | **Monitor** signal strength and connection metadata.                                                           |
| 🔌 WOL           | **Enable** or disable Wake-On-LAN support for compatible network cards.                                        |
| 🗺️ BeaconDB     | **Locate** the device using WiFi triangulation or custom coordinates. [Settings](modules-settings.md#beacondb) |

### 🎚️ **Audio/Video/Input**

| Module             | Description                                                            |
| ------------------ | ---------------------------------------------------------------------- |
| 🎤 Microphone Used | **Monitor** if any application is currently accessing the microphone.  |
| 🔈 Speaker Used    | **Detect** active audio output to determine if the system is "in use." |
| 🎥 Camera Used     | **Track** webcam activity for privacy or presence automations.         |
| 📹 Webcam          | **Expose** a webcam switch and camera feed.                           |
| 🎮 Gamepad Used    | **Report** controller activity (active if input detected within 40s).  |
| 🔐 Fingerprint     | **Use** an R503 fingerprint scanner over UART on Raspberry Pi. [Settings](modules-settings.md#fingerprint) |

### **🧰 Applications & Tools**

| Module            | Description                                                                                                  |
| ----------------- | ------------------------------------------------------------------------------------------------------------ |
| 🌍 LNXlink Update | **Update** LNXlink directly from Home Assistant. [Usage](usage.md#install-update)                            |
| 🗣️ Speech        | **Process** voice input and return responses via binary sensor attributes. [Usage](usage.md#voice-assistant) |
| 🧲 GPIO           | **Control** and monitor Raspberry Pi GPIO pins. [Settings](modules-settings.md#gpio)                         |
| 📺 IR Remote      | **Control** IR devices or decode incoming signals. [Settings](modules-settings.md#ir-remote)                 |

### 🧩 **Advanced/Other**

| Module            | Description                                                                                                                |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------- |
| 🐚 Bash Commands  | **Create** custom sensors, binary\_sensors, buttons, or switches using shell scripts. [Settings](modules-settings.md#bash) |
| 🐳 Docker         | **Manage** containers; toggle status, check for updates, or prune images. [Settings](modules-settings.md#docker)           |
| ⏳ Inference Time  | **Debug** performance by measuring sensor data collection latency.                                                         |
| 📜 Logging Level  | **Change** debug verbosity on-the-fly for troubleshooting.                                                                 |
| 📊 Statistics     | **Opt-in** to send anonymous usage data to help improve LNXlink. [Usage](usage.md#statistics)                              |
| 📮 RESTful        | **Interact** with the system using standard HTTP requests. [Usage](usage.md#restful)                                       |
| 🔁 Update Entities | **Force** all or selected module entities to publish a fresh update.                                                        |
| 👁️ Watch Changes | **Restart** when the configuration changes                                                                                 |

### **📦 Custom Modules**

| Module                  | Link                                                                                           |
| ----------------------- | ---------------------------------------------------------------------------------------------- |
| Lutris Game Launcher    | [Discussion #202](https://github.com/bkbilly/lnxlink/discussions/202)                          |
| Active Window (Wayland) | [Discussion #126](https://github.com/bkbilly/lnxlink/discussions/126)                          |
| Screens On/Off (KDE)    | [KDE Module Source](https://github.com/D3SOX/lnxlink-modules/blob/master/kde_screens_onoff.py) |
| AM2302 Temp/Humidity    | [Discussion #81](https://github.com/bkbilly/lnxlink/discussions/81)                            |
| Satisfactory Server     | [Discussion #128](https://github.com/bkbilly/lnxlink/discussions/128)                          |
| GPU nvidia-settings     | [NVIDIA Settings Source](https://github.com/PW999/lnxlink_gpu_nvidia_settings)                 |

## Supported OS

LNXlink is built specifically for **Linux**. There are currently no plans for Windows or macOS support due to deep system dependencies. Here are some alternatives:

<table><thead><tr><th width="178.2578125">Application</th><th>Platform</th><th>Protocol</th></tr></thead><tbody><tr><td>Go Hass Agent</td><td>Linux, Windows, macOS</td><td>Native HA Mobile App API + MQTT</td></tr><tr><td>HASS.Agent</td><td>Windows</td><td>HA API + MQTT</td></tr><tr><td>System Bridge</td><td>Windows, Linux</td><td>HA API (WebSocket)</td></tr><tr><td>Glances</td><td>Cross-platform (Linux, Windows, macOS, BSD)</td><td>REST API (HTTP polling)</td></tr><tr><td>IoTuring</td><td>Cross-platform (Windows, Linux, macOS, BSD)</td><td>MQTT</td></tr></tbody></table>
