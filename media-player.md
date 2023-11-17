# 🎬 Media Player

MQTT integration for a media player is not supported by home assistant, so a custom addon must be installed using HACS. I've modified an addon called [mqtt-mediaplayer](https://github.com/bkbilly/hass-mqtt-mediaplayer) for creating a new media\_player entity.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://camo.githubusercontent.com/d20afdeaa87e4b5eb55d72ab709263151bfed2f2f121712ee852aa8cb730f4ad/68747470733a2f2f6d792e686f6d652d617373697374616e742e696f2f6261646765732f686163735f7265706f7369746f72792e737667)](https://my.home-assistant.io/redirect/hacs\_repository/?owner=bkbilly\&repository=hass-mqtt-mediaplayer\&category=integration)

This addon gets the information from the attributes of media\_info sensor. It supports playing remote or local media using `cvlc` which should be installed on your system.

<div align="left">

<figure><img src=".gitbook/assets/image.png" alt="" width="449"><figcaption></figcaption></figure>

</div>

Add this yaml block on your configuration.yaml file and restart Home Assistant.

```yaml
media_player:
  - platform: mqtt-mediaplayer
    name: "Desktop Linux"
    status_keyword: "true"
    topic:
      song_title: "{{ state_attr('sensor.desktop_linux_media_info', 'title') }}"
      song_artist: "{{ state_attr('sensor.desktop_linux_media_info', 'artist') }}"
      song_album: "{{ state_attr('sensor.desktop_linux_media_info', 'album') }}"
      song_volume: "{{ state_attr('sensor.desktop_linux_media_info', 'volume') }}"
      player_status: "{{ state_attr('sensor.desktop_linux_media_info', 'status') }}"
      track_duration: "{{ state_attr('sensor.desktop_linux_media_info', 'duration') }}"
      track_position: "{{ state_attr('sensor.desktop_linux_media_info', 'position') }}"
      album_art: "lnxlink/desktop-linux/monitor_controls/media_info/thumbnail"
      volume:
        service: mqtt.publish
        data:
          topic: "lnxlink/desktop-linux/commands/media/volume_set"
          payload: "{{volume}}"
    next:
      service: mqtt.publish
      data:
        topic: "lnxlink/desktop-linux/commands/media/next"
        payload: "ON"
    previous:
      service: mqtt.publish
      data:
        topic: "lnxlink/desktop-linux/commands/media/previous"
        payload: "ON"
    play_media:
      service: mqtt.publish
      data:
        topic: "lnxlink/desktop-linux/commands/media/play_media"
        payload: "{{media}}"
    play:
      service: mqtt.publish
      data:
        topic: "lnxlink/desktop-linux/commands/media/playpause"
        payload: "ON"
    pause:
      service: mqtt.publish
      data:
        topic: "lnxlink/desktop-linux/commands/media/playpause"
        payload: "ON"
```

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
