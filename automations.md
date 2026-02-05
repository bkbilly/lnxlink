---
description: These are automation ideas that are really useful when Working From Home
---

# 🤯 Automations

## Pause media playback when I am on the phone

When my phone is ringing or I am in a call, the media will be paused. This works on any application that I might be using like messenger, viber, etc…

```yaml
alias: Incoming call billy
description: ""
mode: single
triggers:
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
conditions:
  - condition: or
    conditions:
      - condition: state
        entity_id: media_player.desktop_linux
        state: playing
actions:
  - service: media_player.media_pause
    data: {}
    target:
      entity_id:
        - media_player.desktop_linux        
```

## Web Camera turns on Light

When I need to use the web camera, the light at my room turns on automatically so that people can see me better.

```yaml
alias: Webcam started
description: ""
mode: single
triggers:
  - type: turned_on
    platform: device
    device_id: c5538068d8ae2f59ea0a46d9953b03ae
    entity_id: binary_sensor.desktop_linux_camera_used
    domain: binary_sensor
conditions: []
actions:
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
triggers:
  - platform: state
    entity_id: switch.my_pc
conditions: []
actions:
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
triggers:
  - platform: state
    to: "on"
    entity_id:
      - binary_sensor.line_crossing
actions:
  - service: camera.snapshot
    data:
      entity_id: camera.out_person
      filename: /config/www/hikvision.jpg
  - service: mqtt.publish
    data:
      topic: lnxlink/desktop-linux/commands/notify
      retain: false
      qos: 0
      payload: >-
        { "title": "Camera Hikvision", 
          "message": "Line crossing", 
          "iconUrl": "https://homeassistant.local/local/hikvision.jpg" }
```

## Share Video from phone

This is used when you share a video link like youtube. It checks if the media player is available, pauses if something is playing, opens the link on your browser and presses the "f" button to activate the full screen.

```yaml
alias: Mobile App Shared
mode: single
triggers:
  - platform: event
    event_type: mobile_app.share
conditions: []
actions:
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

## Gamepad Controller battery notification

Once the controller battery is below 30%, it will flash the lights and send a notification to the computer and on the mobile application.

```yaml
alias: Controller Low Battery
mode: single
triggers:
  - entity_id: sensor.desktop_linux_battery_xbox_wireless_controller
    below: 30
    trigger: numeric_state
actions:
  - action: light.turn_on
    data:
      effect: Flash
    target:
      entity_id: light.myroom
  - action: notify.send_message
    data:
      message: >-
        { "title": "Controller", "message": "Battery is at {{
        trigger.to_state.state }}%", "urgency": "critical"}
    target:
      entity_id: notify.desktop_linux_desktop_linux
  - action: notify.mobile_app_samsung
    data:
      title: Controller
      message: Battery is at {{ trigger.to_state.state }}%
      data:
        channel: Gamepad Battery
        notification_icon: mdi:microsoft-xbox-controller-battery-alert
        clickAction: entityId:{{ trigger.entity_id }}
```
