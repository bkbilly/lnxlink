"""Manage containers; toggle status, check for updates, or prune images"""
import logging
import os
import time

from lnxlink.modules.scripts import helpers
from lnxlink.modules.scripts.docker_update_status import DockerUpdateStatus
from lnxlink.modules.scripts.helpers import import_install_package

logger = logging.getLogger("lnxlink")


# pylint: disable=too-many-branches,too-many-instance-attributes
class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Docker"
        self.lnxlink = lnxlink
        self.lnxlink.add_settings(
            "docker",
            {
                "include": [],
                "exclude": [],
                "check_update": 24,
                "expose_controls": True,
                "base_url": "",
            },
        )
        self.docker = import_install_package("docker", ">=7.0.0")
        if self.docker is None:
            raise SystemError("Docker package not found")

        self.client = self._get_client()
        self.prev_update = 0
        self.images_remoteinfo = []
        self.updating_containers = set()
        self.containers = self._get_containers()

    def _get_client(self):
        """Finds and returns a working Docker client connection."""
        config_base_url = self.lnxlink.config["settings"]["docker"].get("base_url", "")
        if config_base_url:
            try:
                client = self.docker.DockerClient(base_url=config_base_url)
                client.ping()
                return client
            except Exception as err:
                raise SystemError(
                    f"Docker instance not found at configured base_url {config_base_url}: {err}"
                ) from err

        uid = os.getuid()
        targets_to_try = [
            self.docker.from_env,
            lambda: self.docker.DockerClient(base_url="unix://var/run/docker.sock"),
            lambda: self.docker.DockerClient(base_url="unix://run/docker.sock"),
            lambda: self.docker.DockerClient(
                base_url=f"unix://run/user/{uid}/docker.sock"
            ),
        ]

        for target in targets_to_try:
            try:
                client = target()
                client.ping()
                return client
            except Exception:
                pass

        raise SystemError("Docker instance not found")

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
                    "type": "update",
                    "icon": "mdi:docker",
                    "value_template": f"{{{{ value_json.get('{container}', {{}}).get('update_json', {{}}) | tojson }}}}",
                    "install": "UPDATE",
                }
        discovery_info["Docker Prune"] = {
            "type": "button",
            "icon": "mdi:docker",
        }
        return discovery_info

    def get_info(self, force_update=False):
        """Gather information from the system"""
        containers = self._get_containers(force_update=force_update)
        if len(containers) != len(self.containers):
            self.lnxlink.setup_discovery("docker")
        self.containers = containers
        return self.containers

    # pylint: disable=too-many-locals
    def _get_containers(self, force_update=False):
        include = self.lnxlink.config["settings"].get("docker", {}).get("include", [])
        exclude = self.lnxlink.config["settings"].get("docker", {}).get("exclude", [])
        containers = {}
        images = []
        for container in self.client.containers.list(all=True):
            if len(include) > 0 and container.name not in include:
                continue
            if container.name in exclude:
                continue
            name_id = container.name.lower().replace(" ", "_")
            images.append(container.image)
            containers[name_id] = self._container_info(container)

        cur_time = time.time() / 60 / 60
        check_update = self.lnxlink.config["settings"]["docker"]["check_update"]
        if check_update is not None:
            if force_update or cur_time - self.prev_update > check_update:
                self.prev_update = cur_time
                docker_update_status = DockerUpdateStatus()
                self.images_remoteinfo = docker_update_status.get_updates_sync(images)

            for remoteimage_info in self.images_remoteinfo:
                for container_id, container in containers.items():
                    if remoteimage_info["tag"] in container["attrs"]["images"]:
                        local_ver = remoteimage_info.get("local", "installed")
                        remote_ver = remoteimage_info.get("remote", "latest")
                        if local_ver.startswith("sha256:"):
                            local_ver = local_ver[7:19]
                        if remote_ver.startswith("sha256:"):
                            remote_ver = remote_ver[7:19]

                        in_progress = container_id in self.updating_containers
                        if remoteimage_info["status"] == "update_available":
                            container["attrs"]["update"] = True
                            container["update"] = "ON"
                            container["update_json"] = {
                                "installed_version": local_ver,
                                "latest_version": remote_ver,
                                "title": container["attrs"]["name"],
                                "in_progress": in_progress,
                            }
                        elif remoteimage_info["status"] == "up_to_date":
                            container["attrs"]["update"] = False
                            container["update"] = "OFF"
                            container["update_json"] = {
                                "installed_version": local_ver,
                                "latest_version": local_ver,
                                "title": container["attrs"]["name"],
                                "in_progress": in_progress,
                            }

        return containers

    @staticmethod
    def _container_info(container):
        """Return Home Assistant state and attributes for a Docker container."""
        ports = set()
        for _, host in container.ports.items():
            if host is not None:
                for host_info in host:
                    ports.add(host_info["HostPort"])
        running = "ON" if container.attrs["State"]["Running"] else "OFF"
        images_str = (
            ",".join(container.image.tags)
            if container.image.tags
            else container.image.short_id
        )
        return {
            "running": running,
            "update": None,
            "update_json": None,
            "attrs": {
                "name": container.name,
                "images": images_str,
                "ports": list(ports),
                "status": container.status,
            },
        }

    def start_control(self, topic, data):
        """Control system"""
        subcontrol = (
            topic[1] if isinstance(topic, list) and len(topic) > 1 else str(topic)
        )
        client_id_topic = helpers.text_to_topic(self.lnxlink.config["mqtt"]["clientId"])

        if subcontrol.startswith("docker_"):
            subcontrol = subcontrol[7:]
        if subcontrol.startswith(f"{client_id_topic}_"):
            subcontrol = subcontrol[len(client_id_topic) + 1 :]
        if subcontrol.startswith("docker_"):
            subcontrol = subcontrol[7:]

        if subcontrol.startswith("update_"):
            container_id = subcontrol[7:]
            if container_id in self.containers:
                name = self.containers[container_id]["attrs"]["name"]
                logger.info("Updating container %s...", name)
                self.updating_containers.add(container_id)
                if self.containers[container_id].get("update_json") is None:
                    self.containers[container_id]["update_json"] = {}
                self.containers[container_id]["update_json"]["in_progress"] = True
                self.lnxlink.run_module(self.name, self.containers)
                try:
                    self._update_container(name)
                finally:
                    self.updating_containers.discard(container_id)
                    self.lnxlink.run_module(self.name, self.get_info(force_update=True))
            else:
                logger.error(
                    "Container ID %s not found in monitored containers: %s",
                    container_id,
                    list(self.containers.keys()),
                )
        elif subcontrol in self.containers:
            name = self.containers[subcontrol]["attrs"]["name"]
            if data == "ON":
                logger.info("Starting container %s", name)
                self.client.containers.get(name).start()
            elif data == "OFF":
                logger.info("Stopping container %s", name)
                self.client.containers.get(name).stop()
        elif subcontrol == "prune":
            # docker system prune -af
            logger.info("Running prune all")
            self.client.containers.prune()
            self.client.images.prune()
            self.client.networks.prune()
            self.client.volumes.prune()

    def _update_container(self, name):
        """Pull latest image for container and recreate container."""
        try:
            container = self.client.containers.get(name)
            image_name = None
            if container.image.tags:
                image_name = container.image.tags[0]
            elif (
                "RepoDigests" in container.image.attrs
                and container.image.attrs["RepoDigests"]
            ):
                image_name = container.image.attrs["RepoDigests"][0].split("@")[0]
            elif "Config" in container.attrs and "Image" in container.attrs["Config"]:
                image_name = container.attrs["Config"]["Image"]

            if not image_name:
                logger.error("Could not determine image name for container %s", name)
                return False

            logger.info(
                "Pulling latest image '%s' for container '%s'...", image_name, name
            )
            self.client.images.pull(image_name)

            self._recreate_container(container)
            logger.info("Container %s successfully updated.", name)
            return True
        except Exception as err:
            logger.error("Failed to update container %s: %s", name, err)
            return False

    def _recreate_container(self, container):
        """Recreate container using updated image."""
        container.reload()
        container_info = self.client.api.inspect_container(container.id)
        config = container_info["Config"]
        host_config = container_info["HostConfig"]
        name = container_info["Name"].lstrip("/")
        was_running = container_info["State"]["Running"]

        if was_running:
            logger.info("Stopping container %s...", name)
            container.stop()

        logger.info("Removing old container %s...", name)
        container.remove()

        logger.info("Creating new container %s...", name)
        new_container_dict = self.client.api.create_container(
            name=name,
            image=config.get("Image"),
            command=config.get("Cmd"),
            hostname=config.get("Hostname"),
            user=config.get("User"),
            detach=True,
            stdin_open=config.get("OpenStdin", False),
            tty=config.get("Tty", False),
            ports=config.get("ExposedPorts"),
            environment=config.get("Env"),
            volumes=config.get("Volumes"),
            network_disabled=config.get("NetworkDisabled", False),
            entrypoint=config.get("Entrypoint"),
            working_dir=config.get("WorkingDir"),
            domainname=config.get("Domainname"),
            host_config=host_config,
            mac_address=config.get("MacAddress"),
            labels=config.get("Labels"),
            stop_signal=config.get("StopSignal"),
            stop_timeout=config.get("StopTimeout"),
        )
        new_container = self.client.containers.get(new_container_dict["Id"])
        if was_running:
            logger.info("Starting new container %s...", name)
            new_container.start()
