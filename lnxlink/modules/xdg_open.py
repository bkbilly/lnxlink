import subprocess
import logging

logger = logging.getLogger('lnxlink')


class Addon():

    def __init__(self, lnxlink):
        self.name = 'xdg_open'

    def startControl(self, topic, data):
        logger.info(f"/usr/bin/xdg-open {data}")
        subprocess.call(f"/usr/bin/xdg-open {data}", shell=True)
