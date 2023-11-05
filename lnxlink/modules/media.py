"""Control and show information of currently playing media"""
import base64
from dbus.mainloop.glib import DBusGMainLoop
from mpris2 import get_players_uri
from mpris2 import Player

from .scripts.helpers import import_install_package, syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Media Info"
        self.players = []
        self._requirements()

    def _requirements(self):
        self.lib = {
            "alsaaudio": import_install_package("pyalsaaudio", ">=0.9.2", "alsaaudio"),
        }

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Media Info": {
                "type": "sensor",
                "icon": "mdi:music",
                "value_template": "{{ value_json.status }}",
                "attributes_template": "{{ value_json | tojson }}",
            },
            "playpause": {
                "type": "button",
                "icon": "mdi:play-pause",
                "enabled": False,
            },
            "previous": {
                "type": "button",
                "icon": "mdi:skip-previous",
                "enabled": False,
            },
            "next": {
                "type": "button",
                "icon": "mdi:skip-next",
                "enabled": False,
            },
            "volume_set": {
                "type": "number",
                "icon": "mdi:volume-high",
                "min": 0,
                "max": 100,
                "enabled": False,
                "value_template": "{{ value_json.volume }}",
            },
            "thumbnail": {
                "type": "camera",
                "method": self.get_thumbnail,
                "encoding": "b64",
                "enabled": False,
            },
        }

    def start_control(self, topic, data):
        """Control system"""
        if topic[1] == "volume_set":
            mixer = self.lib["alsaaudio"].Mixer()
            if data <= 1:
                data *= 100
            data = min(data, 100)
            mixer.setvolume(int(data))
        elif topic[1] == "playpause":
            if len(self.players) > 0:
                self.players[0]["player"].PlayPause()
        elif topic[1] == "previous":
            if len(self.players) > 0:
                self.players[0]["player"].Previous()
        elif topic[1] == "next":
            if len(self.players) > 0:
                self.players[0]["player"].Next()
        elif topic[1] == "play_media":
            url = data["media_id"]
            syscommand(f"cvlc --play-and-exit {url}")

    def get_info(self) -> dict:
        """Gather information from the system"""
        self.__get_players()
        info = {
            "title": "",
            "artist": "",
            "album": "",
            "status": "idle",
            "volume": self.__get_volume(),
            "playing": False,
            "position": None,
            "duration": None,
        }
        if len(self.players) > 0:
            player = self.players[0]
            info["playing"] = True
            info["title"] = player["title"]
            info["album"] = player["album"]
            info["artist"] = player["artist"]
            info["status"] = player["status"]
            info["position"] = player["position"]
            info["duration"] = player["duration"]

        return info

    def get_thumbnail(self):
        """Returns the thumbnail if it exists as a base64 string"""
        if len(self.players) > 0:
            player = self.players[0]
            if player["status"] != "stopped":
                try:
                    arturl = player["arturl"].replace("file://", "")
                    with open(arturl, "rb") as image_file:
                        image_thumbnail = base64.b64encode(image_file.read()).decode()
                        return image_thumbnail
                except Exception as e:
                    print(e)
        return " "

    def __get_volume(self):
        """Get system volume"""
        mixer = self.lib["alsaaudio"].Mixer()
        volume = mixer.getvolume()[0]
        if mixer.getmute()[0] == 1:
            volume = 0
        return volume

    def __get_players(self):
        """Get all the currently playing players"""
        DBusGMainLoop(set_as_default=True)
        self.players = []
        for uri in get_players_uri():
            player = Player(dbus_interface_info={"dbus_uri": uri})
            p_status = player.PlaybackStatus.lower()
            title = player.Metadata.get("xesam:title")
            artist = player.Metadata.get("xesam:artist")
            album = player.Metadata.get("xesam:album")
            length = player.Metadata.get("mpris:length")
            arturl = player.Metadata.get("mpris:artUrl")

            if p_status != "stopped":
                position = None
                duration = None
                if length is not None:
                    duration = round(length / 1000 / 1000)
                    position = round(player.Position / 1000 / 1000)

                artist_str = ""
                if artist is not None:
                    artist_str = ",".join(artist)
                self.players.append(
                    {
                        "status": p_status,
                        "title": str(title),
                        "artist": artist_str,
                        "album": "" if album is None else str(album),
                        "player": player,
                        "duration": duration,
                        "position": position,
                        "arturl": arturl,
                    }
                )
        return self.players
