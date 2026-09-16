"""
Image redaction pipeline.

Runs OCR (via Presidio Image Redactor / Tesseract) to locate sensitive text
in an image and replaces those regions with opaque boxes.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytesseract
from PIL import Image
from presidio_analyzer import AnalyzerEngine
from presidio_image_redactor import ImageAnalyzerEngine, ImageRedactorEngine

from presidio_redactor.text import create_analyzer


class TesseractNotFoundError(RuntimeError):
    """Raised when the Tesseract OCR binary cannot be located."""


def _install_hint() -> str:
    if os.name == "nt":
        return "winget install -e --id tesseract-ocr.tesseract"
    if sys.platform == "darwin":
        return "brew install tesseract"
    return "sudo apt install tesseract-ocr   # (Debian/Ubuntu)"


def ensure_tesseract_available() -> None:
    """
    Make sure a Tesseract binary is usable.

    Resolution order:
      1. The TESSERACT_CMD environment variable, if set (explicit override).
      2. A `tesseract` executable discoverable on PATH.

    Raises TesseractNotFoundError with a per-OS install hint if neither is
    available, so image redaction fails with a clear message instead of an
    opaque traceback.
    """

    override = os.environ.get("TESSERACT_CMD")
    if override:
        pytesseract.pytesseract.tesseract_cmd = override
        if not (Path(override).is_file() or shutil.which(override)):
            raise TesseractNotFoundError(
                f"TESSERACT_CMD is set to '{override}' but no executable was "
                f"found there. Install Tesseract OCR: {_install_hint()}"
            )
        return

    if shutil.which("tesseract") is None:
        raise TesseractNotFoundError(
            "Tesseract OCR is required for image redaction but was not found "
            f"on PATH. Install it with: {_install_hint()}\n"
            "Alternatively, set TESSERACT_CMD to the full path of the "
            "tesseract executable."
        )


def redact_image(
    input_path: Path,
    output_path: Path,
    analyzer: AnalyzerEngine | None = None,
) -> None:
    ensure_tesseract_available()

    image = Image.open(input_path)

    if analyzer is None:
        analyzer = create_analyzer()
    image_analyzer = ImageAnalyzerEngine(analyzer_engine=analyzer)
    engine = ImageRedactorEngine(image_analyzer_engine=image_analyzer)

    redacted_image = engine.redact(image)

    # JPEG cannot be saved as RGBA.
    if output_path.suffix.lower() in {".jpg", ".jpeg"}:
        redacted_image = redacted_image.convert("RGB")

    redacted_image.save(output_path)
