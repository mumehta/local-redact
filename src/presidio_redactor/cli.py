"""
Command-line interface for presidio_redactor.

Exposed as the `redact` console script (see pyproject.toml).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from presidio_redactor.image import redact_image
from presidio_redactor.text import (
    IMAGE_EXTENSIONS,
    SUPPORTED_EXTENSIONS,
    create_analyzer,
    get_output_path,
    redact_text,
)


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
