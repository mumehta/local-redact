from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer import RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_image_redactor import ImageAnalyzerEngine, ImageRedactorEngine

from devops_recognizers import register_devops_recognizers


TEXT_EXTENSIONS = {
    ".txt",
    ".log",
    ".json",
    ".yaml",
    ".yml",
    ".env",
    ".conf",
    ".config",
    ".ini",
    ".xml",
    ".csv",
    ".md",
}

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
}

SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | IMAGE_EXTENSIONS

IDENTIFIER_FALSE_POSITIVE_ENTITIES = {
    "LOCATION",
    "PERSON",
    "ORGANIZATION",
    "NRP",
}


def get_output_path(input_path: Path) -> Path:
    """
    example:
        munish-pii.txt -> munish-pii.redacted.txt
        docker-compose.yml -> docker-compose.redacted.yml
    """
    return input_path.with_name(
        f"{input_path.stem}.redacted{input_path.suffix}"
    )


def is_identifier_like(value: str) -> bool:
    return (
        "_" in value
        and value.upper() == value
        and all(char.isalnum() or char == "_" for char in value)
    )


def filter_analyzer_results(
    text: str,
    results: list[RecognizerResult],
) -> list[RecognizerResult]:
    """
    Preserve config/env key names that NLP recognizers can mistake for PII.

    Example: AWS_SECRET_ACCESS_KEY should remain readable while its assigned
    value is replaced by the custom AWS_SECRET_KEY recognizer.
    """

    filtered_results = []

    for result in results:
        value = text[result.start:result.end]

        if (
            result.entity_type in IDENTIFIER_FALSE_POSITIVE_ENTITIES
            and is_identifier_like(value)
        ):
            continue

        filtered_results.append(result)

    return filtered_results


def create_analyzer() -> AnalyzerEngine:
    analyzer = AnalyzerEngine()
    register_devops_recognizers(analyzer)
    return analyzer


def redact_text(text: str, analyzer: AnalyzerEngine) -> tuple[str, list]:
    results = analyzer.analyze(
        text=text,
        language="en",
    )
    results = filter_analyzer_results(text, results)

    anonymizer = AnonymizerEngine()

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
    )

    return anonymized.text, results

def redact_image(
    input_path: Path,
    output_path: Path,
    analyzer: AnalyzerEngine | None = None,
) -> None:
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


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="redact",
        description="Redact sensitive information using Microsoft Presidio.",
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input file to redact",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file. Defaults to <filename>.redacted.<extension>",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output file if it already exists",
    )

    parser.add_argument(
        "--show-detections",
        action="store_true",
        help="Display detected entity types and confidence scores",
    )

    args = parser.parse_args()

    input_path: Path = args.input

    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}", file=sys.stderr)
        return 1

    if not input_path.is_file():
        print(f"ERROR: Not a file: {input_path}", file=sys.stderr)
        return 1

    if input_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        print(
            f"ERROR: Unsupported file type: {input_path.suffix or '(none)'}",
            file=sys.stderr,
        )
        return 1

    output_path = args.output or get_output_path(input_path)

    if output_path.exists() and not args.force:
        print(
            f"ERROR: Output already exists: {output_path}\n"
            "Use --force to overwrite it.",
            file=sys.stderr,
        )
        return 1

    extension = input_path.suffix.lower()

    if extension in IMAGE_EXTENSIONS:
        try:
            redact_image(input_path, output_path)
        except Exception as exc:
            print(f"ERROR: Image redaction failed: {exc}", file=sys.stderr)
            return 1

        print(f"Redacted: {input_path}")
        print(f"Output:   {output_path}")
        print("Type:     Image")

        return 0


    # Text processing
    try:
        text = input_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(
            "ERROR: File is not UTF-8 text.",
            file=sys.stderr,
        )
        return 1

    analyzer = create_analyzer()

    redacted_text, results = redact_text(text, analyzer)

    output_path.write_text(redacted_text, encoding="utf-8")

    print(f"Redacted: {input_path}")
    print(f"Output:   {output_path}")
    print(f"Entities: {len(results)}")

    if args.show_detections:
        print()
        print("Detections:")

        for result in sorted(results, key=lambda r: r.start):
            print(
                f"  {result.entity_type:<20} "
                f"score={result.score:.2f} "
                f"position={result.start}:{result.end}"
            )

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
