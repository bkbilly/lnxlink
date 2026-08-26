"""Tests for the AUR publication file set."""

from pathlib import Path

import yaml

AUR_FILES = {
    "PKGBUILD",
    ".SRCINFO",
    "lnxlink.install",
    "lnxlink.service",
    "config.yaml.example",
}


def test_aur_publish_copies_and_stages_every_package_file():
    """Every maintained AUR input must reach the commit sent to the AUR."""
    workflow_path = Path(".github/workflows/aur-publish.yml")
    workflow = yaml.safe_load(workflow_path.read_text(encoding="UTF-8"))
    steps = workflow["jobs"]["publish"]["steps"]
    publish_script = next(
        step["run"] for step in steps if step["name"] == "Push to AUR"
    )

    for filename in AUR_FILES:
        assert f"cp packaging/aur/{filename} /tmp/aur-repo/{filename}" in publish_script

    git_add = next(
        line.strip()
        for line in publish_script.splitlines()
        if line.strip().startswith("git add ")
    )
    assert set(git_add.split()[2:]) == AUR_FILES


def test_hashed_static_sources_are_in_the_published_file_set():
    """Files hashed into PKGBUILD must be copied and staged with those hashes."""
    workflow_path = Path(".github/workflows/aur-publish.yml")
    workflow = yaml.safe_load(workflow_path.read_text(encoding="UTF-8"))
    steps = workflow["jobs"]["publish"]["steps"]
    hash_script = next(
        step["run"]
        for step in steps
        if step["name"] == "Compute SHA256 for static AUR files"
    )

    hashed_files = {"lnxlink.service", "config.yaml.example"}
    for filename in hashed_files:
        assert f"sha256sum packaging/aur/{filename}" in hash_script
    assert hashed_files < AUR_FILES
