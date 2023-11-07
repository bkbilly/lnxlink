"""Control and show information of currently playing media"""
import re
import hashlib
import traceback
import logging
import base64
from dbus.mainloop.glib import DBusGMainLoop
from mpris2 import get_players_uri
from mpris2 import Player

from .scripts.helpers import import_install_package, syscommand

logger = logging.getLogger("lnxlink")


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
                "type": "image",
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
        self._get_players()
        info = {
            "title": "",
            "artist": "",
            "album": "",
            "status": "idle",
            "volume": self._get_volume(),
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
                except Exception as err:
                    logger.debug(
                        "Can't create thumbnail: %s, %s", err, traceback.format_exc()
                    )
        return " "

    def _get_volume(self):
        """Get system volume"""
        mixer = self.lib["alsaaudio"].Mixer()
        volume = mixer.getvolume()[0]
        if mixer.getmute()[0] == 1:
            volume = 0
        return volume

    def _get_players(self):
        """Get all the currently playing players"""
        DBusGMainLoop(set_as_default=True)
        self.players = []
        for uri in get_players_uri():
            player = Player(dbus_interface_info={"dbus_uri": uri})
            p_status = player.PlaybackStatus.lower()
            title = player.Metadata.get("xesam:title")
            title = self._filter_title(title)
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

    def _filter_title(self, title):
        """Returns Title if it contains specific words"""
        filter_md5 = [
            "89e55d4f580dd044088b9a003110b37a",
            "7f55a0ed8b021080de00960cc73768fb",
            "912897db01678cc0d2147154dddba25b",
            "2dfc97e5e093b4b339ad510433d2e9ff",
            "0fa9d94de8921144b76e47749b4a168b",
            "c2fc2f64438b1eb36b7e244bdb7bd535",
            "2e1056defdb4eac51954b37a93608628",
            "139ae12f7d434595aa7822bd16b031e2",
            "6e11873b9d9d94a44058bef5747735ce",
            "3c88b51b66c95449d21f55eb9425deff",
            "efde81f569ccb7211e56a522b8b55e5b",
            "1dea8427d5f6f77f13a6b4019b8ae6c1",
            "acc6f2779b808637d04c71e3d8360eeb",
            "347341c085ab1ff63e8409ac9073da9f",
            "cf9a879316551295f08c3b7a94d45598",
            "3c3662bcb661d6de679c636744c66b62",
            "5928db5ba6fb5071370c3ffc22a518a6",
            "348a448a51d1e0f0f5eee42337d12adc",
            "823299e0dbcad6c1e15131c322905248",
            "99754106633f94d350db34d548d6091a",
            "788da20fc6ffb6e232511322ee663555",
            "509ee77f6b418321a66bfd21b64eaac4",
            "fe325cf304ee9155d513be1044bf064b",
            "c34fd2bbae2c55fbb73a23ea25e4769d",
            "ee2a23af409b352d8f1819405bc770b2",
            "d0a87b4018d6521b0f5a49e5e03adb6d",
            "a11c1e7006223a2a80bd295e96566d6e",
            "98a72e2b19d0b3cc63c92a492ded60b3",
            "fd75d7be0587677990a94b446c72b97f",
            "2047a58fb1c23f36d9b74d689bcc495b",
            "c34c8b2c24e2aa2e45d62f1e15967bd2",
            "738615305e5f421c74d2d25b5e9b6620",
            "3221031e8ed5a17ec9a57271de7fadfe",
            "5ffedc3384099eba61237f0a6ee6c9b5",
            "ad0e9d5ed077db5266ff315985114a4f",
            "102ec827703eeb509f12a2a0eb5b4e2d",
            "b6325a80293eb8e2c510a7a8e8468bc1",
            "1841804c061e6f1890f1c7703f2d1bb3",
            "9268d0b2d17670598c70045b0c7abf38",
            "d12761d2356ddb5659c1bad9d46ebec0",
            "36c029068925a76bbaa77670d6754841",
            "f7c35a9cfd54951862e895bbebef145f",
            "2b6d39e4dc4cdf1ebe3f1a2e80f18202",
            "7bc66d4625c71a3bd3dd6e1505050616",
            "6a1fccefbc7f074b5017884743cde766",
            "fe81a4f28e6bd176efc8184d58544e66",
        ]
        words = re.split(r";|,|\*|\n| +|you|\.|\/|ing", title.strip().lower())
        for word in words:
            md5_word = hashlib.md5(word.encode("UTF-8")).hexdigest()
            if md5_word in filter_md5:
                return "Title"
        return title
