from pathlib import Path

from PIL import Image

from presidio_redactor import image as redact
from presidio_redactor.text import get_output_path


def test_redact_image_converts_jpeg_output_to_rgb(tmp_path, monkeypatch):
    input_path = tmp_path / "screenshot.png"
    output_path = tmp_path / "screenshot.redacted.jpg"

    Image.new("RGBA", (20, 20), (255, 0, 0, 128)).save(input_path)

    configured_analyzer = object()
    captured = {}

    class FakeImageAnalyzerEngine:
        def __init__(self, analyzer_engine):
            captured["analyzer"] = analyzer_engine

    class FakeImageRedactorEngine:
        def __init__(self, image_analyzer_engine):
            captured["image_analyzer"] = image_analyzer_engine

        def redact(self, image):
            return image.copy()

    monkeypatch.setattr(redact, "ensure_tesseract_available", lambda: None)
    monkeypatch.setattr(redact, "create_analyzer", lambda: configured_analyzer)
    monkeypatch.setattr(redact, "ImageAnalyzerEngine", FakeImageAnalyzerEngine)
    monkeypatch.setattr(redact, "ImageRedactorEngine", FakeImageRedactorEngine)

    redact.redact_image(input_path, output_path)

    with Image.open(output_path) as saved:
        assert saved.mode == "RGB"
        assert saved.size == (20, 20)

    assert captured["analyzer"] is configured_analyzer
    assert isinstance(captured["image_analyzer"], FakeImageAnalyzerEngine)


def test_create_analyzer_includes_standard_and_devops_recognizers():
    analyzer = redact.create_analyzer()

    standard_results = analyzer.analyze(
        text="Contact jane@example.com",
        language="en",
    )
    devops_results = analyzer.analyze(
        text="api_key=FakeApiKey123456789",
        language="en",
    )

    assert any(result.entity_type == "EMAIL_ADDRESS" for result in standard_results)
    assert any(result.entity_type == "GENERIC_SECRET" for result in devops_results)


def test_image_analyzer_detects_devops_secret_from_ocr_text():
    secret_text = "api_key=FakeApiKey123456789"

    class FakeOCR:
        def perform_ocr(self, image, **kwargs):
            return {
                "text": [secret_text],
                "left": [5],
                "top": [10],
                "width": [240],
                "height": [20],
            }

        def get_text_from_ocr_dict(self, ocr_result):
            return " ".join(ocr_result["text"])

    class FakeImagePreprocessor:
        def preprocess_image(self, image):
            return image, None

    image_analyzer = redact.ImageAnalyzerEngine(
        analyzer_engine=redact.create_analyzer(),
        ocr=FakeOCR(),
        image_preprocessor=FakeImagePreprocessor(),
    )

    results = image_analyzer.analyze(Image.new("RGB", (300, 50), "white"))

    assert any(result.entity_type == "GENERIC_SECRET" for result in results)


def test_get_output_path_inserts_redacted_before_extension():
    assert get_output_path(Path("docker-compose.yml")) == Path(
        "docker-compose.redacted.yml"
    )
