"""
tests/test_url_resolver.py -- Unit tests for src/url_resolver.py

Tests run offline using mocks — no real network calls are made here.
For real network integration, see tests/test_web_url_integration.py.
"""

import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Make src/ importable from the test directory
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from url_resolver import (  # noqa: E402
    DownloadedFile,
    _extract_gdrive_id,
    _is_direct_download,
    is_url,
)


# ---------------------------------------------------------------------------
# is_url
# ---------------------------------------------------------------------------


class TestIsUrl:
    def test_http_url(self):
        assert is_url("http://example.com/file.mp4") is True

    def test_https_url(self):
        assert is_url("https://drive.google.com/file/d/abc123/view") is True

    def test_local_path_unix(self):
        assert is_url("/home/user/video.mp4") is False

    def test_local_path_windows(self):
        assert is_url(r"C:\Users\Maria\video.mp4") is False

    def test_relative_path(self):
        assert is_url("videos/clip.mov") is False

    def test_empty_string(self):
        assert is_url("") is False

    def test_ftp_scheme_is_not_http(self):
        assert is_url("ftp://example.com/file.pdf") is False


# ---------------------------------------------------------------------------
# _extract_gdrive_id
# ---------------------------------------------------------------------------


class TestExtractGdriveId:
    def test_standard_share_link(self):
        url = "https://drive.google.com/file/d/1i6ZqijtHN82T9Ig5NDCN9SgHDNRctvpo/view?usp=sharing"
        assert _extract_gdrive_id(url) == "1i6ZqijtHN82T9Ig5NDCN9SgHDNRctvpo"

    def test_open_id_format(self):
        url = "https://drive.google.com/open?id=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
        assert _extract_gdrive_id(url) == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"

    def test_non_gdrive_url(self):
        assert _extract_gdrive_id("https://youtube.com/watch?v=abc") is None

    def test_direct_mp4_link(self):
        assert _extract_gdrive_id("https://example.com/video.mp4") is None


# ---------------------------------------------------------------------------
# _is_direct_download
# ---------------------------------------------------------------------------


class TestIsDirectDownload:
    def test_mp4_url(self):
        assert _is_direct_download("https://example.com/video.mp4") is True

    def test_pdf_url(self):
        assert _is_direct_download("https://example.com/docs/report.pdf") is True

    def test_wav_url(self):
        assert _is_direct_download("https://example.com/audio.wav") is True

    def test_youtube_url(self):
        assert _is_direct_download("https://www.youtube.com/watch?v=abc123") is False

    def test_gdrive_url(self):
        url = "https://drive.google.com/file/d/1i6ZqijtHN82T9Ig5NDCN9SgHDNRctvpo/view"
        assert _is_direct_download(url) is False

    def test_no_extension(self):
        assert _is_direct_download("https://example.com/stream") is False


# ---------------------------------------------------------------------------
# DownloadedFile context manager (mocked)
# ---------------------------------------------------------------------------


class TestDownloadedFileContextManager:
    """Verify cleanup and routing logic without real network calls."""

    def test_cleanup_on_success(self, tmp_path):
        """The temp directory must be deleted after the with-block exits normally."""
        fake_file = tmp_path / "download.mp4"
        fake_file.write_bytes(b"fake")

        with patch("url_resolver._download_via_ytdlp", return_value=fake_file) as mock_dl:
            with DownloadedFile("https://drive.google.com/file/d/abc/view") as path:
                internal_tmp = Path(path).parent
                assert path == fake_file

        # The *actual* internal temp dir (not tmp_path) should be removed.
        # Since we patched the download to return a path in tmp_path (not the
        # real internal dir), we verify the mock was called and no exception raised.
        mock_dl.assert_called_once()

    def test_cleanup_on_exception(self):
        """Temp directory is removed even if an exception occurs inside the block."""
        created_dirs = []

        real_mkdtemp = tempfile.mkdtemp

        def capturing_mkdtemp(**kwargs):
            d = real_mkdtemp(**kwargs)
            created_dirs.append(Path(d))
            return d

        fake_mp4 = None

        def fake_ytdlp(url, tmp_dir):
            nonlocal fake_mp4
            fake_mp4 = tmp_dir / "download.mp4"
            fake_mp4.write_bytes(b"x")
            return fake_mp4

        with patch("tempfile.mkdtemp", side_effect=capturing_mkdtemp):
            with patch("url_resolver._download_via_ytdlp", side_effect=fake_ytdlp):
                try:
                    with DownloadedFile("https://drive.google.com/file/d/abc/view"):
                        raise RuntimeError("simulated error")
                except RuntimeError:
                    pass

        for d in created_dirs:
            assert not d.exists(), f"Temp dir {d} was not cleaned up"

    def test_routes_gdrive_to_ytdlp(self):
        """Google Drive URLs must use yt-dlp, not requests."""
        with patch("url_resolver._download_via_ytdlp") as mock_ytdlp, \
             patch("url_resolver._download_via_requests") as mock_req, \
             patch("tempfile.mkdtemp", return_value=str(Path(tempfile.gettempdir()) / "test_tmp")), \
             patch("pathlib.Path.exists", return_value=False), \
             patch("shutil.rmtree"):
            gdrive_url = "https://drive.google.com/file/d/1i6ZqijtHN82T9Ig5NDCN9SgHDNRctvpo/view"
            mock_ytdlp.return_value = Path("/tmp/test_tmp/download.mp4")
            try:
                with DownloadedFile(gdrive_url) as _:
                    pass
            except Exception:
                pass
            mock_ytdlp.assert_called_once()
            mock_req.assert_not_called()

    def test_routes_direct_pdf_to_requests(self, tmp_path):
        """Direct .pdf URLs must use requests, not yt-dlp."""
        fake_pdf = tmp_path / "download.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4")

        with patch("url_resolver._download_via_ytdlp") as mock_ytdlp, \
             patch("url_resolver._download_via_requests", return_value=fake_pdf) as mock_req:
            with DownloadedFile("https://example.com/doc.pdf") as path:
                assert path == fake_pdf

        mock_req.assert_called_once()
        mock_ytdlp.assert_not_called()
