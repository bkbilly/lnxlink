#!/usr/bin/env python3
"""Update AppStream release notes from a GitHub release."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


MAX_ITEMS = 8
MAX_ITEM_LENGTH = 220


def github_release(repo: str, version: str) -> dict:
    """Fetch a GitHub release by tag."""
    tag = version if version.startswith("v") else version
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as err:
        if not version.startswith("v") and err.code == 404:
            return github_release(repo, f"v{version}")
        raise


def cleanup_markdown(text: str) -> str:
    """Convert a markdown fragment to plain text suitable for AppStream."""
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"[*~]", "", text)
    text = re.sub(r"\s+\(#\d+\)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+by @[\w-]+", "", text)
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def release_items(body: str) -> list[str]:
    """Extract concise release-note items from GitHub markdown."""
    items: list[str] = []
    ignored_prefixes = ("full changelog", "what's changed", "whats changed")

    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if line.startswith(("```", "---")):
            continue

        bullet = re.match(r"^[-*]\s+(.*)", line)
        if not bullet:
            continue

        item = cleanup_markdown(bullet.group(1))
        if not item:
            continue
        if item.lower().startswith(ignored_prefixes):
            continue
        if len(item) > MAX_ITEM_LENGTH:
            item = item[: MAX_ITEM_LENGTH - 1].rstrip() + "."
        items.append(item)
        if len(items) >= MAX_ITEMS:
            break

    if items:
        return items

    summary = cleanup_markdown(body)
    if not summary:
        return [f"Update to {os.environ.get('VERSION', 'the latest release')}."]
    return [summary[:MAX_ITEM_LENGTH].rstrip()]


def release_date(release: dict) -> str:
    """Return the AppStream date for a release."""
    published = release.get("published_at") or release.get("created_at")
    if not published:
        return datetime.now(timezone.utc).date().isoformat()
    return datetime.fromisoformat(published.replace("Z", "+00:00")).date().isoformat()


def build_release_element(version: str, release: dict) -> ET.Element:
    """Build an AppStream release element."""
    element = ET.Element(
        "release",
        {
            "version": version,
            "date": release_date(release),
        },
    )
    url = ET.SubElement(element, "url", {"type": "details"})
    url.text = release.get("html_url") or f"https://github.com/bkbilly/lnxlink/releases/tag/{version}"

    description = ET.SubElement(element, "description")
    paragraph = ET.SubElement(description, "p")
    paragraph.text = release.get("name") or version
    bullet_list = ET.SubElement(description, "ul")
    for item in release_items(release.get("body") or ""):
        list_item = ET.SubElement(bullet_list, "li")
        list_item.text = item
    return element


def update_metainfo(path: str, version: str, release: dict) -> bool:
    """Insert or replace the release entry. Return True if the file changed."""
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    tree = ET.parse(path, parser=parser)
    root = tree.getroot()
    releases = root.find("releases")
    if releases is None:
        releases = ET.SubElement(root, "releases")

    new_release = build_release_element(version, release)
    for child in list(releases):
        if child.tag == "release" and child.get("version") == version:
            releases.remove(child)
            break
    releases.insert(0, new_release)

    ET.indent(tree, space="  ")
    before = open(path, "rb").read()
    with open(path, "wb") as metainfo:
        metainfo.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(metainfo, encoding="UTF-8", xml_declaration=False)
        metainfo.write(b"\n")
    after = open(path, "rb").read()
    return before != after


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="io.github.bkbilly.lnxlink.metainfo.xml")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "bkbilly/lnxlink"))
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    os.environ["VERSION"] = args.version
    release = github_release(args.repo, args.version)
    changed = update_metainfo(args.file, args.version, release)
    print(
        f"{'Updated' if changed else 'No changes for'} {args.file} "
        f"with release notes for {args.version}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
