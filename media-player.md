---
description: Control your media
---

# 🎬 Media Player

MQTT integration for a media player is not supported by home assistant, so a custom addon must be installed. Using HACS you can install the [MQTT Media Player](https://github.com/bkbilly/mqtt\_media\_player) integration for creating a new `media_player` entity.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](.gitbook/assets/hacs\_repository.svg)](https://my.home-assistant.io/redirect/hacs\_repository/?owner=bkbilly\&repository=mqtt\_media\_player\&category=integration)

Once installed you need to restart your Home Assistant instance and add the `MQTT Media Player` integration from `devices & services` page. You can find the appropriate input name under the logs of LNXlink.

<div align="left">

<figure><img src=".gitbook/assets/Screenshot from 2024-10-05 17-11-02.png" alt="" width="287"><figcaption></figcaption></figure>

</div>

It supports playing remote or local media using `cvlc` which should be installed on your system.

<div align="left">

<figure><img src=".gitbook/assets/image.png" alt="" width="449"><figcaption></figcaption></figure>

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

### Volume change by a predefined step

```yaml
service: media_player.volume_set
data:
  volume_level: '{{ state_attr("media_player.desktop_linux", "volume_level") - 0.01 }}'
target:
  entity_id: media_player.desktop_linux
```
