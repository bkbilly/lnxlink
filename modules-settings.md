---
description: User defined settings for the modules that support them
---

# 🔗 Modules Settings

## SystemD

Not all services on a machine are needed to be controlled or monitored through a switch, so they need to be configured manually by adding this on your _config.yaml_ file:

```yaml
settings:
  systemd:
    - docker.service
    - anydesk.service
```

User services can be configured with an object entry:

```yaml
settings:
  systemd:
    - name: syncthing.service
      user: true
```

## Docker

If no configuration is provided, then all the available docker containers will be exposed. This can be configured to only show the ones in the included list or ignore the ones in the exclude list. Also by setting check\_update value it will create binary sensors that check if there is an update available.

```yaml
settings:
  docker:
    include:
      - esphome
    exclude: []
    check_update: 24
    expose_controls: True
```

## Battery

Battery devices can be filtered by the beginning of their model name:

```yaml
settings:
  battery:
    include_batteries: []
    exclude_batteries:
      - Keyboard
```

## Brightness

Monitor brightness entities are discovered when the module starts. Enable autodiscovery if monitors are connected or disconnected while LNXlink is running:

```yaml
settings:
  brightness:
    autodiscovery: true
```

## Idle

The idle module uses `dbus-idle` to read the current desktop idle time. On some Wayland desktop environments, especially setups without the `MIT-SCREEN-SAVER` X11 extension and without Sway support, `dbus-idle` may not find a working monitor.

You can test this manually:

```bash
pipx install dbus-idle
dbus-idle -d
```

If the output includes messages such as `MIT-SCREEN-SAVER missing` or `Could not find any working monitor to get idle time`, install `swayidle` with your distribution package manager and test again:

```bash
# Arch
sudo pacman -S swayidle

# Debian/Ubuntu
sudo apt install swayidle

dbus-idle -d
```

This is useful for KDE Plasma Wayland and other desktop environments where idle detection is not exposed through the usual screensaver interfaces. After `dbus-idle -d` reports `Using: SwayIdleMonitor`, the LNXlink idle module should be able to publish idle time.

## GPIO

This is only supported by Raspberry Pi and needs to be configured manually on your _config.yaml_ file:

```yaml
settings:
  gpio:
    inputs:
      - name: Front Door
        pin: 13
        device_class: door
    outputs:
      - name: Siren
        pin: 25
        icon: mdi:bullhorn
```

## Fingerprint

The fingerprint module is only supported on Raspberry Pi devices with an R503-compatible fingerprint scanner connected over UART. It exposes status sensors and controls for scanning, enrolling, and deleting templates from Home Assistant.

Example configuration:

```yaml
modules:
  - fingerprint

settings:
  fingerprint:
    serial: /dev/serial0
    baudrate: 57600
    password: "0x00000000"
    minimum_confidence: 0
    delete_all_enabled: false
    change_password_enabled: false
    led_enabled: true
```

Available settings:

| Setting | Default | Description |
| ------- | ------- | ----------- |
| `serial` | `/dev/serial0` | UART device used by the fingerprint scanner. |
| `baudrate` | `57600` | Serial baud rate for the scanner. |
| `password` | `0x00000000` | Sensor password. Update this if you change the scanner password. |
| `minimum_confidence` | `0` | Minimum match confidence required before a scan is treated as authorized. |
| `delete_all_enabled` | `false` | Enables the dangerous delete-all Home Assistant button. |
| `change_password_enabled` | `false` | Enables the Home Assistant text entity for changing the sensor password. |
| `led_enabled` | `true` | Enables scanner LED feedback during scan, enroll, and error states. |

The module creates entities for status, mode, last matched ID, last authorized time, confidence, template count, library size, and read errors. It also creates controls for scan, enroll ID, and delete ID.

When enrolling or deleting a fingerprint from Home Assistant, send the template ID as the text value. If enroll is called without a valid ID, the module tries to use the first empty template slot.

Delete-all and password change controls are disabled by default. Enable them only on trusted installations. If you change the scanner password from Home Assistant, update `settings.fingerprint.password` before restarting LNXlink, otherwise the module will not be able to reconnect to the scanner.

## IR Remote

This is only supported by Raspberry Pi and needs to be configured manually on your _config.yaml_ file:

```yaml
settings:
  ir_remote:
    receiver: 18
    transmitter: 23
    buttons:
      - name: PC Speaker
        data: [9084, 4360, 652, 462, 652, 1587, 652, 462, 652, 462, 652, 462, 652, 462, 652, 462, 652, 462, 652, 462, 652, 400, 652, 462, 652, 462, 652, 462, 652, 1587, 652, 462, 652, 1587, 652, 462, 652, 462, 652, 462, 652, 462, 652, 462, 652, 462, 652, 462, 652, 1587, 652, 1587, 652, 1587, 652, 1587, 652, 1587, 652, 1587, 652, 1587, 652, 1587, 652, 462, 652]
        icon: mdi:speaker-wireless
```

In this example, the IR Receiver (TSOP38238) is connected to GPIO input pin 18 and an IR LED is connected to the GPIO input pin 23.

You also need to start the `pigpio` daemon and it should start when the OS boots. This can be done with these commands:

```bash
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

## Keyboard Hotkeys

This is used to run remote commands to your Home Assistant instance using keyboard shortcuts. Pynput is used for the keys syntax and the monitoring of presses.

```yaml
settings:
  hotkeys:
  - key: <ctrl>+<alt>+s
    type: state  # Shows a notification using zenity with the state of the entity
    entity_id: light.myroom
  - key: <ctrl>+<alt>+a
    type: action  # Perform an action on Home Assistant
    service: light.toggle
    entity_id: light.myroom
  - key: <ctrl>+<alt>+z
    type: conversation  # Sends a predefined text to Home Assistant and displays a notification with the result
    text: What is the water heater temperature?
  - key: <ctrl>+<alt>+x # Same as conversation, but a zenity popup with an entry is displayd for the user to write
    type: popup
  - key: <ctrl>+<alt>+q  # Creates a sensor on home assistant, without any further configuration
```

## Bash

Using this option you can create `sensors`, `binary_sensors`, `buttons`, `switches` or `selects` that run custom commands. These options are optional: unit, entity\_category, update\_interval.

```yaml
settings:
  bash:
    allow_any_command: false
    expose:
    - name: Prune Docker
      type: button
      command: docker system prune -af
    - name: Load 1minute
      type: sensor
      command: cat /proc/loadavg | awk '{print $1}'
      unit: load
    - name: WiFi Exists
      type: binary_sensor
      command: ip a | grep wlan0
    - name: Microphone Mute
      type: switch
      command: amixer get Capture | grep "\[off\]"
      command_on: amixer set Capture nocap
      command_off: amixer set Capture cap
    - name: Power Mode
      type: select
      command: powerprofilesctl get
      options:
        - performance
        - balanced
        - power-saver
      command_select: powerprofilesctl set {option}
```

There are some optional options:

```yaml
settings:
  bash:
    expose:
    - name: ....
      type: ....
      command: ....
      icon: mdi:script-text
      entity_category: config  # config or diagnostic
      device_class: battery
      state_class: measurement
      update_interval: 300  # Minimum is the update_interval
      sensor_timeout: 10  # Timeout info command, defaults to 3 sec
      command_timeout: 30  # Timeout control command, defaults to 120 sec
```

<details>

<summary>Create Bash sensors on Home Assistant side</summary>

The bash module can run any command on a remote computer which makes it dangerous, but also very helpful to create sensors without creating modules on LNXlink.

If you want to use it, you should set the following in your LNXlink configuration:

<pre class="language-yaml"><code class="lang-yaml"><strong>settings:
</strong><strong>  bash:
</strong>    allow_any_command: true
</code></pre>

You will need to create a new sensor on your Home Assistant configuration file like so:

```yaml
mqtt:
  sensor:
    - name: "Test ls"
      unique_id: "test_ls"
      state_topic: "lnxlink/desktop-linux/command_result/bash/bash_command/test_ls"
      availability:
        - topic: "lnxlink/desktop-linux/lwt"
          payload_available: "ON"
          payload_not_available: "OFF"
```

Then you must create an automation to run on an interval to get the result of a command:

```yaml
alias: Get files count
mode: single
trigger:
  - platform: time_pattern
    seconds: "40"
action:
  - service: mqtt.publish
    data:
      topic: lnxlink/desktop-linux/commands/bash/bash_command/test_ls
      payload: ls ~/Downloads | wc -l
```

</details>

## Disk usage

By default this module finds all connected drives and exposes them to Home assistant, but this can be changed by setting them manually on settings with the include\_disks option:

```yaml
settings:
  disk_usage:
    include_disks:
      - /dev/sda
      - /dev/sdb
```

Using the exclude\_disks option it finds all connected drives, but excludes from exposing the ones in this configuration:

```yaml
settings:
  disk_usage:
    exclude_disks:
      - /dev/sda
      - /dev/sdb
```

Set `detailed_info` to expose extra attributes such as filesystem, device, used space and free space:

```yaml
settings:
  disk_usage:
    detailed_info: true
```

## Disk IO

By default this module finds physical disks and ignores loop, ram and zram devices. You can limit or exclude disks with:

```yaml
settings:
  disk_io:
    include_disks:
      - sda
      - nvme0n1
    exclude_disks: []
```

## Mounts usage

Checks the usage of mounted volumes on the system. If autocheck is `true`, it will use the Gnome GVFS to find volumes mounted by the file browser.

```yaml
settings:
  mounts:
    autocheck: false
    directories:
      - /mnt/mymount      
```

## Media

When Home Assistant sends media to LNXlink, the media module tries locally installed players in the configured order:

```yaml
settings:
  media:
    order:
      - gst-play-1.0
      - ffplay
      - mpv
      - cvlc
      - vlc
```

## Steam

LNXlink usually finds the Steam library configuration automatically. If it cannot, set the path to `libraryfolders.vdf`:

```yaml
settings:
  steam:
    library: /home/user/.steam/steam/steamapps/libraryfolders.vdf
```

## BeaconDB

Setup custom locations for specific WiFi networks.

```yaml
settings:
  beacondb:
    wifi_positions:
      - ssid: mywifi_example
        latitude: 40.644400
        longitude: 21.494300
        accuracy: 2500

```

## Clipboard

The clipboard module always exposes a text entity to set the clipboard. Clipboard monitoring is disabled by default and can be enabled with:

```yaml
settings:
  clipboard:
    monitor_enabled: true
```

On Wayland it requires `wl-clipboard`. On X11 it requires `xclip` or `xsel`.
