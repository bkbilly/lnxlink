---
description: User defined settings for the modules that support them
---

# 🔗 Settings

## SystemD

Not all services on a machine are needed to be controlled or monitored through a switch, so they need to be configured manually by adding this on your _config.yaml_ file:

```yaml
settings:
  systemd:
    - docker.service
    - anydesk.service
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
```

## Bash

Using this option you can create buttons that run custom commands:

```yaml
settings:
  bash:
    expose:
    - name: Prune Docker
      command: docker system prune -af
      icon: mdi:script-text
```

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
