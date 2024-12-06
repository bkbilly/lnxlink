#!/usr/bin/env python3
"""Start the LNXlink service"""

import os
import sys
import time
import json
import threading
import logging
from logging.handlers import RotatingFileHandler
import argparse
import platform
import importlib.metadata
import ssl
import traceback

import yaml
import distro
import paho.mqtt.client as mqtt
from lnxlink import modules
from lnxlink import config_setup
from lnxlink.system_monitor import MonitorSuspend, GracefulKiller
from lnxlink.modules.scripts.helpers import syscommand


# Get the current version of the app
version = importlib.metadata.version(__package__ or __name__)
path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if os.path.exists(os.path.join(path, "lnxlink/edit.txt")):
    version += "+edit"
    git_hash, _, return_code = syscommand(f"git -C {path} rev-parse --short HEAD")
    if return_code == 0:
        version += f"-{git_hash}"

logger = logging.getLogger("lnxlink")


# pylint: disable=too-many-instance-attributes
class LNXlink:
    """Start LNXlink service that loads all modules and connects to MQTT"""

    version = version
    path = path

    def __init__(self, config_path):
        logger.info("LNXlink %s, Python %s", self.version, platform.python_version())
        logger.debug("Path=%s", self.path)
        self.config_path = config_path
        self.kill = None
        self.display = None
        self.inference_times = {}
        self.addons = {}
        self.prev_publish = {}
        self.saved_publish = {}
        self.update_change_interval = 900
        self.pref_topic = "lnxlink"
        if hasattr(mqtt, "CallbackAPIVersion"):
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        else:
            self.client = mqtt.Client()

        # Read configuration from yaml file
        self.config = self.read_config(config_path)

    def start(self, exclude_modules_arg):
        """Run each addon included in the modules folder"""
        conf_exclude = self.config["exclude"]
        conf_exclude = [] if conf_exclude is None else conf_exclude
        conf_exclude.extend(exclude_modules_arg)
        loaded_modules = modules.parse_modules(
            self.config["modules"], self.config["custom_modules"], conf_exclude
        )
        for _, addon in loaded_modules.items():
            try:
                tmp_addon = addon(self)
                self.addons[addon.service] = tmp_addon
            except Exception as err:
                logger.error(
                    "Error with addon %s, please remove it from your config: %s",
                    addon.service,
                    err,
                )
                logger.debug(
                    traceback.format_exc(),
                )
        loaded = list(self.addons.keys())
        loaded.sort()
        logger.info("Loaded addons: %s", ", ".join(loaded))

        # Setup MQTT
        return self.setup_mqtt()

    def publish_monitor_data(self, name, pub_data):
        """Publish info data to mqtt in the correct format"""
        subtopic = name.lower().replace(" ", "_")
        topic = f"{self.pref_topic}/monitor_controls/{subtopic}"
        if pub_data is None:
            return
        if isinstance(pub_data, bool):
            if pub_data is True:
                pub_data = "ON"
            if pub_data is False:
                pub_data = "OFF"
        if isinstance(pub_data, dict):
            if all(v is None for v in pub_data.values()):
                return
        if isinstance(pub_data, list):
            if all(v is None for v in pub_data):
                return
        if isinstance(pub_data, (dict, list)):
            pub_data = json.dumps(pub_data)

        # User option that checks and sends only the updated sensors
        update_change_time = time.time() - self.prev_publish.get("last_update", 0)
        if update_change_time > self.update_change_interval:
            self.prev_publish = {"last_update": time.time()}
        if (
            self.config["update_on_change"] or isinstance(pub_data, bytes)
        ) and self.prev_publish.get(topic) == pub_data:
            return

        self.prev_publish[topic] = pub_data
        self.saved_publish[subtopic.replace("/", "_")] = pub_data
        self.client.publish(
            topic, payload=pub_data, retain=self.config["mqtt"]["lwt"]["retain"]
        )

    def run_module(self, name, method):
        """Runs the method of a module"""
        try:
            start_time = time.time()
            if isinstance(method, (dict, list, bool, bytes, int, str, float)):
                pub_data = method
            else:
                pub_data = method()
                diff_time = round(time.time() - start_time, 5)
                self.inference_times[name] = diff_time
            self.publish_monitor_data(name, pub_data)
        except Exception as err:
            logger.error(
                "Error with addon %s: %s, %s",
                name,
                err,
                traceback.format_exc(),
            )

    def monitor_run(self):
        """Gets information from each Addon and sends it to MQTT"""
        methods_to_run = []
        for _, addon in self.addons.items():
            if hasattr(addon, "get_info"):
                methods_to_run.append(
                    {
                        "name": addon.name,
                        "method": addon.get_info,
                    }
                )
        for method in methods_to_run:
            self.run_module(method["name"], method["method"])

    def monitor_run_thread(self):
        """Runs method to get sensor information every prespecified interval"""
        self.monitor_run()

        interval = self.config["update_interval"]
        if not self.kill:
            monitor = threading.Timer(interval, self.monitor_run_thread)
            monitor.start()

    def setup_mqtt(self):
        """Creates the mqtt object"""
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        keyfile = self.config["mqtt"]["auth"]["keyfile"]
        keyfile = None if keyfile == "" else keyfile
        certfile = self.config["mqtt"]["auth"]["certfile"]
        certfile = None if certfile == "" else certfile
        ca_certs = self.config["mqtt"]["auth"]["ca_certs"]
        ca_certs = None if ca_certs == "" else ca_certs
        use_cert = all(option is not None for option in [keyfile, certfile, ca_certs])
        use_tls = self.config["mqtt"]["auth"]["tls"]
        username = self.config["mqtt"]["auth"]["user"]
        password = self.config["mqtt"]["auth"]["pass"]
        use_userpass = all(option != "" for option in [username, password])

        if use_userpass:
            self.client.username_pw_set(username, password)
        if use_tls:
            cert_reqs = ssl.CERT_NONE
            if use_cert:
                cert_reqs = ssl.CERT_REQUIRED
            logger.info("Using MQTT ca_certs: %s", ca_certs)
            logger.info("Using MQTT certfile: %s", certfile)
            logger.info("Using MQTT keyfile: %s", keyfile)
            self.client.tls_set(
                ca_certs=ca_certs,
                certfile=certfile,
                keyfile=keyfile,
                cert_reqs=cert_reqs,
            )
            if ca_certs is None:
                self.client.tls_insecure_set(True)
        if self.config["mqtt"]["lwt"]["enabled"]:
            self.client.will_set(
                f"{self.pref_topic}/lwt",
                payload="OFF",
                qos=self.config["mqtt"]["lwt"]["qos"],
                retain=True,
            )
        try:
            self.client.connect(
                self.config["mqtt"]["server"], self.config["mqtt"]["port"], 60
            )
        except ssl.SSLCertVerificationError:
            logger.info("TLS not verified, using insecure connection instead")
            self.client.tls_insecure_set(True)
            self.client.connect(
                self.config["mqtt"]["server"], self.config["mqtt"]["port"], 60
            )
        except Exception as err:
            logger.error(
                "Error establishing connection to MQTT broker: %s, %s",
                err,
                traceback.format_exc(),
            )
            return False
        self.client.loop_start()
        return True

    def read_config(self, config_path):
        """Reads the config file and prepares module names for import"""
        with open(config_path, "r", encoding="utf8") as file:
            conf = yaml.load(file, Loader=yaml.FullLoader)

        self.pref_topic = f"{conf['mqtt']['prefix']}/{conf['mqtt']['clientId']}"
        self.pref_topic = self.pref_topic.lower()

        if conf["modules"] is not None:
            conf["modules"] = [x.lower().replace("-", "_") for x in conf["modules"]]
        return conf

    def on_connect(self, client, userdata, flags, rcode, *args):
        """Callback for MQTT connect which reports the connection status
        back to MQTT server"""
        logger.info("MQTT connection: %s", mqtt.connack_string(rcode))
        client.subscribe(f"{self.pref_topic}/commands/#")
        if self.config["mqtt"]["lwt"]["enabled"]:
            self.client.publish(
                f"{self.pref_topic}/lwt",
                payload="ON",
                qos=self.config["mqtt"]["lwt"]["qos"],
                retain=True,
            )
        if self.config["mqtt"]["discovery"]["enabled"]:
            self.setup_discovery()
        if self.kill is None:
            self.kill = False
            self.monitor_run_thread()

    def on_disconnect(self, *args):
        """Disconnected from MQTT broker"""
        logger.warning("Lost connection to MQTT Broker...")

    def disconnect(self, *args):
        """Reports to MQTT server that the service has stopped"""
        logger.info("Disconnected from MQTT.")
        if self.config["mqtt"]["lwt"]["enabled"]:
            self.client.publish(
                f"{self.pref_topic}/lwt",
                payload="OFF",
                qos=self.config["mqtt"]["lwt"]["qos"],
                retain=True,
            )
        self.kill = True
        self.client.disconnect()

    def replace_values_with_none(self, data):
        """Replaces specified values with None recursively"""
        if isinstance(data, (str, bool, float, int)):
            return None
        if isinstance(data, dict):
            return {
                key: self.replace_values_with_none(value) for key, value in data.items()
            }
        return data

    def temp_connection_callback(self, status):
        """Report the connection status to MQTT server"""
        self.kill = True
        if self.config["mqtt"]["lwt"]["enabled"]:
            if status:
                logger.info("Power Down detected.")
                self.client.publish(
                    f"{self.pref_topic}/lwt",
                    payload="OFF",
                    qos=self.config["mqtt"]["lwt"]["qos"],
                    retain=True,
                )
                for topic, message in self.prev_publish.items():
                    message = self.replace_values_with_none(message)
                    self.client.publish(
                        topic,
                        payload=message,
                    )
            else:
                logger.info("Power Up detected.")
                if self.kill:
                    self.kill = False
                    self.monitor_run_thread()
                self.client.publish(
                    f"{self.pref_topic}/lwt",
                    payload="ON",
                    qos=self.config["mqtt"]["lwt"]["qos"],
                    retain=True,
                )

    def on_message(self, client, userdata, msg):
        """MQTT message is received with a module command to excecute"""
        topic = msg.topic.replace(f"{self.pref_topic}/commands/", "")
        message = msg.payload
        logger.info("Message received %s: %s", topic, message)
        try:
            message = json.loads(message)
        except json.decoder.JSONDecodeError:
            message = message.decode()
        except Exception as err:
            logger.debug("Error reading message: %s", err)

        select_service = topic.split("/")
        addon = self.addons.get(select_service[0])
        if addon is not None:
            if hasattr(addon, "start_control"):
                try:
                    result = addon.start_control(select_service, message)
                    if result is not None:
                        result_topic = (
                            f"{self.pref_topic}/command_result/{topic.strip('/')}"
                        )
                        self.client.publish(result_topic, payload=result, retain=False)
                except Exception as err:
                    logger.error(
                        "Couldn't run command for module %s: %s, %s",
                        addon,
                        err,
                        traceback.format_exc(),
                    )

    def setup_discovery_entities(self, addon, service, exp_name, options):
        """Send discovery information on Home Assistant for controls"""
        discovery_template = {
            "availability": {
                "topic": f"{self.pref_topic}/lwt",
                "payload_available": "ON",
                "payload_not_available": "OFF",
            },
            "device": {
                "identifiers": [self.config["mqtt"]["clientId"]],
                "name": self.config["mqtt"]["clientId"],
                "model": f"{distro.name()} {distro.version()}",
                "manufacturer": "LNXlink",
                "sw_version": version,
            },
        }
        control_name_topic = exp_name.lower().replace(" ", "_")
        subtopic = addon.name.lower().replace(" ", "_")
        if "method" in options or options.get("subtopic", False):
            subcontrol = exp_name.lower().replace(" ", "_")
            subtopic = f"{subtopic}/{subcontrol}"
        state_topic = f"{self.pref_topic}/monitor_controls/{subtopic}"
        command_topic = f"{self.pref_topic}/commands/{service}/{control_name_topic}"

        lookup_options = {
            "value_template": {
                "value_template": options.get("value_template", ""),
            },
            "attributes_template": {
                "json_attributes_topic": state_topic,
                "json_attributes_template": options.get(
                    "attributes_template", "{{ value_json | tojson }}"
                ),
            },
            "icon": {"icon": options.get("icon", "")},
            "unit": {"unit_of_measurement": options.get("unit", "")},
            "title": {"title": options.get("title", "")},
            "entity_picture": {"entity_picture": options.get("entity_picture", "")},
            "device_class": {"device_class": options.get("device_class", "")},
            "state_class": {"state_class": options.get("state_class", "")},
            "entity_category": {"entity_category": options.get("entity_category", "")},
            "enabled": {"enabled_by_default": options.get("enabled", True)},
            "expire_after": {"expire_after": options.get("expire_after", "")},
            "install": {
                "command_topic": command_topic,
                "payload_install": options.get("install", ""),
            },
        }
        lookup_entities = {
            "sensor": {
                "state_topic": state_topic,
            },
            "binary_sensor": {
                "state_topic": state_topic,
            },
            "camera": {
                "topic": state_topic,
                "image_encoding": options.get("encoding"),
            },
            "image": {
                "image_topic": state_topic,
                "image_encoding": options.get("encoding"),
            },
            "update": {"state_topic": state_topic},
            "button": {
                "command_topic": command_topic,
                "payload_press": options.get("payload_press", "PRESS"),
            },
            "switch": {
                "state_topic": state_topic,
                "command_topic": command_topic,
                "payload_off": options.get("command_off", "OFF"),
                "payload_on": options.get("command_on", "ON"),
                "state_off": "OFF",
                "state_on": "ON",
            },
            "text": {
                "state_topic": state_topic,
                "command_topic": command_topic,
                "min": options.get("min", 0),
                "max": options.get("max", 255),
            },
            "number": {
                "state_topic": state_topic,
                "command_topic": command_topic,
                "min": options.get("min", 1),
                "max": options.get("max", 100),
                "step": options.get("step", 1),
            },
            "select": {
                "state_topic": state_topic,
                "command_topic": command_topic,
                "options": options.get("options", []),
            },
            "media_player": {
                "name": self.config["mqtt"]["clientId"],
                "state_state_topic": f"{state_topic}/state",
                "state_title_topic": f"{state_topic}/title",
                "state_artist_topic": f"{state_topic}/artist",
                "state_album_topic": f"{state_topic}/album",
                "state_duration_topic": f"{state_topic}/duration",
                "state_position_topic": f"{state_topic}/position",
                "state_volume_topic": f"{state_topic}/volume",
                "state_albumart_topic": f"{state_topic}/albumart",
                "state_mediatype_topic": f"{state_topic}/mediatype",
                "command_volume_topic": f"{command_topic}/set_volume",
                "command_play_topic": f"{command_topic}/play",
                "command_play_payload": "Play",
                "command_pause_topic": f"{command_topic}/pause",
                "command_pause_payload": "Pause",
                "command_playpause_topic": f"{command_topic}/playpause",
                "command_playpause_payload": "PlayPause",
                "command_next_topic": f"{command_topic}/next",
                "command_next_payload": "Next",
                "command_previous_topic": f"{command_topic}/previous",
                "command_previous_payload": "Previous",
                "command_playmedia_topic": f"{command_topic}/play_media",
            },
        }
        discovery = discovery_template.copy()
        discovery["name"] = exp_name
        discovery[
            "unique_id"
        ] = f"{self.config['mqtt']['clientId']}_{control_name_topic}"
        discovery.update(lookup_entities.get(options["type"], {}))
        for option in options:
            discovery.update(lookup_options.get(option, {}))

        if options["type"] not in lookup_entities:
            logger.error("Not supported: %s", options["type"])
            return
        if "value_template" in discovery and options["type"] in ["camera", "image"]:
            del discovery["json_attributes_topic"]
            del discovery["json_attributes_template"]
        self.client.publish(
            f"homeassistant/{options['type']}/lnxlink/{discovery['unique_id']}/config",
            payload=json.dumps(discovery),
            retain=True,
        )
        if options["type"] == "media_player":
            logger.info(
                "MQTT Media Player configuration name: lnxlink/%s",
                discovery["unique_id"],
            )

    def setup_discovery(self, filter_name=None):
        """First time setup of discovery for Home Assistant"""
        for service, addon in self.addons.items():
            if filter_name is not None and filter_name != service:
                continue
            if hasattr(addon, "exposed_controls"):
                for exp_name, options in addon.exposed_controls().items():
                    try:
                        self.setup_discovery_entities(addon, service, exp_name, options)
                    except Exception as err:
                        logger.error(
                            "%s: %s, %s", exp_name, err, traceback.format_exc()
                        )

    def restart_script(self):
        """Restarts itself"""
        logger.info("Restarting LNXlink...")
        os.execv(sys.executable, ["python"] + sys.argv)


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
    logging.getLogger("dasbus").setLevel(logging.WARNING)


def main():
    """Starts the app with some arguments"""
    description = (
        f"LNXlink {version} bridges this OS with Home Assistant through an MQTT broker."
    )
    parser = argparse.ArgumentParser(prog="lnxlink", description=description)
    parser.add_argument(
        "-c",
        "--config",
        help="Configuration file",
    )
    parser.add_argument(
        "-i",
        "--ignore-systemd",
        help="Runs without setting up SystemD service",
        action="store_true",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        help="Exclude modules from running",
        default=[],
        type=lambda t: [s.strip() for s in t.split(",")],
    )
    parser.add_argument(
        "-l",
        "--logging",
        help="Set the logging level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    parser.add_argument(
        "-s",
        "--setup",
        help="Runs only the setup configuration workflow",
        action="store_true",
    )
    parser.add_argument(
        "-v",
        "--version",
        help="Shows current version of LNXlink",
        action="store_true",
    )
    args = parser.parse_args()

    if args.version:
        print(version)
        sys.exit()
    if args.config is None:
        parser.print_help()
        parser.exit("\nSomething went wrong, --config condition was not set")
    config_file = os.path.abspath(args.config)
    setup_logger(config_file, args.logging)
    config_setup.setup_config(config_file)
    if args.setup:
        logger.info("The configuration exists under the file: %s", config_file)
        sys.exit()
    if not args.ignore_systemd:
        config_setup.setup_systemd(config_file)
    else:
        logger.info(
            "By not setting up the SystemD, LNXlink won't be able to start on boot..."
        )

    lnxlink = LNXlink(config_file)

    # Monitor for system changes (Shutdown/Suspend/Sleep)
    monitor_suspend = MonitorSuspend(lnxlink.temp_connection_callback)
    monitor_suspend.start()
    monitor_gracefulkiller = GracefulKiller(lnxlink.temp_connection_callback)

    # Starts the main app
    start_status = lnxlink.start(args.exclude)
    if start_status:
        while not monitor_gracefulkiller.kill_now:
            time.sleep(1.0)
        monitor_suspend.stop()
        lnxlink.disconnect()
    else:
        monitor_suspend.stop()


if __name__ == "__main__":
    main()
