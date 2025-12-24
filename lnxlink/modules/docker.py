"""Manage containers; toggle status, check for updates, or prune images"""
import time
import logging
from lnxlink.modules.scripts.docker_update_status import DockerUpdateStatus
from lnxlink.modules.scripts.helpers import import_install_package

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    # pylint: disable=too-many-branches
    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Docker"
        self.lnxlink = lnxlink
        self.docker = import_install_package("docker", ">=7.0.0")
        if self.docker is None:
            raise SystemError("Docker package not found")
        try:
            # client = docker.from_env()
            self.client = self.docker.DockerClient(base_url="unix://run/docker.sock")
        except Exception as err:
            raise SystemError(f"Docker instance not found: {err}") from err
        self.lnxlink.add_settings(
            "docker",
            {
                "include": [],
                "exclude": [],
                "check_update": 24,
                "expose_controls": True,
            },
        )
        self.prev_update = 0
        self.images_remoteinfo = []
        self.containers = self._get_containers()

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        for container in self.containers:
            attr_templ = f"{{{{ value_json.get('{container}', {{}}).get('attrs', {{}}) | tojson }}}}"
            if self.lnxlink.config["settings"]["docker"]["expose_controls"]:
                discovery_info[f"Docker {container}"] = {
                    "type": "switch",
                    "icon": "mdi:docker",
                    "value_template": f"{{{{ value_json.get('{container}', {{}}).get('running') }}}}",
                    "attributes_template": attr_templ,
                }
            if self.lnxlink.config["settings"]["docker"]["check_update"] is not None:
                discovery_info[f"Docker Update {container}"] = {
                    "type": "binary_sensor",
                    "icon": "mdi:docker",
                    "value_template": f"{{{{ value_json.get('{container}', {{}}).get('update') }}}}",
                }
        discovery_info["Docker Prune"] = {
            "type": "button",
            "icon": "mdi:docker",
        }
        return discovery_info

    def get_info(self):
        """Gather information from the system"""
        containers = self._get_containers()
        if len(containers) != len(self.containers):
            self.lnxlink.setup_discovery("docker")
        self.containers = containers
        return self.containers

    def _get_containers(self):
        include = self.lnxlink.config["settings"].get("docker", {}).get("include", [])
        exclude = self.lnxlink.config["settings"].get("docker", {}).get("exclude", [])
        containers = {}
        images = []
        for container in self.client.containers.list(all=True):
            if len(include) > 0 and container.name not in include:
                continue
            if container.name in exclude:
                continue
            ports = set()
            for _, host in container.ports.items():
                if host is not None:
                    for host_info in host:
                        ports.add(host_info["HostPort"])
            running = "OFF"
            if container.attrs["State"]["Running"]:
                running = "ON"
            name_id = container.name.lower().replace(" ", "_")
            images.append(container.image)
            containers[name_id] = {
                "running": running,
                "attrs": {
                    "name": container.name,
                    "images": ",".join(container.image.tags),
                    "ports": list(ports),
                    "status": container.status,
                    "update": None,
                },
            }

        cur_time = time.time() / 60 / 60
        check_update = self.lnxlink.config["settings"]["docker"]["check_update"]
        if check_update is not None:
            if cur_time - self.prev_update > check_update:
                self.prev_update = cur_time
                docker_update_status = DockerUpdateStatus()
                self.images_remoteinfo = docker_update_status.get_updates_sync(images)

            for remoteimage_info in self.images_remoteinfo:
                for container in containers.values():
                    if remoteimage_info["tag"] in container["attrs"]["images"]:
                        if remoteimage_info["status"] == "update_available":
                            container["attrs"]["update"] = True
                            container["update"] = "ON"
                        elif remoteimage_info["status"] == "up_to_date":
                            container["attrs"]["update"] = False
                            container["update"] = "OFF"

        return containers

    def start_control(self, topic, data):
        """Control system"""
        name_id = topic[1].replace("docker_", "")
        if name_id in self.containers:
            name = self.containers[name_id]["attrs"]["name"]
            if data == "ON":
                logger.info("Starting container %s", name)
                self.client.containers.get(name).start()
            elif data == "OFF":
                logger.info("Stopping container %s", name)
                self.client.containers.get(name).stop()
        elif name_id == "prune":
            # docker system prune -af
            logger.info("Running prune all")
            self.client.containers.prune()
            self.client.images.prune()
            self.client.networks.prune()
            self.client.volumes.prune()
