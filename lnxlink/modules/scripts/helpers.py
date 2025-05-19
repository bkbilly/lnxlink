"""A collection of helper functions"""
import sys
import importlib.metadata
import logging
import subprocess

logger = logging.getLogger("lnxlink")


# pylint: disable=consider-using-with
def syscommand(command, ignore_errors=False, timeout=3, background=False):
    """Global subprocess command"""
    logger.debug("Executing command: %s", command)
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


def import_install_package(package, req_version="", syspackage=None):
    """Imports a system package and if it doesn't exist, it gets installed"""
    if syspackage is None:
        syspackage = package

    try:
        current_version = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        current_version = None

    if current_version is None or needs_update(current_version, req_version):
        package_version = f"'{package}{req_version}'"
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
            try:
                if isinstance(syspackage, tuple):
                    return __import__(syspackage[0], fromlist=syspackage[1])
                return __import__(syspackage)
            except ModuleNotFoundError:
                logger.error("Can't install package %s", package)
                return None

    try:
        if isinstance(syspackage, tuple):
            return __import__(syspackage[0], fromlist=syspackage[1])
        return __import__(syspackage)
    except Exception as err:
        logger.error("Can't import package %s: %s", package, err)
        return None


def needs_update(current_version, request_version):
    """Compares two version strings"""
    current_version = str(current_version).strip("><=~")
    request_version = str(request_version).strip("><=~")
    try:
        current_versions = [int(version) for version in current_version.split(".")]
    except (TypeError, ValueError):
        current_versions = [0]
    if request_version is None or request_version == "":
        return False
    request_versions = [int(version) for version in request_version.split(".")]
    for num in range(max(len(current_versions), len(request_versions))):
        cur_version = current_versions[num] if num < len(current_versions) else 0
        req_version = request_versions[num] if num < len(request_versions) else 0
        if req_version > cur_version:
            return True
        if req_version < cur_version:
            return False
    return False


def text_to_topic(text):
    """Used for setting a text to be sent to mqtt topic"""
    text = text.lower()
    text = text.replace(" ", "_")
    text = text.replace("+", "")
    text = text.replace("*", "")
    text = text.replace("(", "")
    text = text.replace(")", "")
    text = text.replace("@", "")
    return text
