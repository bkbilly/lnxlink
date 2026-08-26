"""Discovery topic registry for Home Assistant integration."""

import copy
import errno
import json
import logging
import os
import threading

logger = logging.getLogger("lnxlink")


class DiscoveryRegistry:
    """Manages Home Assistant discovery topic registration, storage, and cleanup."""

    def __init__(self, config):
        self.config = config
        self.lock = threading.Lock()
        self.registry = {}
        self.file_enabled = True

    def registry_path(self):
        """Path of the locally stored Home Assistant discovery topic registry."""
        registry_path = self.config.get("registry_path")
        if registry_path:
            return registry_path

        config_dir = os.path.dirname(
            os.path.realpath(self.config.get("config_path", ""))
        )
        return os.path.join(config_dir, "discovery_registry.json")

    def load(self):
        """Load Home Assistant discovery topics published by this instance."""
        if not self.file_enabled:
            return copy.deepcopy(self.registry)
        try:
            with open(self.registry_path(), encoding="UTF-8") as registry_file:
                data = json.load(registry_file)
            if isinstance(data, dict):
                self.registry = data
                return copy.deepcopy(data)
        except FileNotFoundError:
            pass
        except Exception as err:
            logger.error("Could not read discovery registry: %s", err)
        return copy.deepcopy(self.registry)

    def save(self, registry):
        """Persist Home Assistant discovery topics published by this instance."""
        self.registry = copy.deepcopy(registry)
        if not self.file_enabled:
            return
        try:
            with open(self.registry_path(), "w", encoding="UTF-8") as file:
                json.dump(registry, file, indent=2, sort_keys=True)
                file.write("\n")
        except OSError as err:
            if err.errno in {errno.EACCES, errno.EPERM, errno.EROFS}:
                self.file_enabled = False
                logger.warning(
                    "Could not write discovery registry to %s because of permission "
                    "issues. Discovery registry will be stored in memory only.",
                    self.registry_path(),
                )
            else:
                logger.error("Could not write discovery registry: %s", err)
        except Exception as err:
            logger.error("Could not write discovery registry: %s", err)

    def registry_entry(self, registry, service):
        """Read a registry entry, including the old list-only format."""
        entry = registry.get(service, {})
        if isinstance(entry, list):
            return set(entry), set()
        if isinstance(entry, dict):
            return set(entry.get("topics", [])), set(entry.get("stale_topics", []))
        return set(), set()

    def _clear_topic(self, topic, mqtt):
        """Clear a retained discovery topic and report transport acceptance."""
        try:
            msg_info = mqtt.publish(topic, payload="", retain=True)
        except Exception as err:
            logger.error(
                "Could not clear Home Assistant discovery topic %s: %s", topic, err
            )
            return False

        if getattr(msg_info, "rc", None) != 0:
            logger.error(
                "Could not clear Home Assistant discovery topic %s: MQTT RC %s",
                topic,
                getattr(msg_info, "rc", None),
            )
            return False
        return True

    def clear_excluded(self, excluded_modules, mqtt):
        """Clear Home Assistant discovery topics for explicitly excluded modules."""
        if not excluded_modules:
            return
        with self.lock:
            registry = self.load()
            updated = False
            for service in sorted(excluded_modules & set(registry)):
                topics, stale_topics = self.registry_entry(registry, service)
                failed_topics = set()
                for topic in sorted(topics | stale_topics):
                    logger.info(
                        "Clearing excluded module Home Assistant discovery topic: %s",
                        topic,
                    )
                    if not self._clear_topic(topic, mqtt):
                        failed_topics.add(topic)

                if failed_topics:
                    remaining_topics = topics & failed_topics
                    remaining_stale_topics = stale_topics & failed_topics
                    updated_entry = {
                        "topics": sorted(remaining_topics),
                        "stale_topics": sorted(remaining_stale_topics),
                    }
                    if registry.get(service) != updated_entry:
                        registry[service] = updated_entry
                        updated = True
                else:
                    registry.pop(service, None)
                    updated = True
            if updated:
                self.save(registry)

    def sync(self, service, current_topics, prune_stale, mqtt):
        """Track discovery topics and clear stale configs for opt-in modules."""
        with self.lock:
            registry = self.load()
            previous_topics, previous_stale_topics = self.registry_entry(
                registry, service
            )
            missing_topics = previous_topics - current_topics
            topics_to_clear = set()
            topics_to_mark_stale = set()
            if prune_stale:
                topics_to_clear = previous_stale_topics & missing_topics
                topics_to_mark_stale = missing_topics - topics_to_clear

            failed_topics = set()

            for topic in sorted(topics_to_clear):
                logger.info("Clearing stale Home Assistant discovery topic: %s", topic)
                if not self._clear_topic(topic, mqtt):
                    failed_topics.add(topic)

            if prune_stale:
                tracked_topics = current_topics | topics_to_mark_stale | failed_topics
                tracked_stale_topics = topics_to_mark_stale | failed_topics
            else:
                tracked_topics = current_topics | previous_topics
                tracked_stale_topics = previous_stale_topics

            registry[service] = {
                "topics": sorted(tracked_topics),
                "stale_topics": sorted(tracked_stale_topics),
            }
            self.save(registry)
