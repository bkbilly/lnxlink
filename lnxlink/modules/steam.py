"""List all steam games and start them when selected"""
import os
import re
import glob
import struct
import binascii
import logging
import psutil
from lnxlink.modules.scripts.helpers import import_install_package, syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Steam"
        self.lnxlink = lnxlink
        self._requirements()
        self.steam_config = self._find_libary_config()
        if self.steam_config is None:
            raise SystemError("Steam not found")
        self.games = {}
        self.games = self._get_games()

    def _requirements(self):
        self.vdf = import_install_package("vdf", ">=3.4")

    def exposed_controls(self):
        """Exposes to home assistant"""
        mygames = list(self.games.values())
        mygames.sort()
        mygames.insert(0, "Stopped")
        discovery_info = {
            "Steam Game Select": {
                "type": "select",
                "icon": "mdi:steam",
                "options": mygames,
            },
        }
        return discovery_info

    def get_info(self):
        """Gather information from the system"""
        games = self._get_games()
        if self.games != games:
            self.lnxlink.setup_discovery("steam")
        self.games = games
        return self._get_current_game()

    def start_control(self, topic, data):
        """Control system"""
        try:
            position = list(self.games.values()).index(data)
            game_id = list(self.games.keys())[position]
            logger.info("running command: steam steam://rungameid/%s", game_id)
            syscommand(f"steam steam://rungameid/{game_id}")
        except ValueError:
            logger.error("Can't find selected game: %s", data)

    def _get_current_game(self):
        """Checks running processes"""
        app_ids = set()
        for p in psutil.process_iter():
            try:
                process = " ".join(p.cmdline())
            except psutil.ZombieProcess:
                process = ""
            except psutil.NoSuchProcess:
                process = ""
            if "AppId=" in process:
                match = re.findall(r"AppId=(\d+) ", process)
                if match:
                    app_ids.add(match[0])
        if len(app_ids) > 1:
            logger.info(
                "More than one game instance has been found: %s", ",".join(app_ids)
            )
        for app_id in app_ids:
            game = self.games.get(app_id)
            if game is None:
                long_app_id = int(app_id) << 32 | 0x02000000
                game = self.games.get(long_app_id)
            if game is not None:
                return game
            logger.error("Can't find game app id: %s", app_id)

        return "Stopped"

    def _find_libary_config(self, level=4):
        """Finds the library folders configuration from home directory
        with a max depth level"""
        home_dir = os.path.expanduser("~")
        num_sep = home_dir.count("/")
        name = "libraryfolders.vdf"
        for root, dirs, files in os.walk(home_dir):
            num_sep_this = root.count("/")
            if num_sep + level <= num_sep_this:
                del dirs[:]
            if name in files:
                return os.path.join(root, name)
        return None

    # pylint: disable=too-many-locals
    def _get_games(self):
        """Gets a dictionary of the game_ids and their names"""
        with open(self.steam_config, encoding="UTF-8") as file:
            libraries = self.vdf.load(file)

        # Steam Games
        games = {}
        for num in libraries["libraryfolders"].values():
            for app_id in num["apps"].keys():
                if app_id not in self.games:
                    acf_path = os.path.join(
                        num["path"], f"steamapps/appmanifest_{app_id}.acf"
                    )
                    if os.path.exists(acf_path):
                        with open(acf_path, encoding="UTF-8") as file:
                            game_properties = self.vdf.load(file)
                        games[app_id] = game_properties["AppState"]["name"]
                else:
                    games[app_id] = self.games[app_id]

        # Non-Steam Games
        shortcut_dirs = os.path.abspath(
            f"{self.steam_config}/../../userdata/*/config/shortcuts.vdf"
        )
        for shortcut_dir in glob.glob(shortcut_dirs):
            with open(shortcut_dir, "rb") as file:
                shortcuts_dict = self.vdf.binary_loads(file.read())
            for shortcut in shortcuts_dict["shortcuts"].values():
                # Convert to HEX
                bin_appid = struct.Struct("<i").pack(shortcut["appid"])
                hex_appid = binascii.hexlify(bin_appid).decode("UTF-8")

                # Convert to long_appid
                reversed_hex = bytes.fromhex(hex_appid)[::-1].hex()
                long_app_id = int(reversed_hex, 16) << 32 | 0x02000000
                games[long_app_id] = shortcut["AppName"]

        return games
