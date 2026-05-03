""""""

class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "LWT"
        self.lnxlink = lnxlink

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "LWT": {
                "type": "binary_sensor",
                "entity_category": "diagnostic",
                "use_availability": False,
                "topic_category": None,
            },
        }
