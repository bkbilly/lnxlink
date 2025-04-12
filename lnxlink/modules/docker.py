"""Controls Docker instance"""
import logging
from lnxlink.modules.scripts.helpers import import_install_package

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Docker"
        self.lnxlink = lnxlink
        self._requirements()
        try:
            # client = docker.from_env()
            self.client = self.docker.DockerClient(base_url="unix://run/docker.sock")
        except Exception as err:
            raise SystemError(f"Docker instance not found: {err}") from err
        self.containers = self._get_containers()

    def _requirements(self):
        self.docker = import_install_package("docker", ">=7.0.0")

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        for container in self.containers:
            discovery_info[f"Docker {container}"] = {
                "type": "switch",
                "icon": "mdi:docker",
                "value_template": f"{{{{ value_json.get('{container}', {{}}).get('running') }}}}",
                "attributes_template": f"{{{{ value_json.get('{container}', {{}}) | tojson }}}}",
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
            containers[name_id] = {
                "name": container.name,
                "image": ",".join(container.image.tags),
                "ports": list(ports),
                "running": running,
                "status": container.status,
            }
        return containers

    def start_control(self, topic, data):
        """Control system"""
        name_id = topic[1].replace("docker_", "")
        if name_id in self.containers:
            name = self.containers[name_id]["name"]
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
