"""A collection of helper functions"""
import sys
import logging
import subprocess

logger = logging.getLogger("lnxlink")


def syscommand(command, ignore_errors=False, timeout=3, background=False):
    """Global subprocess command"""
    if isinstance(command, list):
        command = " ".join(command)
    if background:
        subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return "", "", 0
    result = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )
    stderr = result.stderr.decode("UTF-8").strip()
    stdout = result.stdout.decode("UTF-8").strip()
    returncode = result.returncode
    if returncode != 0 and ignore_errors is False:
        logger.error("Error with command: %s (%s)", command, stderr)
    return stdout, stderr, returncode


def import_install_package(package, version="", syspackage=None, forceupgrade=False):
    """Imports a system package and if it doesn't exist, it gets installed"""
    if syspackage is None:
        syspackage = package
    try:
        if forceupgrade:
            raise ImportError
        return __import__(syspackage)
    except (ImportError, ModuleNotFoundError):
        package_version = f"'{package}{version}'"
        logger.info("Installing %s...", package_version)
        args = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--break-system-packages",
            "-U",
            "--quiet",
            package_version,
        ]
        _, _, returncode = syscommand(args, ignore_errors=True, timeout=None)
        if returncode != 0:
            logger.error("Can't install package %s", package)
            return None
    return __import__(syspackage)
