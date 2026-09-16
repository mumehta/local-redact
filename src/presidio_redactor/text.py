"""
Text redaction pipeline.

Detects PII and DevOps secrets in UTF-8 text using Presidio (plus the custom
DevOps recognizers) and returns an anonymized copy.
"""

from __future__ import annotations

from pathlib import Path

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_anonymizer import AnonymizerEngine

from presidio_redactor.recognizers import register_devops_recognizers


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
