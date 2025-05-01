"""Helper functions to get information from files"""
import os
import time
import logging
import importlib.metadata
from logging.handlers import RotatingFileHandler
from collections import OrderedDict

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

    def __repr__(self):
        """Returns a string representation of the queue."""
        return f"<{self.__class__.__name__} queue: {repr(self.queue)}>"

    def __iter__(self):
        """Returns an iterator that yields and removes items from the queue in FIFO order"""
        while self.queue:
            yield self.queue.popitem(last=False)

    def add_item(self, name, value):
        """Adds an item to the queue. If the item already exists, it replaces it"""
        # If item exists, remove it so we can re-add at the end
        if name in self.queue:
            del self.queue[name]
        # If queue is full, remove the oldest item
        elif len(self.queue) >= self.max_size:
            self.queue.popitem(last=False)
        self.queue[name] = value

    def get_item(self):
        """Retrieves and removes the next item from the queue (FIFO)"""
        if self.queue:
            return self.queue.popitem(last=False)
        return None, None

    def clear(self):
        """Clears all items from the queue"""
        self.queue.clear()


def setup_logger(config_path, log_level):
    """Save logs on the same directory as the config file"""
    config_dir = os.path.dirname(os.path.realpath(config_path))
    start_sec = str(int(time.time()))[-4:]
    log_formatter = logging.Formatter(
        "%(asctime)s ["
        + start_sec
        + ":%(threadName)s.%(module)s.%(funcName)s.%(lineno)d] [%(levelname)s]  %(message)s"
    )

    file_handler = RotatingFileHandler(
        f"{config_dir}/lnxlink.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=1,
    )
    logging.basicConfig(level=log_level)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)


def read_config(config_path):
    """Reads the config file and prepares module names for import"""
    with open(config_path, "r", encoding="utf8") as file:
        conf = yaml.load(file, Loader=yaml.FullLoader)

    pref_topic = f"{conf['mqtt']['prefix']}/{conf['mqtt']['clientId']}"
    conf["pref_topic"] = pref_topic.lower()
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
        conf["mqtt"]["port"] = os.environ.get("LNXLINK_MQTT_PORT")
    if os.environ.get("LNXLINK_MQTT_USER") not in [None, ""]:
        conf["mqtt"]["user"] = os.environ.get("LNXLINK_MQTT_USER")
    if os.environ.get("LNXLINK_MQTT_PASS") not in [None, ""]:
        conf["mqtt"]["pass"] = os.environ.get("LNXLINK_MQTT_PASS")
    if os.environ.get("LNXLINK_HASS_URL") not in [None, ""]:
        conf["hass_url"] = os.environ.get("LNXLINK_HASS_URL")
    if os.environ.get("LNXLINK_HASS_API") not in [None, ""]:
        conf["hass_api"] = os.environ.get("LNXLINK_HASS_API")

    return conf


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
