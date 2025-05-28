"""Control and show information of currently playing media"""
import re
import hashlib
import traceback
import logging
import base64
import threading
import subprocess
from shutil import which
from lnxlink.modules.scripts.helpers import import_install_package, syscommand

logger = logging.getLogger("lnxlink")


# pylint: disable=too-many-instance-attributes
class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Media Info"
        self.lnxlink = lnxlink
        self.players = []
        self._requirements()
        self.prev_info = {}
        self.playmedia_thread = None
        self.process = None
        self.audio_system = self._get_audio_system()
        self.mediavolume = "OFF"
        if self.audio_system is None:
            self.mediavolume = "ON"
        self.media_player = self.dbus_mediaplayer.DBusMediaPlayers(self.media_callback)

    def _requirements(self):
        self.dbus_mediaplayer = import_install_package(
            "dbus-mediaplayer", ">=2025.6.0", "dbus_mediaplayer"
        )

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Media Info": {
                "type": "sensor",
                "icon": "mdi:music",
                "value_template": "{{ value_json.status }}",
                "attributes_template": "{{ value_json | tojson }}",
            },
            "Media Player": {
                "type": "media_player",
            },
            "Stop Media": {
                "type": "button",
                "icon": "mdi:stop",
                "enabled": False,
            },
            "PlayPause": {
                "type": "button",
                "icon": "mdi:play-pause",
                "enabled": False,
            },
            "Previous": {
                "type": "button",
                "icon": "mdi:skip-previous",
                "enabled": False,
            },
            "Next": {
                "type": "button",
                "icon": "mdi:skip-next",
                "enabled": False,
            },
            "Volume Set": {
                "type": "number",
                "icon": "mdi:volume-high",
                "min": 0,
                "max": 1,
                "step": 0.01,
                "enabled": True,
                "value_template": "{{ value_json.volume }}",
            },
            "Thumbnail": {
                "type": "image",
                "encoding": "b64",
                "enabled": False,
                "subtopic": True,
            },
            "Media Volume": {
                "type": "switch",
                "icon": "mdi:volume-source",
                "value_template": "{{ value_json.mediavolume }}",
            },
        }

    def start_control(self, topic, data):
        """Control system"""
        if topic[-1] in ["set_volume", "volume_set"]:
            if data <= 1:
                data *= 100
            data = min(data, 100)
            self._set_volume(data)
        elif len(self.players) > 0 and topic[-1] == "playpause":
            self.media_player.control_media("PlayPause")
        elif len(self.players) > 0 and topic[-1] == "play":
            self.media_player.control_media("Play")
        elif len(self.players) > 0 and topic[-1] == "pause":
            self.media_player.control_media("Pause")
            self.stop_playmedia()
        elif len(self.players) > 0 and topic[-1] == "previous":
            self.media_player.control_media("Previous")
        elif len(self.players) > 0 and topic[-1] == "next":
            self.media_player.control_media("Next")
        elif topic[-1] == "play_media":
            self.play_media(data)
        elif topic[-1] in ["stop_media", "pause"]:
            self.stop_playmedia()
        elif topic[-1] == "media_volume":
            self.mediavolume = data

    def get_info(self):
        """Gather information from the system"""
        info = {
            "title": "",
            "artist": "",
            "album": "",
            "status": "idle",
            "volume": self._get_volume(),
            "playing": False,
            "position": None,
            "duration": None,
            "mediavolume": self.mediavolume,
        }
        if len(self.players) > 0:
            player = self.players[0]
            info["playing"] = True
            info["title"] = player["title"]
            info["album"] = player["album"]
            info["artist"] = player["artist"]
            info["position"] = player["position"]
            info["duration"] = player["duration"]
            info["status"] = player["status"].lower()
            if self.mediavolume == "ON":
                info["volume"] = player["volume"]
            if self.playmedia_thread is not None:
                info["status"] = "playing"
            if self.prev_info != info:
                self.prev_info = info
                self.lnxlink.run_module(f"{self.name}/volume", info["volume"])
                self.lnxlink.run_module(f"{self.name}/state", info["status"])
                self.lnxlink.run_module(f"{self.name}/title", info["title"])
                self.lnxlink.run_module(f"{self.name}/artist", info["artist"])
                self.lnxlink.run_module(f"{self.name}/album", info["album"])
                self.lnxlink.run_module(f"{self.name}/duration", info["duration"])
                self.lnxlink.run_module(f"{self.name}/position", info["position"])
                self.lnxlink.run_module(f"{self.name}/albumart", self.get_thumbnail())
        else:
            info["status"] = "off"
            if self.playmedia_thread is not None:
                info["status"] = "playing"
            if self.prev_info != info:
                self.prev_info = info
                self.lnxlink.run_module(f"{self.name}/state", info["status"])
                self.lnxlink.run_module(f"{self.name}/volume", info["volume"])
                self.lnxlink.run_module(f"{self.name}/albumart", "")
        return info

    def media_callback(self, players):
        """Callback function to update media information"""
        self.players = players
        self.get_info()

    def get_thumbnail(self):
        """Returns the thumbnail if it exists as a base64 string"""
        if len(self.players) > 0:
            player = self.players[0]
            try:
                arturl = player["arturl"].replace("file://", "")
                with open(arturl, "rb") as image_file:
                    image_thumbnail = base64.b64encode(image_file.read())
                    return image_thumbnail
            except Exception as err:
                logger.debug(
                    "Can't create thumbnail: %s, %s", err, traceback.format_exc()
                )
        return b" "

    def stop_playmedia(self):
        """Stops the background media process if it's running"""
        if self.playmedia_thread is not None:
            try:
                self.playmedia_thread.join(0)
                self.process.kill()
                self.playmedia_thread = None
            except Exception:
                self.playmedia_thread = None

    # pylint: disable=too-many-branches
    def play_media(self, data):
        """Finds an plays media using one of the supported players"""
        self.stop_playmedia()
        players = {
            "gst-play-1.0": {
                "supported_media": ["audio", "video", "image"],
                "opt_static": "--wait-on-eos",
                "opt_foreground": "",
                "opt_background": "",
            },
            "ffplay": {
                "supported_media": ["audio", "video", "image"],
                "opt_static": "",
                "opt_foreground": "-autoexit",
                "opt_background": "-nodisp -autoexit",
            },
            "mpv": {
                "supported_media": ["audio", "video", "image", "playlist", "other"],
                "opt_static": "--pause",
                "opt_foreground": "--force-window",
                "opt_background": "",
            },
            "cvlc": {
                "supported_media": ["audio"],
                "opt_static": "--play-and-exit",
                "opt_foreground": "--play-and-exit",
                "opt_background": "--play-and-exit",
            },
            "vlc": {
                "supported_media": ["audio", "video", "playlist", "other"],
                "opt_static": "--play-and-exit",
                "opt_foreground": "--play-and-exit",
                "opt_background": "--play-and-exit",
            },
        }
        audio_extentions = [".mp3", ".wav", ".ogg", ".wma", ".aac"]
        video_extentions = [".mp4", ".avi", ".mov", ".mkv", ".mpg", ".mpeg"]
        image_extentions = [".jpg", ".jpeg", ".png", ".gif", ".ico"]
        for player, options in players.items():
            if which(player) is not None:
                url = data["media_id"]
                media_type = "other"
                if ".m3u" in url:
                    media_type = "playlist"
                elif any(ext in url for ext in audio_extentions):
                    media_type = "audio"
                elif any(ext in url for ext in video_extentions):
                    media_type = "video"
                elif any(ext in url for ext in image_extentions):
                    media_type = "image"
                elif "audio" in data["media_type"]:
                    media_type = "audio"
                elif "music" in data["media_type"]:
                    media_type = "audio"
                elif "video" in data["media_type"]:
                    media_type = "video"
                elif "image" in data["media_type"]:
                    media_type = "image"

                if media_type not in options["supported_media"]:
                    continue
                self.playmedia_thread = threading.Thread(
                    target=self.run_playmedia_thread,
                    args=(player, options, url, media_type),
                    daemon=True,
                )
                self.playmedia_thread.start()
                return
        logger.error(
            "You don't have any player installed on your system: %s", players.keys()
        )

    def run_playmedia_thread(self, player, options, url, media_type):
        """Runs in the background"""
        logger.info("Playing %s using app %s", media_type, player)
        commands = ["exec", player]
        if media_type == "image":
            commands.append(options["opt_static"])
        elif media_type == "audio":
            commands.append(options["opt_background"])
        elif media_type in ["video", "playlist", "other"]:
            commands.append(options["opt_foreground"])
        commands.append(url)
        # pylint: disable=consider-using-with
        self.process = subprocess.Popen(
            " ".join(commands),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _get_audio_system(self):
        """Get system volume type"""
        _, _, returncode = syscommand(
            "pactl get-sink-volume @DEFAULT_SINK@", ignore_errors=True
        )
        if returncode == 0:
            return "pactl"

        _, _, returncode = syscommand("amixer get Master", ignore_errors=True)
        if returncode == 0:
            return "amixer"

        return None

    def _get_volume(self):
        """Get system volume"""
        volume = 100
        if self.audio_system == "pactl":
            result, _, _ = syscommand(
                "pactl get-sink-volume @DEFAULT_SINK@", ignore_errors=True
            )
            match = re.search(r"(\d+)%", result)
            if match:
                volume = int(match.group(1))
        elif self.audio_system == "amixer":
            result, _, _ = syscommand("amixer get Master", ignore_errors=True)
            match = re.search(r"(\d+)%", result)
            if match:
                volume = int(match.group(1))
        return round(volume / 100, 2)

    def _set_volume(self, volume):
        """Set system volume"""
        if self.mediavolume == "ON":
            self.media_player.control_volume(volume / 100)
        elif self.audio_system == "pactl":
            syscommand(f"pactl set-sink-volume @DEFAULT_SINK@ {volume}%")
        elif self.audio_system == "amixer":
            syscommand(f"amixer set Master {volume}%")
        else:
            logger.error("Can't find pactl or amixer commands")

    def _filter_title(self, title):
        """Returns Title if it contains specific words"""
        if title is None:
            return title
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
