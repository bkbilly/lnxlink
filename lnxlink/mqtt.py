"""MQTT methods"""


import asyncio
import json
import logging
import os
import ssl
import threading
import time
import traceback
from dataclasses import dataclass

import aiohttp
import distro
import paho.mqtt.client as mqtt
import requests

from lnxlink.modules.scripts import helpers

logger = logging.getLogger("lnxlink")


@dataclass
class PublishInfo:
    """Small paho-compatible publish result for alternate transports."""

    rc: int
    mid: int


@dataclass
class CommandMessage:
    """MQTT-like command message passed to the existing on_message handler."""

    topic: str
    payload: bytes


class DirectMQTTClient:
    """Direct MQTT broker client using paho-mqtt."""

    def __init__(self, config):
        self.config = config
        self._disconnecting = False
        if hasattr(mqtt, "CallbackAPIVersion"):
            self.client = mqtt.Client(
                client_id=f"LNXlink-{self.config['mqtt']['clientId']}",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            )
        else:
            self.client = mqtt.Client(
                client_id=f"LNXlink-{self.config['mqtt']['clientId']}"
            )

    def _setup_auth(self):
        """Configure authentication and TLS certificates for direct MQTT."""
        keyfile = self.config["mqtt"]["auth"].get("keyfile")
        keyfile = None if keyfile == "" else keyfile
        certfile = self.config["mqtt"]["auth"].get("certfile")
        certfile = None if certfile == "" else certfile
        ca_certs = self.config["mqtt"]["auth"].get("ca_certs")
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

    def connect(self, on_connect, on_message, on_disconnect, on_publish):
        """Connect to the configured MQTT broker directly."""
        self.client.on_connect = on_connect
        self.client.on_message = on_message
        self.client.on_disconnect = on_disconnect
        self.client.on_publish = on_publish

        self._setup_auth()
        if self.config["mqtt"]["lwt"]["enabled"]:
            self.client.will_set(
                f"{self.config['pref_topic']}/lwt",
                payload="OFF",
                qos=self.config["mqtt"]["lwt"]["qos"],
                retain=True,
            )
        keepalive = self.config.get("mqtt", {}).get("keepalive")
        if keepalive is None:
            keepalive = int(round(int(self.config.get("update_interval", 5)) * 1.5, 0))
        else:
            keepalive = int(keepalive)
        try:
            self.client.connect(
                host=self.config["mqtt"]["server"],
                port=self.config["mqtt"]["port"],
                keepalive=keepalive,
            )
        except ssl.SSLCertVerificationError:
            logger.info("TLS not verified, using insecure connection instead")
            self.client.tls_insecure_set(True)
            try:
                self.client.connect(
                    host=self.config["mqtt"]["server"],
                    port=self.config["mqtt"]["port"],
                    keepalive=keepalive,
                )
            except Exception as err:
                logger.error(
                    "Error establishing connection to MQTT broker: %s, %s",
                    err,
                    traceback.format_exc(),
                )
                return False
        except Exception as err:
            logger.error(
                "Error establishing connection to MQTT broker: %s, %s",
                err,
                traceback.format_exc(),
            )
            return False
        self.client.loop_start()
        return True

    def publish(self, topic, payload, qos=1, retain=True):
        """Publishes message using direct MQTT broker."""
        msg_info = self.client.publish(
            topic,
            payload=payload,
            qos=qos,
            retain=retain,
        )
        logger.debug("Message RC Code: %s, MQTT Number: %s", msg_info.rc, msg_info.mid)
        return msg_info

    def reconnect(self):
        """Reconnect to direct MQTT broker."""
        logger.info("Reconnecting to MQTT")
        self._disconnecting = False
        self.client.disconnect()
        time.sleep(2)
        self.client.reconnect()
        time.sleep(3)

    def disconnect(self):
        """Disconnect from direct MQTT broker."""
        self._disconnecting = True
        self.client.disconnect()
        logger.info("Disconnected from MQTT.")

    def subscribe(self, topic):
        """Subscribe to topic on direct MQTT broker."""
        return self.client.subscribe(topic)


# pylint: disable=too-many-instance-attributes
class HomeAssistantApiClient:
    """MQTT client transport via Home Assistant HTTP and WebSocket APIs."""

    def __init__(self, config):
        self.config = config
        self._publish_mid = 0
        self._publish_lock = threading.Lock()
        self._stop_event = threading.Event()
        self.is_disconnecting = False
        self._ws_thread = None
        self._on_message_callback = None
        self.session = requests.Session()

    def _get_ha_config(self):
        """Return Home Assistant API transport configuration."""
        ha_config = self.config["mqtt"].get("homeassistant", {})
        return {
            "url": str(ha_config.get("url", "")).rstrip("/"),
            "token": self._get_token(ha_config),
            "timeout": float(ha_config.get("timeout", 20)),
            "verify_ssl": self._config_bool(ha_config.get("verify_ssl", True)),
            "subscribe_commands": self._config_bool(
                ha_config.get("subscribe_commands", True)
            ),
        }

    def _config_bool(self, value):
        """Parse boolean config values."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ["1", "true", "yes", "on"]
        return bool(value)

    def _get_token(self, ha_config):
        """Read the Home Assistant long-lived access token."""
        token = str(ha_config.get("token", "")).strip()
        if not token:
            return ""

        token_path = os.path.expanduser(token)
        if os.path.isfile(token_path):
            try:
                with open(token_path, encoding="UTF-8") as file:
                    return file.read().strip()
            except OSError as err:
                logger.error("Could not read Home Assistant token file: %s", err)
                return ""

        return token

    def connect(self, on_connect, on_message, on_disconnect, on_publish):
        """Connect to Home Assistant API for MQTT publish and commands."""
        ha_config = self._get_ha_config()
        if not ha_config["url"] or not ha_config["token"]:
            logger.error(
                "Home Assistant MQTT API transport needs mqtt.homeassistant.url "
                "and token"
            )
            return False

        self._on_message_callback = on_message
        logger.info("Home Assistant MQTT API transport: %s", ha_config["url"])
        on_connect(self, None, None, 0)
        if ha_config["subscribe_commands"]:
            self._start_websocket()
        return True

    def publish(self, topic, payload, qos=1, retain=True):
        """Publish MQTT message through Home Assistant's mqtt.publish service."""
        ha_config = self._get_ha_config()
        if payload is None:
            payload = ""
        elif isinstance(payload, bytes):
            payload = payload.decode("UTF-8")
        elif not isinstance(payload, str):
            payload = str(payload)

        timeout = 2.0 if self.is_disconnecting else ha_config["timeout"]

        try:
            response = self.session.post(
                f"{ha_config['url']}/api/services/mqtt/publish",
                headers={
                    "Authorization": f"Bearer {ha_config['token']}",
                    "Content-Type": "application/json",
                },
                json={
                    "topic": topic,
                    "payload": payload,
                    "qos": qos,
                    "retain": retain,
                },
                timeout=timeout,
                verify=ha_config["verify_ssl"],
            )
            response.raise_for_status()
            rc = 0
        except Exception as err:
            logger.error("Home Assistant MQTT publish failed: %s", err)
            logger.debug(traceback.format_exc())
            rc = 1

        with self._publish_lock:
            self._publish_mid += 1
            mid = self._publish_mid

        logger.debug("Message RC Code: %s, MQTT Number: %s", rc, mid)
        return PublishInfo(rc=rc, mid=mid)

    def reconnect(self):
        """Reconnect to Home Assistant MQTT WebSocket."""
        logger.info("Reconnecting to Home Assistant MQTT websocket")
        self._stop_event.set()
        if self._ws_thread and self._ws_thread.is_alive():
            self._ws_thread.join(timeout=2)
        self._start_websocket()

    def disconnect(self):
        """Disconnect from Home Assistant API."""
        self.is_disconnecting = True
        self._stop_event.set()
        if self._ws_thread and self._ws_thread.is_alive():
            self._ws_thread.join(timeout=2)
        try:
            self.session.close()
        except Exception:
            pass
        logger.info("Disconnected from Home Assistant MQTT API.")

    def subscribe(self, topic):
        """Subscriptions are owned by the websocket bridge."""
        logger.debug("Home Assistant websocket subscribes to %s", topic)

    def _start_websocket(self):
        """Start the Home Assistant websocket MQTT subscription thread."""
        if self._ws_thread and self._ws_thread.is_alive():
            return
        self._stop_event.clear()
        self._ws_thread = threading.Thread(
            target=self._run_websocket,
            daemon=True,
        )
        self._ws_thread.start()

    def _run_websocket(self):
        """Run the Home Assistant websocket bridge in its own event loop."""
        try:
            asyncio.run(self._websocket_loop())
        except Exception as err:
            logger.error("Home Assistant MQTT websocket failed: %s", err)
            logger.debug(traceback.format_exc())

    async def _websocket_loop(self):
        """Subscribe to command topics through Home Assistant websocket."""
        ha_config = self._get_ha_config()
        command_topic = f"{self.config['pref_topic']}/commands/#"
        while not self._stop_event.is_set():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(
                        f"{ha_config['url']}/api/websocket",
                        heartbeat=30,
                        ssl=ha_config["verify_ssl"],
                    ) as websocket:
                        auth_required = await websocket.receive_json()
                        if auth_required.get("type") != "auth_required":
                            raise RuntimeError(
                                f"Unexpected Home Assistant websocket hello: {auth_required}"
                            )
                        await websocket.send_json(
                            {
                                "type": "auth",
                                "access_token": ha_config["token"],
                            }
                        )
                        auth_result = await websocket.receive_json()
                        if auth_result.get("type") != "auth_ok":
                            raise RuntimeError(
                                f"Home Assistant websocket auth failed: {auth_result}"
                            )
                        await websocket.send_json(
                            {
                                "id": 1,
                                "type": "mqtt/subscribe",
                                "topic": command_topic,
                            }
                        )
                        subscribe_result = await websocket.receive_json()
                        if not subscribe_result.get("success"):
                            raise RuntimeError(
                                "Home Assistant MQTT subscribe failed: "
                                f"{subscribe_result}"
                            )
                        logger.info(
                            "Subscribed to MQTT commands through Home Assistant API: %s",
                            command_topic,
                        )
                        await self._receive_commands(websocket)
            except Exception as err:
                if not self._stop_event.is_set():
                    logger.error("Home Assistant MQTT websocket disconnected: %s", err)
                    logger.debug(traceback.format_exc())
                    await asyncio.sleep(5)

    async def _receive_commands(self, websocket):
        """Forward Home Assistant websocket MQTT events to the command handler."""
        while not self._stop_event.is_set():
            try:
                message = await websocket.receive(timeout=1)
            except asyncio.TimeoutError:
                continue
            if message.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(message.data)
                event = data.get("event", {})
                topic = event.get("topic")
                payload = event.get("payload", "")
                if topic and self._on_message_callback is not None:
                    if not isinstance(payload, str):
                        payload = json.dumps(payload)
                    self._on_message_callback(
                        self,
                        None,
                        CommandMessage(topic=topic, payload=payload.encode("UTF-8")),
                    )
            elif message.type in (
                aiohttp.WSMsgType.CLOSED,
                aiohttp.WSMsgType.CLOSE,
                aiohttp.WSMsgType.ERROR,
            ):
                raise RuntimeError(f"websocket closed: {message.type}")


class MQTT:
    """Start LNXlink service that loads all modules and connects to MQTT"""

    def __init__(self, config):
        self.config = config
        self.publish_rc_code = 0
        self.transport = self.config["mqtt"].get("transport", "mqtt")
        self._on_connect_callback = None
        self._on_message_callback = None
        self._on_transport_switch_callback = None

        if self.transport == "homeassistant_api":
            self.client = HomeAssistantApiClient(config)
        else:
            self.client = DirectMQTTClient(config)

    def publish(self, topic, payload, retain=True):
        """Publishes messages to the MQTT broker"""
        qos = self.config["mqtt"]["lwt"]["qos"]
        msg_info = self.client.publish(topic, payload, qos=qos, retain=retain)
        self.publish_rc_code = msg_info.rc
        return msg_info

    @property
    def delivery_token(self):
        """Identify the client responsible for the current delivery attempt."""
        return self.client

    def publish_accepted(self, msg_info):
        """Return whether the transport accepted responsibility for delivery."""
        if msg_info.rc == mqtt.MQTT_ERR_SUCCESS:
            return True
        return (
            self.transport != "auto"
            and isinstance(self.client, DirectMQTTClient)
            and self.config["mqtt"]["lwt"]["qos"] > 0
            and msg_info.rc == mqtt.MQTT_ERR_NO_CONN
        )

    def reconnect(self):
        """Try to reconnect to broker"""
        self.publish_rc_code = 0
        self.client.reconnect()

    def disconnect(self):
        """Used when exiting"""
        self.send_lwt("OFF")
        self.client.disconnect()

    def send_lwt(self, status):
        """Sends the status of lwt, ON or OFF"""
        if status == "OFF" and not self.config["mqtt"]["lwt"]["enabled"]:
            return
        self.publish(
            f"{self.config['pref_topic']}/lwt",
            payload=status,
            retain=True,
        )

    def setup_mqtt(self, on_connect, on_message, on_transport_switch=None):
        """Creates the mqtt object"""
        self._on_connect_callback = on_connect
        self._on_message_callback = on_message
        self._on_transport_switch_callback = on_transport_switch

        if self.client.connect(
            on_connect=on_connect,
            on_message=on_message,
            on_disconnect=self.on_disconnect,
            on_publish=self.on_publish,
        ):
            return True

        if self.transport == "auto":
            logger.warning(
                "Direct MQTT connection failed in auto transport mode; "
                "using Home Assistant MQTT API instead"
            )
            return self.switch_to_homeassistant_api()

        return False

    def switch_to_homeassistant_api(self):
        """Switch the active transport to Home Assistant's MQTT API."""
        if isinstance(self.client, HomeAssistantApiClient):
            return True
        if self._on_connect_callback is None or self._on_message_callback is None:
            logger.error("Cannot switch to Home Assistant MQTT API before setup")
            return False

        logger.info("Switching MQTT transport to Home Assistant API")
        self.client.disconnect()
        if self._on_transport_switch_callback is not None:
            self._on_transport_switch_callback()
        self.client = HomeAssistantApiClient(self.config)
        return self.client.connect(
            on_connect=self._on_connect_callback,
            on_message=self._on_message_callback,
            on_disconnect=self.on_disconnect,
            on_publish=self.on_publish,
        )

    def on_publish(self, client, userdata, mid, *args):
        """Trying to reconnect if the reason code is not Success"""
        reason_code = args[0] if args else None
        if reason_code is not None and reason_code != "Success":
            logger.error("Publish Error, trying to reconnect...")
            self.reconnect()

    def on_disconnect(self, *args):
        """Disconnected from MQTT broker"""
        if getattr(self.client, "_disconnecting", False):
            return
        logger.warning("Lost connection to MQTT Broker...")
        if self.transport == "auto":
            threading.Thread(
                target=self.switch_to_homeassistant_api, daemon=True
            ).start()

    def get_rcode_name(self, rcode):
        """Returns the rcode message"""
        if isinstance(self.client, HomeAssistantApiClient) and rcode == 0:
            return "Success"
        return mqtt.connack_string(rcode)

    # pylint: disable=too-many-locals
    def setup_discovery_entities(self, addon, service, exp_name, options):
        """Send discovery information on Home Assistant for controls"""
        discovery_template = {
            "device": {
                "identifiers": [self.config["mqtt"]["clientId"]],
                "name": self.config["mqtt"]["clientId"],
                "model": f"{distro.name()} {distro.version()}",
                "manufacturer": "LNXlink",
                "sw_version": self.config["version"],
            },
        }
        if options.get("use_availability", True):
            discovery_template["availability"] = {
                "topic": f"{self.config['pref_topic']}/lwt",
                "payload_available": "ON",
                "payload_not_available": "OFF",
            }

        subtopic = helpers.text_to_topic(addon.name)
        if "method" in options or options.get("subtopic", False):
            subcontrol = helpers.text_to_topic(exp_name)
            subtopic = f"{subtopic}/{subcontrol}"
        topic_category = options.get("topic_category", "monitor_controls")
        category_path = f"/{topic_category}" if topic_category else ""
        state_topic = f"{self.config['pref_topic']}{category_path}/{subtopic}"
        control_name_topic = helpers.text_to_topic(exp_name)
        command_topic = (
            f"{self.config['pref_topic']}/commands/{service}/{control_name_topic}"
        )

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
            "schema": {"schema": options.get("schema", "")},
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
            "device_tracker": {
                "json_attributes_topic": state_topic,
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
            "notify": {
                "command_topic": command_topic,
                "json_attributes_topic": state_topic,
                "name": self.config["mqtt"]["clientId"],
            },
            "infrared": {
                "platform": "infrared",
                "command_topic": command_topic,
                "state_topic": state_topic,
            },
            "event": {
                "automation_type": "trigger",
                "topic": state_topic,
                "type": options.get("event_type", "button_short_press"),
                "subtype": options.get("event_subtype", "turn_on"),
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
            return None
        if "value_template" in discovery and options["type"] in ["camera", "image"]:
            discovery.pop("json_attributes_topic", None)
            discovery.pop("json_attributes_template", None)
        discovery_prefix = self.config["mqtt"]["discovery"]["prefix"]
        discovery_component = (
            "device_automation" if options["type"] == "event" else options["type"]
        )
        discovery_unique_id = discovery["unique_id"]
        if options["type"] == "event":
            discovery = {
                key: discovery[key]
                for key in (
                    "automation_type",
                    "device",
                    "topic",
                    "type",
                    "subtype",
                )
            }
        discovery_topic = (
            f"{discovery_prefix}/{discovery_component}/lnxlink/"
            f"{discovery_unique_id}/config"
        )
        msg_info = self.publish(
            discovery_topic,
            payload=json.dumps(discovery),
        )
        if getattr(msg_info, "rc", None) != 0:
            raise RuntimeError(
                f"Could not publish Home Assistant discovery topic "
                f"{discovery_topic}: MQTT RC {getattr(msg_info, 'rc', None)}"
            )
        if options["type"] == "media_player":
            logger.info(
                "MQTT Media Player configuration name: lnxlink/%s",
                discovery["unique_id"],
            )
        return discovery_topic
