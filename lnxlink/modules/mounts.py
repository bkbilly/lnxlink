"""Gets mount usage from all mounted directories"""
import logging
from lnxlink.modules.scripts.helpers import syscommand, import_install_package

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Mounts"
        self.lnxlink = lnxlink
        self.lib = {}
        self.mounts = self._get_mounts()

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        for device in self.mounts:
            att_temp = f"{{{{ value_json.get('{device}', {{}}).get('attributes', {{}}) | tojson }}}}"
            discovery_info[f"Mount {device}"] = {
                "type": "sensor",
                "icon": "mdi:harddisk",
                "unit": "%",
                "entity_category": "diagnostic",
                "state_class": "measurement",
                "value_template": f"{{{{ value_json.get('{device}', {{}}).get('percent') }}}}",
                "attributes_template": att_temp,
                "enabled": True,
            }
        return discovery_info

    def get_info(self):
        """Gather information from the system"""
        mounts = self._get_mounts()
        mounted = set(mounts) - set(self.mounts)
        unmounted = set(self.mounts) - set(mounts)
        for mount_name in unmounted:
            mounts[mount_name] = self.mounts[mount_name]
            self.mounts[mount_name]["attributes"]["connected"] = False
            self.mounts[mount_name]["percent"] = None
        self.mounts = mounts
        if len(mounted) > 0:
            self.lnxlink.setup_discovery("mounts")
        return self.mounts

    def _get_mounts(self):
        """Get a list of all mounts"""
        mounts = {}
        mount_directories = (
            self.lnxlink.config["settings"].get("mounts", {}).get("directories", [])
        )
        for mount_directory in mount_directories:
            unique_name, mount_data = self._calculate_size(mount_directory)
            mounts[unique_name] = mount_data

        if self.lnxlink.config["settings"].get("mounts", {}).get("autocheck", False):
            mounts.update(self._get_remote_mounts())

        return mounts

    def _calculate_size(self, mountpoint):
        unique_name = mountpoint
        unique_name = unique_name.replace(" ", "_")
        unique_name = unique_name.replace("=", "_")
        unique_name = unique_name.replace(".", "_")
        unique_name = unique_name.replace(",", "")
        unique_name = unique_name.replace("/", "")
        unique_name = unique_name.replace(",", "")
        unique_name = unique_name.replace(":", "")
        unique_name = unique_name.replace("-", "")

        data = {
            "percent": None,
            "attributes": {
                "mountpoint": mountpoint,
                "total": None,
                "filesystem": None,
                "mount_on": None,
                "connected": False,
            },
        }
        stdout, _, _ = syscommand(["df", mountpoint])
        if len(stdout.split("\n")) == 2:
            filesystem, size_str, _, _, used, mounton = stdout.split("\n")[1].split()
            data["percent"] = int(used.replace("%", ""))
            data["attributes"]["total"] = round(int(size_str) / 1024 / 1024, 0)
            data["attributes"]["filesystem"] = filesystem
            data["attributes"]["mount_on"] = mounton
            data["attributes"]["connected"] = True
        return unique_name, data

    def _requirements(self):
        self.lib["gi"] = import_install_package(
            "PyGObject", ">=3.44.0", "gi.repository.Gio"
        )

    def _get_remote_mounts(self):
        """Uses Gnome GVFS to find remote mounts mounted by the system"""
        if "gi" not in self.lib:
            self._requirements()

        mounts_dict = {}
        volume_monitor = self.lib["gi"].repository.Gio.VolumeMonitor.get()
        mounts = volume_monitor.get_mounts()
        for mount in mounts:
            name = mount.get_name()
            mounttype = mount.get_root().get_uri_scheme()
            native = mount.get_root().is_native()
            mountpoint = mount.get_root().get_path()
            if not native:
                unique_name, mount_data = self._calculate_size(mountpoint)
                if mount_data["percent"] is not None:
                    mounts_dict[unique_name] = mount_data
                    mounts_dict[unique_name]["attributes"]["name"] = name
                    mounts_dict[unique_name]["attributes"]["mount_type"] = mounttype
        return mounts_dict
