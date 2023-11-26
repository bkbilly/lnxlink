---
description: >-
  These modules are not created using the autodiscovery or they need to be
  combined with others to work.
---

# 🔱 Modules Usage

## Voice Assistant

The Speech Recognition module listens to the user's input and sends the response as an attribute to the binary sensor of speech recognition entity.

For the automation to work you will need to setup the Media Player.

<details>

<summary>LNXlink Speech Recognition</summary>

Set the volume to the desired level and then if a successful speech is recognized it is sent to the conversation agent of Home Assistant to run. The result is then sent as an audio to the host machine.

```yaml
alias: LNXlink Speech Recognition
mode: single
trigger:
  - platform: state
    entity_id:
      - binary_sensor.desktop_linux_speech_recognition
    from: "off"
    to: "on"
condition: []
action:
  - variables:
      volume: "{{ state_attr('media_player.desktop_linux', 'volume_level') }}"
  - service: media_player.volume_set
    data:
      volume_level: 0.15
    target:
      entity_id: media_player.desktop_linux
  - wait_for_trigger:
      - platform: state
        entity_id:
          - binary_sensor.desktop_linux_speech_recognition
        to: "off"
  - if:
      - condition: not
        conditions:
          - condition: state
            entity_id: binary_sensor.desktop_linux_speech_recognition
            attribute: speech
            state: "\"\""
    then:
      - service: conversation.process
        data:
          agent_id: homeassistant
          text: >-
            {{ state_attr('binary_sensor.desktop_linux_speech_recognition',
            'speech') }}
        response_variable: agent
  - service: media_player.volume_set
    data:
      volume_level: "{{ volume }}"
    target:
      entity_id: media_player.desktop_linux
  - service: tts.speak
    data:
      cache: true
      media_player_entity_id: media_player.desktop_linux
      message: "{{ agent.response.speech.plain.speech }}"
    target:
      entity_id: tts.piper

```

</details>

## Notification

Sends a notification with an image as a preview

```yaml
service: mqtt.publish
data:
  topic: {prefix}/{clientId}/commands/notify
  payload: >-
    { "title": "Notification Title",
      "message": "Testing notification",
      "iconUrl": "http://hass.local:8123/local/myimage.jpg" }
```

## Turn PC On or Off

Combine with Wake on Lan to control your PC with one switch:

```yaml
switch:
  - platform: template
    switches:
      my_pc:
        friendly_name: "My PC"
        unique_id: my_pc
        value_template: "{{ not is_state('button.shutdown', 'unavailable') }}"
        turn_on:
          service: switch.turn_on
          data:
            entity_id: switch.pc_wol
        turn_off:
          service: button.press
          data:
            entity_id: button.shutdown
```

## Open a URL or File

```yaml
service: mqtt.publish
data:
  topic: lnxlink/desktop-linux/commands/xdg_open
  payload: "https://www.google.com"  # or "myimg.jpeg" for file
```

## Keys Send

Send a series of keys:

```yaml
service: mqtt.publish
data:
  topic: {prefix}/{clientId}/commands/send_keys
  payload: "ctrl+f H e l l o space W o r l d"  
```

You can create a virtual keyboard on your frontend:

<div align="left" data-full-width="false">

<figure><img src=".gitbook/assets/Screenshot from 2023-11-02 11-10-09.png" alt=""><figcaption></figcaption></figure>

</div>

<details>

<summary>Lovelace Card Config Letters</summary>

{% code overflow="wrap" lineNumbers="true" %}
```yaml
type: conditional
conditions:
  - entity: input_boolean.keyboard_switch
    state: 'off'
  - entity: text.desktop_linux_bash_command
    state: unknown
card:
  type: vertical-stack
  cards:
    - square: true
      type: grid
      cards:
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: q
          entity: text.desktop_linux_send_keys
          name: Q
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: w
          entity: text.desktop_linux_send_keys
          name: W
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: e
          entity: text.desktop_linux_send_keys
          name: E
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: r
          entity: text.desktop_linux_send_keys
          name: R
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: t
          entity: text.desktop_linux_send_keys
          name: T
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: 'y'
          entity: text.desktop_linux_send_keys
          name: 'Y'
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: u
          entity: text.desktop_linux_send_keys
          name: U
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: i
          entity: text.desktop_linux_send_keys
          name: I
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: o
          entity: text.desktop_linux_send_keys
          name: O
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: p
          entity: text.desktop_linux_send_keys
          name: P
          hold_action:
            action: more-info
      columns: 10
    - square: true
      type: grid
      cards:
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: a
          entity: text.desktop_linux_send_keys
          name: A
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: s
          entity: text.desktop_linux_send_keys
          name: S
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: d
          entity: text.desktop_linux_send_keys
          name: D
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: f
          entity: text.desktop_linux_send_keys
          name: F
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: g
          entity: text.desktop_linux_send_keys
          name: G
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: h
          entity: text.desktop_linux_send_keys
          name: H
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: j
          entity: text.desktop_linux_send_keys
          name: J
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: k
          entity: text.desktop_linux_send_keys
          name: K
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: l
          entity: text.desktop_linux_send_keys
          name: L
          hold_action:
            action: more-info
        - show_name: false
          show_icon: true
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: BackSpace
          entity: text.desktop_linux_send_keys
          hold_action:
            action: more-info
          icon: mdi:backspace-outline
      columns: 10
    - square: true
      type: grid
      columns: 10
      cards:
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: z
          entity: text.desktop_linux_send_keys
          name: Z
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: x
          entity: text.desktop_linux_send_keys
          name: X
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: c
          entity: text.desktop_linux_send_keys
          name: C
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: v
          entity: text.desktop_linux_send_keys
          name: V
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: b
          entity: text.desktop_linux_send_keys
          name: B
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: 'n'
          entity: text.desktop_linux_send_keys
          name: 'N'
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: m
          entity: text.desktop_linux_send_keys
          name: M
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: comma
          entity: text.desktop_linux_send_keys
          name: ','
          hold_action:
            action: more-info
        - show_name: true
          show_icon: false
          type: button
          tap_action:
            action: call-service
            service: text.set_value
            target:
              entity_id: text.desktop_linux_send_keys
            data:
              value: period
          entity: text.desktop_linux_send_keys
          name: .
          hold_action:
            action: more-info
    - type: horizontal-stack
      cards:
        - square: false
          type: grid
          columns: 1
          cards:
            - show_name: false
              show_icon: true
              type: button
              tap_action:
                action: toggle
              entity: input_boolean.keyboard_switch
              icon: ''
              icon_height: 30px
              show_state: false
        - square: true
          type: grid
          columns: 2
          cards: []
        - square: false
          type: grid
          columns: 1
          cards:
            - show_name: false
              show_icon: true
              type: button
              tap_action:
                action: call-service
                service: text.set_value
                target:
                  entity_id: text.desktop_linux_send_keys
                data:
                  value: space
              entity: text.desktop_linux_send_keys
              name: Space
              icon: mdi:keyboard-space
              icon_height: 30px
              hold_action:
                action: more-info
        - square: true
          type: grid
          columns: 2
          cards: []
        - square: false
          type: grid
          columns: 1
          cards:
            - show_name: false
              show_icon: true
              type: button
              tap_action:
                action: call-service
                service: text.set_value
                target:
                  entity_id: text.desktop_linux_send_keys
                data:
                  value: Return
              entity: text.desktop_linux_send_keys
              name: Enter
              hold_action:
                action: more-info
              icon: mdi:keyboard-return
              icon_height: 30px

```
{% endcode %}

</details>

<div align="left">

<figure><img src=".gitbook/assets/Screenshot from 2023-11-02 11-10-20.png" alt=""><figcaption></figcaption></figure>

</div>

<details>

<summary>Lovelace Card Config Symbols</summary>

```yaml
type: conditional
conditions:
  - entity: input_boolean.keyboard_switch
    state: 'on'
  - entity: text.desktop_linux_bash_command
    state: unknown
card:
  square: true
  type: grid
  columns: 7
  cards:
    - show_name: true
      show_icon: false
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: Escape
      entity: text.desktop_linux_send_keys
      name: Esc
      hold_action:
        action: more-info
    - show_name: true
      show_icon: false
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: '1'
      entity: text.desktop_linux_send_keys
      name: '1'
      hold_action:
        action: more-info
    - show_name: true
      show_icon: false
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: '2'
      entity: text.desktop_linux_send_keys
      name: '2'
      hold_action:
        action: more-info
    - show_name: true
      show_icon: false
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: '3'
      entity: text.desktop_linux_send_keys
      name: '3'
      hold_action:
        action: more-info
    - show_name: true
      show_icon: false
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: slash
      entity: text.desktop_linux_send_keys
      name: /
      hold_action:
        action: more-info
    - show_name: false
      show_icon: true
      icon: mdi:arrow-up
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: Up
      entity: text.desktop_linux_send_keys
      hold_action:
        action: more-info
    - show_name: true
      show_icon: false
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: backslash
      entity: text.desktop_linux_send_keys
      name: \
      hold_action:
        action: more-info
    - show_name: true
      show_icon: false
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: Tab
      entity: text.desktop_linux_send_keys
      name: Tab
      hold_action:
        action: more-info
    - show_name: true
      show_icon: false
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: '4'
      entity: text.desktop_linux_send_keys
      name: '4'
      hold_action:
        action: more-info
    - show_name: true
      show_icon: false
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: '5'
      entity: text.desktop_linux_send_keys
      name: '5'
      hold_action:
        action: more-info
    - show_name: true
      show_icon: false
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: '6'
      entity: text.desktop_linux_send_keys
      name: '6'
      hold_action:
        action: more-info
    - show_name: false
      show_icon: true
      icon: mdi:arrow-left
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: Left
      entity: text.desktop_linux_send_keys
      hold_action:
        action: more-info
    - show_name: false
      show_icon: true
      icon: mdi:arrow-down
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: Down
      entity: text.desktop_linux_send_keys
      hold_action:
        action: more-info
    - show_name: false
      show_icon: true
      icon: mdi:arrow-right
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: Right
      entity: text.desktop_linux_send_keys
      hold_action:
        action: more-info
    - show_name: false
      show_icon: true
      type: button
      tap_action:
        action: toggle
      entity: input_boolean.keyboard_switch
      icon: ''
      icon_height: 30px
      show_state: false
    - show_name: true
      show_icon: false
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: '7'
      entity: text.desktop_linux_send_keys
      name: '7'
      hold_action:
        action: more-info
    - show_name: true
      show_icon: false
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: '8'
      entity: text.desktop_linux_send_keys
      name: '8'
      hold_action:
        action: more-info
    - show_name: true
      show_icon: false
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: '9'
      entity: text.desktop_linux_send_keys
      name: '9'
      hold_action:
        action: more-info
    - show_name: true
      show_icon: false
      type: button
      tap_action:
        action: call-service
        service: text.set_value
        target:
          entity_id: text.desktop_linux_send_keys
        data:
          value: 0
      entity: text.desktop_linux_send_keys
      name: '0'
      hold_action:
        action: more-info

```

</details>

## Install Update

When a new version of LNXlink is available the update sensor on Home Assistant activates the INSTALL button, but when you are using the development installation this option doesn't get activated. You can manually send the MQTT topic to start the update:

```yaml
service: mqtt.publish
data:
  topic: lnxlink/desktop-linux/commands/update/update
```

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

## SystemD

Not all services on a machine are needed to be controlled or monitored through a switch, so they need to be configured manually by adding this on your configuration.yaml file:

```yaml
settings:
  systemd:
    - docker.service
    - anydesk.service
```

