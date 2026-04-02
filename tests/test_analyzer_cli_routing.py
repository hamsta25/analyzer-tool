import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import analyzer  # noqa: E402


def test_cmd_video_local_path_uses_transcribe(tmp_path):
    video_file = tmp_path / "sample.mp4"
    video_file.write_bytes(b"video")
    output_dir = tmp_path / "out"
    args = SimpleNamespace(input=str(video_file), model="base", output=str(output_dir))

    with patch("url_resolver.is_url", return_value=False), patch(
        "video_transcriber.transcribe"
    ) as mock_transcribe:
        analyzer.cmd_video(args)

    mock_transcribe.assert_called_once_with(video_file, "base", output_dir)


def test_cmd_pdf_local_path_uses_process_path(tmp_path):
    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")
    output_dir = tmp_path / "out"
    args = SimpleNamespace(
        input=str(pdf_file),
        output=str(output_dir),
        ocr_all=False,
        ocr_engine="auto",
        ocr_lang="eng",
        tesseract_psm=6,
    )

    with patch("url_resolver.is_url", return_value=False), patch(
        "pdf_analyzer.process_path"
    ) as mock_process_path:
        analyzer.cmd_pdf(args)

    mock_process_path.assert_called_once_with(
        pdf_file,
        output_dir,
        False,
        ocr_engine="auto",
        ocr_lang="eng",
        tesseract_psm=6,
    )