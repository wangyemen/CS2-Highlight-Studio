"""
Auto-updater - check GitHub for new releases
"""
import os
import json
import subprocess
import urllib.request
import urllib.error
from dataclasses import dataclass

CURRENT_VERSION = "1.0.260612"
REPO = "wangyemen/CS2-Highlight-Studio"
VERSION_URL = (
    "https://raw.githubusercontent.com/"
    + REPO + "/main/version.txt")
RELEASE_URL = (
    "https://github.com/" + REPO + "/releases/latest")


@dataclass
class UpdateInfo:
    has_update: bool = False
    current: str = CURRENT_VERSION
    latest: str = ""
    download_url: str = ""
    release_notes: str = ""
    error: str = ""


def check_for_update(proxy=None):
    """Check GitHub for latest version.
    Returns UpdateInfo.
    """
    info = UpdateInfo(
        current=CURRENT_VERSION, latest=CURRENT_VERSION)

    try:
        ctx = None
        if proxy:
            ctx = urllib.request.ProxyHandler(
                {"https": proxy, "http": proxy})
        req = urllib.request.Request(
            VERSION_URL,
            headers={"User-Agent": "CS2HighlightStudio"})
        resp = urllib.request.urlopen(
            req, timeout=10, context=ctx)
        data = resp.read().decode("utf-8").strip()

        # version.txt format:
        # Line 1: version number (e.g. 1.1.0)
        # Line 2: (optional) download URL
        # Line 3+: (optional) release notes
        lines = [l.strip() for l in data.split("\n")
                 if l.strip()]
        if not lines:
            info.error = "\u7248\u672c\u6587\u4ef6\u683c\u5f0f\u9519\u8bef"
            return info

        info.latest = lines[0]
        if len(lines) > 1:
            info.download_url = lines[1]
        if len(lines) > 2:
            info.release_notes = "\n".join(lines[2:])

        info.has_update = (
            _parse_ver(info.latest) > _parse_ver(
                info.current))

    except urllib.error.URLError as e:
        info.error = "\u7f51\u7edc\u8fde\u63a5\u5931\u8d25: " + str(e)
    except Exception as e:
        info.error = "\u68c0\u67e5\u5931\u8d25: " + str(e)

    return info


def download_update(url, dest_dir):
    """Download the installer/update to dest_dir.
    Returns the file path or empty string on failure.
    """
    if not url:
        url = RELEASE_URL
    try:
        fname = "CS2HighlightStudio_setup.exe"
        dest = os.path.join(dest_dir, fname)

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CS2HighlightStudio"})

        # Follow redirect to get actual download URL
        resp = urllib.request.urlopen(req, timeout=30)
        final_url = resp.geturl()

        req2 = urllib.request.Request(
            final_url,
            headers={"User-Agent": "CS2HighlightStudio"})
        resp2 = urllib.request.urlopen(req2, timeout=60)

        total = int(
            resp2.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024 * 256  # 256KB

        with open(dest, "wb") as f:
            while True:
                chunk = resp2.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)

        if os.path.isfile(dest) and downloaded > 0:
            return dest
    except Exception as e:
        print("Download failed:", e)
    return ""


def open_release_page():
    """Open the GitHub releases page in browser."""
    import webbrowser
    webbrowser.open(RELEASE_URL)


def launch_installer(installer_path):
    """Launch the downloaded installer."""
    if not installer_path or not os.path.isfile(
            installer_path):
        return False
    try:
        if os.name == "nt":
            os.startfile(installer_path)
        else:
            subprocess.Popen(
                ["xdg-open", installer_path])
        return True
    except Exception:
        return False


def _parse_ver(v):
    """Parse '1.0.0' to (1, 0, 0) for comparison."""
    try:
        parts = v.strip().split(".")
        return tuple(int(p) for p in parts[:3])
    except Exception:
        return (0, 0, 0)
