"""Read GitHub releases and stage integrity-checked client downloads."""

from __future__ import annotations

import hashlib
import json
import platform as system_platform
import re
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from . import __version__

RELEASE_API = "https://api.github.com/repos/RoleWeaver/roleweaver/releases/latest"
RELEASES_URL = "https://github.com/RoleWeaver/roleweaver/releases"
MAX_CHECKSUM_BYTES = 2_000_000
MAX_ASSET_BYTES = 1_500_000_000
VERSION_PATTERN = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


class UpdateError(Exception):
    """A release could not be checked or safely staged."""


@dataclass(frozen=True)
class Release:
    version: str
    page_url: str
    notes: str
    assets: dict[str, str]


def _version_tuple(value: str) -> tuple[int, int, int]:
    match = VERSION_PATTERN.fullmatch(value)
    if not match:
        raise UpdateError(f"Unsupported release version: {value!r}")
    return tuple(map(int, match.groups()))


def is_newer(version: str, current: str = __version__) -> bool:
    return _version_tuple(version) > _version_tuple(current)


def asset_name(version: str, platform: str, *, portable: bool = False) -> str:
    if platform == "win32":
        if portable:
            return f"RoleWeaver-Portable-v{version}.zip"
        return f"RoleWeaver-Setup-v{version}.exe"
    if platform == "linux":
        return f"RoleWeaver-v{version}-Linux.tar.gz"
    if platform == "darwin":
        arch = "arm64" if system_platform.machine() == "arm64" else "x86_64"
        return f"RoleWeaver-v{version}-macOS-{arch}.zip"
    raise UpdateError(f"Updates are unavailable for platform {platform!r}.")


def can_download(release: Release, platform: str, *, portable: bool = False) -> bool:
    mac_arch = "arm64" if system_platform.machine() == "arm64" else "x86_64"
    checksum = {
        "linux": "SHA256SUMS-Linux.txt",
        "darwin": f"SHA256SUMS-macOS-{mac_arch}.txt",
    }.get(platform, "SHA256SUMS.txt")
    return (
        asset_name(release.version, platform, portable=portable) in release.assets
        and checksum in release.assets
    )


def _github_url(url: str) -> bool:
    from urllib.parse import urlsplit

    parts = urlsplit(url)
    return parts.scheme == "https" and parts.hostname == "github.com" and not parts.username


def _request(url: str, *, limit: int) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "RoleWeaver-Client-Updater",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        content = response.read(limit + 1)
    if len(content) > limit:
        raise UpdateError("The release response exceeds the expected size.")
    return content


def check_latest() -> Release:
    """Fetch the latest stable release; do not inspect draft/prerelease builds."""
    try:
        payload = json.loads(_request(RELEASE_API, limit=2_000_000))
        version = str(payload["tag_name"]).removeprefix("v")
        _version_tuple(version)
        page_url = str(payload["html_url"])
        if not _github_url(page_url) or payload.get("draft") or payload.get("prerelease"):
            raise UpdateError("The release metadata is not a published stable GitHub release.")
        assets = {
            str(item["name"]): str(item["browser_download_url"]) for item in payload["assets"]
        }
        if any(not _github_url(url) for url in assets.values()):
            raise UpdateError("The release contains an unexpected download URL.")
        return Release(version, page_url, str(payload.get("body") or ""), assets)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise UpdateError(f"Could not check releases: {exc}") from exc


def _expected_hash(checksums: bytes, filename: str) -> str:
    for line in checksums.decode("utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)", line.strip())
        if match and match.group(2) == filename:
            return match.group(1).lower()
    raise UpdateError(f"No SHA-256 checksum was published for {filename}.")


def stage_release(
    release: Release, platform: str, destination: Path, *, portable: bool = False
) -> Path:
    """Download an exact release asset, verify SHA-256, then atomically publish it."""
    filename = asset_name(release.version, platform, portable=portable)
    asset_url = release.assets.get(filename)
    checksum_url = release.assets.get("SHA256SUMS.txt")
    if platform == "linux":
        checksum_url = release.assets.get("SHA256SUMS-Linux.txt")
    elif platform == "darwin":
        arch = "arm64" if system_platform.machine() == "arm64" else "x86_64"
        checksum_url = release.assets.get(f"SHA256SUMS-macOS-{arch}.txt")
    if not asset_url or not checksum_url:
        raise UpdateError("This release lacks the platform download or checksum file.")
    if not _github_url(asset_url) or not _github_url(checksum_url):
        raise UpdateError("The release download URL is not on GitHub.")
    expected = _expected_hash(_request(checksum_url, limit=MAX_CHECKSUM_BYTES), filename)
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / filename
    with tempfile.NamedTemporaryFile(
        dir=destination, prefix=filename + ".", suffix=".part", delete=False
    ) as temporary:
        part = Path(temporary.name)
    digest = hashlib.sha256()
    size = 0
    try:
        request = urllib.request.Request(
            asset_url, headers={"User-Agent": "RoleWeaver-Client-Updater"}
        )
        with urllib.request.urlopen(request, timeout=30) as response, part.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_ASSET_BYTES:
                    raise UpdateError("The download exceeds the expected size.")
                digest.update(chunk)
                output.write(chunk)
        if not size or digest.hexdigest() != expected:
            raise UpdateError("The download did not match its published SHA-256 checksum.")
        part.replace(target)
        return target
    except (OSError, ValueError) as exc:
        raise UpdateError(f"Could not download update: {exc}") from exc
    finally:
        part.unlink(missing_ok=True)
