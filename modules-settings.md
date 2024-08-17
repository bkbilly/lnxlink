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

## Docker

If no configuration is provided, then all the available docker containers will be exposed. This can be configured to only show the ones in the included list or ignore the ones in the exclude list:

```yaml
settings:
  docker:
    include:
      - esphome
    exclude: []
```

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

Using this option you can create `sensors`, `binary_sensors`, `buttons` or `switches` that run custom commands. These options are optional: unit, entity\_category.

```yaml
settings:
  bash:
    expose:
    - name: Prune Docker
      type: button
      command: docker system prune -af
      icon: mdi:script-text
      entity_category: config
    - name: Load 1minute
      type: sensor
      command: cat /proc/loadavg | awk '{print $1}'
      unit: load
      entity_category: diagnostic
    - name: WiFi Exists
      type: binary_sensor
      command: ip a | grep wlan0
    - name: Microphone Mute
      type: switch
      command: amixer get Capture | grep "\[off\]"
      command_on: amixer set Capture nocap
      command_off: amixer set Capture cap
```

<details>

<summary>Create Bash sensors on Home Assistant side</summary>

The bash module can run any command on a remote computer which makes it dangerous, but also very helpful to create sensors without creating modules on LNXlink.

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

## Mounts usage

Checks the usage of mounted volumes on the system. If autocheck is `true`, it will use the Gnome GVFS to find volumes mounted by the file browser.

```yaml
settings:
  mounts:
    autocheck: false
    directories:
      - /mnt/mymount
```
