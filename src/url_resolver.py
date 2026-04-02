"""
url_resolver.py -- Resolve and download media/documents from HTTP/HTTPS URLs.

Supports:
  - Google Drive shared file links (drive.google.com/file/d/...)
  - YouTube and yt-dlp-supported platforms (video/audio)
  - Direct HTTP download links (PDF, mp4, etc.)

Usage (as context manager):
    from url_resolver import is_url, DownloadedFile

    if is_url(user_input):
        with DownloadedFile(user_input) as tmp_path:
            process(tmp_path)

The temporary directory is cleaned up automatically when the context exits.
"""

import re
import shutil
import sys
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any, Optional, cast

# Google Drive URL patterns
_GDRIVE_FILE_RE = re.compile(
    r"https?://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)"
)
_GDRIVE_OPEN_RE = re.compile(
    r"https?://drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)"
)

# File extensions that can be fetched with a plain HTTP download
_DIRECT_DOWNLOAD_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v",
    ".mp3", ".wav", ".flac", ".ogg", ".m4a",
    ".pdf",
}


def is_url(value: str) -> bool:
    """Return True if *value* looks like an HTTP/HTTPS URL."""
    try:
        parsed = urllib.parse.urlparse(value)
        return parsed.scheme in ("http", "https")
    except Exception:
        return False


def _extract_gdrive_id(url: str) -> Optional[str]:
    """Return the Google Drive file ID embedded in *url*, or None."""
    for pattern in (_GDRIVE_FILE_RE, _GDRIVE_OPEN_RE):
        m = pattern.search(url)
        if m:
            return m.group(1)
    return None


def _is_direct_download(url: str) -> bool:
    """
    Return True when the URL path ends with a known media/document extension,
    indicating a direct binary download that does not need yt-dlp.
    """
    path = urllib.parse.urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in _DIRECT_DOWNLOAD_EXTENSIONS)


def _download_via_ytdlp(url: str, tmp_dir: Path) -> Path:
    """
    Download *url* using yt-dlp into *tmp_dir* and return the resulting file path.
    Works for Google Drive shared links, YouTube, and other yt-dlp-supported sites.
    """
    try:
        import yt_dlp  # type: ignore
    except ImportError:
        sys.exit(
            "yt-dlp is required to download videos from Google Drive and web platforms.\n"
            "Install it with:  pip install yt-dlp\n"
            "Then retry the command."
        )

    out_template = str(tmp_dir / "download.%(ext)s")

    ydl_opts: dict[str, Any] = {
        "outtmpl": out_template,
        # Prefer best audio+video merge, fall back to single best stream
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": False,
        "no_warnings": False,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
        info = ydl.extract_info(url, download=True)
        ext = info.get("ext", "mp4")

    # yt-dlp writes the file; locate it in the temp directory
    candidates = sorted(tmp_dir.iterdir(), key=lambda p: p.stat().st_size, reverse=True)
    if not candidates:
        sys.exit(
            f"yt-dlp reported success but no file was written to {tmp_dir}.\n"
            "Check the URL and try again."
        )

    # Prefer the expected extension, fall back to the largest file present
    preferred = tmp_dir / f"download.{ext}"
    if preferred.exists():
        return preferred

    return candidates[0]


def _download_via_requests(url: str, tmp_dir: Path) -> Path:
    """
    Fetch *url* with a plain HTTP GET and write the bytes into *tmp_dir*.
    Used for direct-download URLs (e.g. raw .mp4 or .pdf links).
    """
    try:
        import requests  # type: ignore
    except ImportError:
        sys.exit("requests is required for direct URL downloads. Run: pip install requests")

    path_part = urllib.parse.urlparse(url).path
    suffix = Path(path_part).suffix or ".bin"
    dest = tmp_dir / f"download{suffix}"

    print(f"[url_resolver] Fetching: {url}")
    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()

    with dest.open("wb") as fh:
        for chunk in response.iter_content(chunk_size=65536):
            fh.write(chunk)

    return dest


class DownloadedFile:
    """
    Context manager that downloads a URL to a temporary directory and exposes
    the downloaded file as a :class:`~pathlib.Path`.

    Usage::

        with DownloadedFile("https://...") as path:
            process(path)
        # Temp directory is deleted after the ``with`` block.
    """

    def __init__(self, url: str) -> None:
        self.url = url
        self._tmp_dir: Optional[Path] = None
        self.path: Optional[Path] = None

    def __enter__(self) -> Path:
        self._tmp_dir = Path(tempfile.mkdtemp(prefix="analyzer_url_"))

        gdrive_id = _extract_gdrive_id(self.url)
        if gdrive_id or not _is_direct_download(self.url):
            # Use yt-dlp for Google Drive, YouTube and all non-direct URLs
            self.path = _download_via_ytdlp(self.url, self._tmp_dir)
        else:
            self.path = _download_via_requests(self.url, self._tmp_dir)

        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._tmp_dir and self._tmp_dir.exists():
            shutil.rmtree(self._tmp_dir, ignore_errors=True)
        return False  # Do not suppress exceptions
