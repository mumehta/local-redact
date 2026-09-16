import pytest

from presidio_redactor import image as image_module
from presidio_redactor.image import (
    TesseractNotFoundError,
    ensure_tesseract_available,
)


def test_env_override_is_applied(tmp_path, monkeypatch):
    fake_tesseract = tmp_path / "tesseract"
    fake_tesseract.write_text("#!/bin/sh\n")
    fake_tesseract.chmod(0o755)

    monkeypatch.setenv("TESSERACT_CMD", str(fake_tesseract))

    ensure_tesseract_available()

    assert (
        image_module.pytesseract.pytesseract.tesseract_cmd
        == str(fake_tesseract)
    )


def test_env_override_missing_binary_raises(monkeypatch, tmp_path):
    missing = tmp_path / "does-not-exist"
    monkeypatch.setenv("TESSERACT_CMD", str(missing))

    with pytest.raises(TesseractNotFoundError):
        ensure_tesseract_available()


def test_missing_tesseract_on_path_raises(monkeypatch):
    monkeypatch.delenv("TESSERACT_CMD", raising=False)
    monkeypatch.setattr(image_module.shutil, "which", lambda _: None)

    with pytest.raises(TesseractNotFoundError) as excinfo:
        ensure_tesseract_available()

    # The error should include an actionable install hint.
    assert "Tesseract" in str(excinfo.value)
