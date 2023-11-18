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
from . import modules
from . import config_setup
from .system_monitor import MonitorSuspend, GracefulKiller
from .modules.scripts.helpers import syscommand


# Get the current version of the app
version = importlib.metadata.version(__package__ or __name__)
path = os.path.dirname(os.path.realpath(__file__))
if os.path.exists(os.path.join(path, "edit.txt")):
    version += "+edit"
    git_hash, _, return_code = syscommand(f"git -C {path} rev-parse --short HEAD")
    if return_code == 0:
        version += f"-{git_hash}"

logger = logging.getLogger("lnxlink")


class LNXlink:
    """Start LNXlink service that loads all modules and connects to MQTT"""

    version = version
    path = path

    def __init__(self, config_path):

        logger.info("LNXlink %s, Python %s", self.version, platform.python_version())
        self.kill = False
        self.display = None
        self.inference_times = {}

        # Read configuration from yaml file
        self.pref_topic = "lnxlink"
        self.config = self.read_config(config_path)

        # Run each addon included in the modules folder
        self.addons = {}
        conf_modules = self.config.get("modules", None)
        custom_modules = self.config.get("custom_modules", None)
        conf_exclude = self.config.get("exclude", [])
        conf_exclude = [] if conf_exclude is None else conf_exclude
        loaded_modules = modules.parse_modules(
            conf_modules, custom_modules, conf_exclude
        )
        for _, addon in loaded_modules.items():
            try:
                tmp_addon = addon(self)
                self.addons[addon.service] = tmp_addon
            except Exception as err:
                logger.error(
                    "Error with addon %s, please remove it from your config: %s, %s",
                    addon.service,
                    err,
                    traceback.format_exc(),
                )

        # Setup MQTT
        self.client = mqtt.Client()
        self.setup_mqtt()

    def publish_monitor_data(self, topic, pub_data):
        """Publish info data to mqtt in the correct format"""
        # logger.info(topic, pub_data, type(pub_data))
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
        if pub_data is None:
            return
        if isinstance(pub_data, (dict, list)):
            pub_data = json.dumps(pub_data)
        self.client.publish(
            topic, payload=pub_data, retain=self.config["mqtt"]["lwt"]["retain"]
        )

    def run_modules(self, methods_to_run):
        """Runs the methods of each module"""
        for method in methods_to_run:
            subtopic = method["name"].lower().replace(" ", "_")
            topic = f"{self.pref_topic}/monitor_controls/{subtopic}"

            try:
                start_time = time.time()
                pub_data = method["method"]()
                diff_time = round(time.time() - start_time, 5)
                self.inference_times[f"{method['name']}"] = diff_time
                self.publish_monitor_data(topic, pub_data)
            except Exception as err:
                logger.error(
                    "Error with addon %s: %s, %s",
                    method["name"],
                    err,
                    traceback.format_exc(),
                )

    def monitor_run(self):
        """Gets information from each Addon and sends it to MQTT"""
        methods_to_run = []
        for service, addon in self.addons.items():
            if hasattr(addon, "get_info"):
                methods_to_run.append(
                    {
                        "name": addon.name,
                        "method": addon.get_info,
                        "service": service,
                    }
                )
            if hasattr(addon, "exposed_controls"):
                for exp_name, options in addon.exposed_controls().items():
                    if options.get("method") is not None:
                        methods_to_run.append(
                            {
                                "name": f"{addon.name}/{exp_name}",
                                "method": options["method"],
                                "service": service,
                            }
                        )
        self.run_modules(methods_to_run)

    def monitor_run_thread(self):
        """Runs method to get sensor information every prespecified interval"""
        self.monitor_run()

        interval = self.config.get("update_interval", 1)
        if not self.kill:
            monitor = threading.Timer(interval, self.monitor_run_thread)
            monitor.start()

    def setup_mqtt(self):
        """Creates the mqtt object"""
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.username_pw_set(
            self.config["mqtt"]["auth"]["user"], self.config["mqtt"]["auth"]["pass"]
        )
        if self.config["mqtt"]["auth"].get("tls", False):
            self.client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_NONE)
            self.client.tls_insecure_set(True)
        self.client.connect(
            self.config["mqtt"]["server"], self.config["mqtt"]["port"], 60
        )
        self.client.loop_start()

    def read_config(self, config_path):
        """Reads the config file and prepares module names for import"""
        with open(config_path, "r", encoding="utf8") as file:
            conf = yaml.load(file, Loader=yaml.FullLoader)

        if "prefix" in conf["mqtt"] and "clientId" in conf["mqtt"]:
            self.pref_topic = f"{conf['mqtt']['prefix']}/{conf['mqtt']['clientId']}"
        self.pref_topic = self.pref_topic.lower()

        conf["modules"] = conf.get("modules")
        conf["custom_modules"] = conf.get("custom_modules")
        if conf["modules"] is not None:
            conf["modules"] = [x.lower().replace("-", "_") for x in conf["modules"]]
        return conf

    def on_connect(self, client, userdata, flags, rcode):
        """Callback for MQTT connect which reports the connection status
        back to MQTT server"""
        logger.info("Connected to MQTT with code %s", rcode)
        client.subscribe(f"{self.pref_topic}/commands/#")
        if self.config["mqtt"]["lwt"]["enabled"]:
            self.client.publish(
                f"{self.pref_topic}/lwt",
                payload=self.config["mqtt"]["lwt"]["connectMsg"],
                qos=self.config["mqtt"]["lwt"]["qos"],
                retain=self.config["mqtt"]["lwt"]["retain"],
            )
        if self.config["mqtt"]["discovery"]["enabled"]:
            self.setup_discovery()
        self.kill = False
        self.monitor_run_thread()

    def disconnect(self, *args):
        """Reports to MQTT server that the service has stopped"""
        logger.info("Disconnected from MQTT.")
        if self.config["mqtt"]["lwt"]["enabled"]:
            self.client.publish(
                f"{self.pref_topic}/lwt",
                payload=self.config["mqtt"]["lwt"]["disconnectMsg"],
                qos=self.config["mqtt"]["lwt"]["qos"],
                retain=self.config["mqtt"]["lwt"]["retain"],
            )
        self.kill = True
        self.client.disconnect()

    def temp_connection_callback(self, status):
        """Report the connection status to MQTT server"""
        self.kill = True
        if self.config["mqtt"]["lwt"]["enabled"]:
            if status:
                logger.info("Power Down detected.")
                self.client.publish(
                    f"{self.pref_topic}/lwt",
                    payload=self.config["mqtt"]["lwt"]["disconnectMsg"],
                    qos=self.config["mqtt"]["lwt"]["qos"],
                    retain=self.config["mqtt"]["lwt"]["retain"],
                )
            else:
                logger.info("Power Up detected.")
                if self.kill:
                    self.kill = False
                    self.monitor_run_thread()
                self.client.publish(
                    f"{self.pref_topic}/lwt",
                    payload=self.config["mqtt"]["lwt"]["connectMsg"],
                    qos=self.config["mqtt"]["lwt"]["qos"],
                    retain=self.config["mqtt"]["lwt"]["retain"],
                )

    def on_message(self, client, userdata, msg):
        """MQTT message is received with a module command to excecute"""
        topic = msg.topic.replace(f"{self.pref_topic}/commands/", "")
        message = msg.payload
        logger.info("Message received %s: %s", topic, message)
        try:
            message = json.loads(message)
        except Exception as err:
            message = message.decode()
            logger.debug("String could not be converted to JSON: %s", err)

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
        if "method" in options:
            subcontrol = exp_name.lower().replace(" ", "_")
            subtopic = f"{subtopic}/{subcontrol}"
        state_topic = f"{self.pref_topic}/monitor_controls/{subtopic}"
        command_topic = f"{self.pref_topic}/commands/{service}/{control_name_topic}/"

        lookup_options = {
            "value_template": {
                "value_template": options.get("value_template", ""),
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
            "button": {"command_topic": command_topic},
            "switch": {
                "state_topic": state_topic,
                "command_topic": command_topic,
                "payload_off": "OFF",
                "payload_on": "ON",
            },
            "text": {
                "state_topic": state_topic,
                "command_topic": command_topic,
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
            retain=self.config["mqtt"]["lwt"]["retain"],
        )

    def setup_discovery(self):
        """First time setup of discovery for Home Assistant"""
        for service, addon in self.addons.items():
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


def setup_logger(config_path):
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
    logging.basicConfig(level=logging.INFO)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)


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
        default="/etc/config.yaml",
        required=True,
    )
    args = parser.parse_args()

    config_file = os.path.abspath(args.config)
    setup_logger(config_file)
    config_setup.setup_config(config_file)
    config_setup.setup_systemd(config_file)
    lnxlink = LNXlink(config_file)

    # Monitor for system changes (Shutdown/Suspend/Sleep)
    monitor_suspend = MonitorSuspend(lnxlink.temp_connection_callback)
    monitor_suspend.start()
    monitor_gracefulkiller = GracefulKiller(lnxlink.temp_connection_callback)
    while not monitor_gracefulkiller.kill_now:
        time.sleep(0.2)
    monitor_suspend.stop()
    lnxlink.disconnect()


if __name__ == "__main__":
    main()
