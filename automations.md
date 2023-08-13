# 🚗 Automations

## Set unavailable after shutdown

Just before LNXlink stops, it sends to MQTT an OFF command, but sometimes it doesn't stop gracefully. To fix this, you will have to create an automation on Home Assistant which checks for when was the last time one of the sensors got a value and if it exceeds it sends the OFF command to the MQTT server.

This is an example of the automation which checks events for the idle sensor:

```yaml
alias: lnxlink powered down
description: ""
mode: single
trigger:
  - platform: template
    value_template: >-
      {{ (now() | as_timestamp -
      states.sensor.desktop_linux_idle.last_changed | as_timestamp) >
      10 }}
condition: []
action:
  - service: mqtt.publish
    data:
      qos: 0
      retain: true
      topic: lnxlink/desktop-linux/lwt
      payload: "OFF"
```

## Pause media playback when I am on the phone

When my phone is ringing or I am in a call, the media will be paused. This works on any application that I might be using like messenger, viber, etc…

```yaml
alias: Incoming call billy
description: ""
mode: single
trigger:
  - platform: state
    entity_id:
      - sensor.redmi_note_8_pro_audio_mode
    to: ringing
  - platform: state
    entity_id:
      - sensor.redmi_note_8_pro_audio_mode
    to: in_call
  - platform: state
    entity_id:
      - sensor.redmi_note_8_pro_audio_mode
    to: in_communication
condition:
  - condition: or
    conditions:
      - condition: state
        entity_id: media_player.desktop_windows
        state: playing
      - condition: state
        entity_id: media_player.desktop_linux
        state: playing
action:
  - service: media_player.media_pause
    data: {}
    target:
      entity_id:
        - media_player.desktop_windows
        - media_player.desktop_linux        
```

## Web Camera turns on Light

When I need to use the web camera, the light at my room turns on automatically so that people can see me better.

```yaml
alias: Webcam started
description: ""
mode: single
trigger:
  - type: turned_on
    platform: device
    device_id: c5538068d8ae2f59ea0a46d9953b03ae
    entity_id: binary_sensor.desktop_linux_camera_used
    domain: binary_sensor
  - type: turned_on
    platform: device
    device_id: ac5aa697b615f40563be49834acc3a88
    entity_id: binary_sensor.desktop_windows_webcamactive
    domain: binary_sensor
condition: []
action:
  - service: scene.turn_on
    target:
      entity_id: scene.bright
    metadata: {}
  - wait_for_trigger:
      - type: turned_off
        platform: device
        device_id: c5538068d8ae2f59ea0a46d9953b03ae
        entity_id: binary_sensor.desktop_linux_camera_used
        domain: binary_sensor
      - type: turned_off
        platform: device
        device_id: ac5aa697b615f40563be49834acc3a88
        entity_id: binary_sensor.desktop_windows_webcamactive
        domain: binary_sensor
  - type: turn_off
    device_id: f94669e2f90611ea9467bb51f6786486
    entity_id: light.myroom
    domain: light
```

## Turn On/Off PC speakers

My Logitech speakers can be controlled via infrared, so when my PC turns on or off, a power command is sent through Broadlink RM Mini 3 remote.

```yaml
alias: MyPC state change
description: "Turns on or off the speakers of my 🖥 "
mode: single
trigger:
  - platform: state
    entity_id: switch.my_pc
condition: []
action:
  - choose:
      - conditions:
          - condition: state
            entity_id: switch.my_pc
            state: "on"
        sequence:
          - service: media_player.turn_on
            data: {}
            target:
              entity_id: media_player.logitech
    default:
      - service: media_player.turn_off
        data: {}
        target:
          entity_id: media_player.logitech
```

## Notify on Hikvision Line Crossing event

My hikvision camera can recognize when someone has crossed a line that I’ve configured on the camera, so I get a notification on my desktop when this happens.

```yaml
alias: Hikvision - Linecrossing
description: ""
mode: single
trigger:
  - platform: state
    to: "on"
    entity_id:
      - binary_sensor.line_crossing
action:
  - service: camera.snapshot
    data:
      entity_id: camera.out_person
      filename: /config/www/hikvision.jpg
  - service: mqtt.publish
    data:
      topic: lnxlink/desktop-linux/commands/notify
      retain: false
      qos: 0
      payload_template: >-
        { "title": "Camera Hikvision", 
          "message": "Line crossing", 
          "iconUrl": "https://homeassistant.local/local/hikvision.jpg" }
  - service: notify.desktop_windows
    data:
      title: Camera Hikvision
      message: Line crossing
      data:
        image: >-
          https://homeassistant.local/local/hikvision.jpg
```

## Share Video from phone

This is used when you share a video link like youtube. It checks if the media player is available, pauses if something is playing, opens the link on your browser and presses the "f" button to activate the full screen.

```yaml
alias: Mobile App Shared
mode: single
trigger:
  - platform: event
    event_type: mobile_app.share
condition: []
action:
  - if:
      - condition: not
        conditions:
          - condition: state
            entity_id: sensor.desktop_linux_media_info
            state: unavailable
    then:
      - if:
          - condition: state
            entity_id: media_player.desktop_linux
            state: playing
        then:
          - service: media_player.media_play_pause
            data: {}
            target:
              entity_id: media_player.desktop_linux
      - service: mqtt.publish
        data:
          qos: 0
          retain: false
          topic: lnxlink/desktop-linux/commands/xdg_open
          payload: "{{ trigger.event.data.url }}"
      - delay:
          hours: 0
          minutes: 0
          seconds: 3
          milliseconds: 0
      - service: text.set_value
        data:
          value: f
        target:
          entity_id: text.desktop_linux_send_keys
```

