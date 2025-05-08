"""MQTT methods"""

import ssl
import time
import logging
import traceback
import paho.mqtt.client as mqtt

logger = logging.getLogger("lnxlink")


class MQTT:
    """Start LNXlink service that loads all modules and connects to MQTT"""

    def __init__(self, config):
        self.config = config
        self.publish_rc_code = 0

        # Setup mqtt client object
        if hasattr(mqtt, "CallbackAPIVersion"):
            self.client = mqtt.Client(
                client_id=f"LNXlink-{self.config['mqtt']['clientId']}",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            )
        else:
            self.client = mqtt.Client(
                client_id=f"LNXlink-{self.config['mqtt']['clientId']}"
            )

    def publish(self, topic, payload):
        """Publishes messages to the MQTT broker"""
        msg_info = self.client.publish(
            topic,
            payload=payload,
            qos=self.config["mqtt"]["lwt"]["qos"],
            retain=self.config["mqtt"]["lwt"]["retain"],
        )
        logger.debug("Message RC Code: %s, MQTT Number: %s", msg_info.rc, msg_info.mid)
        self.publish_rc_code = msg_info.rc
        # if self.publish_rc_code != 0:
        #     logger.error("Publish RC Code Error, trying to reconnect...")
        #     self.publish_rc_code = 0
        #     self.client.disconnect()
        #     time.sleep(2)
        #     self.client.reconnect()
        #     time.sleep(3)
        return msg_info

    def reconnect(self):
        """Try to reconnect to broker"""
        logger.info("Reconnecting to MQTT")
        self.publish_rc_code = 0
        self.client.disconnect()
        time.sleep(2)
        self.client.reconnect()
        time.sleep(3)

    def disconnect(self):
        """Used when exiting"""
        self.client.disconnect()
        logger.info("Disconnected from MQTT.")
        if self.config["mqtt"]["lwt"]["enabled"]:
            self.send_lwt("OFF")

    def send_lwt(self, status):
        """Sends the status of lwt"""
        self.client.publish(
            f"{self.config['pref_topic']}/lwt",
            payload=status,
            qos=self.config["mqtt"]["lwt"]["qos"],
            retain=True,
        )

    def setup_mqtt(self, on_connect, on_message):
        """Creates the mqtt object"""
        self.client.on_connect = on_connect
        self.client.on_message = on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish

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
                f"{self.config['pref_topic']}/lwt",
                payload="OFF",
                qos=self.config["mqtt"]["lwt"]["qos"],
                retain=True,
            )
        try:
            self.client.connect(
                host=self.config["mqtt"]["server"],
                port=self.config["mqtt"]["port"],
                keepalive=60,
            )
        except ssl.SSLCertVerificationError:
            logger.info("TLS not verified, using insecure connection instead")
            self.client.tls_insecure_set(True)
            self.client.connect(
                host=self.config["mqtt"]["server"],
                port=self.config["mqtt"]["port"],
                keepalive=60,
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

    # pylint: disable=too-many-arguments
    def on_publish(self, client, userdata, mid, reason_code, properties):
        """Trying to reconnect if the reason code is not Success"""
        if reason_code != "Success":
            logger.error("Publish Error, trying to reconnect...")
            self.reconnect()

    def on_disconnect(self, *args):
        """Disconnected from MQTT broker"""
        logger.warning("Lost connection to MQTT Broker...")

    def get_rcode_name(self, rcode):
        """Returns the rcode message"""
        return mqtt.connack_string(rcode)
