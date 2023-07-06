# 🤯 Examples

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

```
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

## Media Player

Create a media player using [mqtt-mediaplayer](https://github.com/bkbilly/hass-mqtt-mediaplayer) using the information collected from the media sensor which supports playing remote or local media using `cvlc` which should be installed on your system.

<div align="left">

<figure><img src="https://user-images.githubusercontent.com/518494/193397441-f18bb5fa-de37-4d95-9158-32cd81b31c72.png" alt=""><figcaption></figcaption></figure>

</div>

### Text To Speech

```yaml
service: tts.google_say
data:
  entity_id: media_player.desktop_linux
  message: Hello world!
```

### Play Media

```yaml
service: media_player.play_media
data:
  media_content_id: /home/user/imag.jpg
  media_content_type: media  # Not used, but required by home assistant
target:
  entity_id: media_player.desktop_linux
```

### Stream Camera

```yaml
service: camera.play_stream
data:
  media_player: media_player.desktop_linux
target:
  entity_id: camera.demo_camera
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

<div align="left">

<figure><img src=".gitbook/assets/Screenshot from 2023-06-22 01-17-12.png" alt=""><figcaption></figcaption></figure>

</div>

## Open a URL or File

```yaml
service: mqtt.publish
data:
  topic: lnxlink/desktop-linux/commands/xdg_open
  payload: "https://www.google.com"  # or "myimg.jpeg" for file
```
