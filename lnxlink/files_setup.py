"""Helper functions to get information from files"""
import importlib.metadata
import logging
import os
import threading
import time
from collections import OrderedDict
from logging.handlers import RotatingFileHandler
from pathlib import Path

import yaml

from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class UniqueQueue:
    """
    A queue that maintains unique named items with a maximum size limit.
    If an item with the same name is added, it replaces the old one.
    When full, the oldest item is discarded to make room.
    """

    def __init__(self, max_size=200):
        """Initializes the UniqueQueue"""
        self.queue = OrderedDict()
        self.max_size = max_size
        self._lock = threading.Lock()

    def __repr__(self):
        """Returns a string representation of the queue."""
        return f"<{self.__class__.__name__} queue: {repr(self.queue)}>"

    def __iter__(self):
        """Returns an iterator that yields and removes items from the queue in FIFO order"""
        while True:
            with self._lock:
                if not self.queue:
                    break
                yield self.queue.popitem(last=False)

    def add_item(self, name, value, retain=True, force_publish=False):
        """Adds an item to the queue. If the item already exists, it replaces it"""
        with self._lock:
            if name in self.queue:
                del self.queue[name]
            elif len(self.queue) >= self.max_size:
                self.queue.popitem(last=False)
            self.queue[name] = (value, retain, force_publish)

    def get_item(self):
        """Retrieves and removes the next item from the queue (FIFO)"""
        with self._lock:
            if self.queue:
                return self.queue.popitem(last=False)
        return None, None

    def clear(self):
        """Clears all items from the queue"""
        with self._lock:
            self.queue.clear()


def setup_logger(config_path, log_level, log_directory=None):
    """Configure file logging."""
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    if log_directory is None:
        log_directory = os.path.dirname(os.path.realpath(config_path))
    log_path = Path(log_directory).expanduser()
    log_path.mkdir(parents=True, exist_ok=True)
    start_sec = str(int(time.time()))[-4:]
    log_formatter = logging.Formatter(
        "%(asctime)s ["
        + start_sec
        + ":%(threadName)s.%(module)s.%(funcName)s.%(lineno)d] [%(levelname)s]  %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_path / "lnxlink.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=1,
    )
    logging.basicConfig(level=log_level)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)


def read_config(config_path):
    """Reads the config file and prepares module names for import"""
    with open(config_path, encoding="utf8") as file:
        conf = yaml.load(file, Loader=yaml.FullLoader)

    conf["config_path"] = config_path

    if conf["modules"] is not None:
        conf["modules"] = [x.lower().replace("-", "_") for x in conf["modules"]]

    if os.environ.get("LNXLINK_MQTT_PREFIX") not in [None, ""]:
        conf["mqtt"]["prefix"] = os.environ.get("LNXLINK_MQTT_PREFIX")
    if os.environ.get("LNXLINK_MQTT_CLIENTID") not in [None, ""]:
        conf["mqtt"]["clientId"] = os.environ.get("LNXLINK_MQTT_CLIENTID")
    if os.environ.get("LNXLINK_MQTT_SERVER") not in [None, ""]:
        conf["mqtt"]["server"] = os.environ.get("LNXLINK_MQTT_SERVER")
    if os.environ.get("LNXLINK_MQTT_PORT") not in [None, ""]:
        conf["mqtt"]["port"] = int(os.environ.get("LNXLINK_MQTT_PORT"))

    pref_topic = f"{conf['mqtt']['prefix']}/{conf['mqtt']['clientId']}"
    conf["pref_topic"] = pref_topic.lower()
    if os.environ.get("LNXLINK_MQTT_USER") not in [None, ""]:
        conf["mqtt"]["auth"]["user"] = os.environ.get("LNXLINK_MQTT_USER")
    if os.environ.get("LNXLINK_MQTT_PASS") not in [None, ""]:
        conf["mqtt"]["auth"]["pass"] = os.environ.get("LNXLINK_MQTT_PASS")

    return conf


def get_install_method(path):
    """Detect how lnxlink was installed"""
    if os.path.exists(os.path.join(path, "lnxlink/edit.txt")):
        method = "edit"
    elif os.environ.get("FLATPAK_ID"):
        method = "flatpak"
    elif os.environ.get("SNAP"):
        method = "snap"
    elif os.path.exists("/.dockerenv"):
        method = "docker"
    elif "pipx" in path:
        method = "pipx"
    elif (
        path.startswith("/usr/lib")
        and syscommand("pacman -Qq python-lnxlink", ignore_errors=True)[2] == 0
    ):
        method = "aur"
    elif path.startswith("/usr/lib"):
        method = "system"
    else:
        method = "pip"
    return method


def get_version():
    """Get the current version and the path of the app"""
    version = importlib.metadata.version(__package__ or __name__)
    path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    if os.path.exists(os.path.join(path, "lnxlink/edit.txt")):
        version += "+edit"
        git_hash, _, return_code = syscommand(
            f"git -C {path} rev-parse --short HEAD",
            ignore_errors=True,
        )
        if return_code == 0:
            version += f"-{git_hash}"
    return version, path
