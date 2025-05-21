---
description: Control your media
---

# 🎬 Media Player

**Note:** Home Assistant does not natively support MQTT integration for media players, so a custom add-on must be installed. Using **HACS**, you can install the **MQTT Media Player** integration to create a new `media_player` entity.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](.gitbook/assets/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=bkbilly\&repository=mqtt_media_player\&category=integration)

After installation, restart your Home Assistant instance and add the MQTT Media Player integration from the **Devices & Services** page. You can find the correct input name by checking the **LNXlink** logs.

<div align="left"><figure><img src=".gitbook/assets/Screenshot from 2024-10-05 17-11-02.png" alt=""><figcaption></figcaption></figure></div>

This setup supports playing both local and remote media using one of the following backends: `cvlc`, `gst-play-1.0`, `ffplay`, `mpv`, or `vlc` — make sure at least one of these is installed on your system.

<div align="left"><figure><img src=".gitbook/assets/image.png" alt="" width="449"><figcaption></figcaption></figure></div>

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
