"""Gets the coordinates of the maching using WiFi Networks"""
import io
import csv
import time
import logging
from shutil import which

import requests
from lnxlink.modules.scripts.helpers import syscommand


logger = logging.getLogger("lnxlink")


def scan_wifi_nmcli():
    """Command to list Wi-Fi access points with their details"""
    command = ["nmcli", "-t", "-f", "BSSID,SSID,SIGNAL", "dev", "wifi", "list"]
    stdout, _, _ = syscommand(command, timeout=7)
    output_buffer = io.StringIO(stdout)
    csv_reader = csv.reader(output_buffer, delimiter=":", escapechar="\\")

    wifi_aps = []
    for row in csv_reader:
        if len(row) >= 3:
            bssid = row[0].strip().upper()
            ssid = row[1].strip()
            signal_str = row[2].strip()

            if ssid == "--" or ssid.lower() == "null":
                ssid = None  # Represent hidden/empty SSIDs as None
            try:
                signal = int(signal_str)
            except ValueError:
                continue

            wifi_aps.append(
                {
                    "macAddress": bssid,
                    "ssid": ssid,
                    "signalStrength": signal,
                }
            )
    return wifi_aps


def get_location_from_beacondb(wifi_aps_data, consider_ip=False):
    """Get the coordinates from BeaconDB"""
    try:
        response = requests.post(
            "https://api.beacondb.net/v1/geolocate",
            headers={
                "Content-Type": "application/json",
            },
            json={
                "wifiAccessPoints": wifi_aps_data,
                "considerIp": consider_ip,
            },
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        logger.error("Error querying BeaconDB: %s", err)
        return None


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "BeaconDB"
        self.lnxlink = lnxlink
        self.last_time = 0
        self.update_interval = 360  # Check for position every 6 minutes
        self.position = None
        if which("nmcli") is None:
            raise SystemError("System command 'nmcli' not found")
        self.lnxlink.add_settings(
            "beacondb",
            {
                "wifi_positions": [
                    {
                        "ssid": "mywifi_example",
                        "latitude": 40.644400,
                        "longitude": 21.494300,
                        "accuracy": 2500,
                    },
                ],
            },
        )

    def get_info(self):
        """Gather information from the system"""
        cur_time = time.time()
        if cur_time - self.last_time > self.update_interval:
            self.last_time = cur_time
            wifi_data = scan_wifi_nmcli()
            use_localconfig = False
            for config in self.lnxlink.config["settings"]["beacondb"]["wifi_positions"]:
                if any(data["ssid"] == config.get("ssid") for data in wifi_data):
                    use_localconfig = True
                    self.position = {
                        "latitude": config.get("latitude"),
                        "longitude": config.get("longitude"),
                        "gps_accuracy": config.get("accuracy", 200),
                    }
            location_result = get_location_from_beacondb(wifi_data, consider_ip=True)
            if location_result and not use_localconfig:
                self.position = {
                    "latitude": location_result.get("location", {}).get("lat"),
                    "longitude": location_result.get("location", {}).get("lng"),
                    "gps_accuracy": location_result.get("accuracy"),
                }
        return self.position

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "BeaconDB": {
                "type": "device_tracker",
                "entity_category": "diagnostic",
            }
        }
