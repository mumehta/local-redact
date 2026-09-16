# Security Model And Trust Boundaries

Local Redact is a local command-line redaction tool for developers who need to
remove PII, credentials, tokens, and other sensitive values from logs, config
files, text files, and screenshots before sharing them with external systems.

This document is intended for security-conscious users, platform teams, and
tool approvers who need to understand what the tool does, what it does not do,
and what risk remains after using it.

## Summary

Local Redact is designed as a local first-pass redaction tool.

- It runs on the user's machine.
- It does not send file contents to a hosted redaction service.
- It does not collect telemetry or analytics.
- It writes a separate redacted output file and leaves the original unchanged.
- It uses deterministic code paths and open-source libraries, not a remote LLM,
  to perform redaction.
- It is a developer helper tool, not a guarantee that output is safe to publish.

The tool is intended to get a developer most of the way toward safer sharing by
redacting commonly detected PII, secrets, credentials, and similar sensitive
values before content is passed to a downstream system. It does not remove the
need for human review. The person using the tool remains responsible for
checking the redacted output and satisfying themselves that it is safe for their
intended use case.

## Intended Use

Use Local Redact before sharing sensitive developer material such as:

- application logs
- terminal output
- stack traces
- JSON, YAML, `.env`, INI, XML, CSV, and Markdown files
- configuration snippets
- screenshots containing logs or credentials
- support diagnostics
- debugging context intended for an LLM or external support system

The tool is intended for developers, DevOps engineers, SREs, support engineers,
and internal teams who need a repeatable local workflow for reducing accidental
data exposure.

## Not Intended As

Local Redact is not:

- a data loss prevention platform
- a compliance certification mechanism
- a substitute for security review
- a guarantee that output is safe for public disclosure
- a one-size-fits-all redaction system
- a parser-aware sanitizer for every structured file format
- a secret scanner for source control history
- an access-control boundary

Users remain responsible for reviewing redacted output before sharing it.

## Runtime Data Flow

At runtime, the data flow is local:

```text
input file on local machine
        |
        v
local detection pipeline
        |
        v
local redaction pipeline
        |
        v
new redacted output file on local machine
```

The original input file is not modified. By default, output is written beside
the input using the `.redacted` filename convention, for example:

```text
application.log -> application.redacted.log
screenshot.png  -> screenshot.redacted.png
```

## Network Behavior

Local Redact does not intentionally transmit file contents, detected entities,
redacted output, telemetry, analytics, or usage data over the network at
runtime.

Network access may occur during setup:

- `pip install` or `pipx install` downloads Python packages.
- `python -m spacy download en_core_web_lg` downloads the spaCy language model.

After installation, the redaction process is designed to operate locally. For
controlled or air-gapped environments, dependencies and models should be
mirrored, pinned, reviewed, and installed from approved internal sources.

## Underlying Components

Local Redact builds on open-source components:

- Microsoft Presidio Analyzer for entity detection
- Microsoft Presidio Anonymizer for text replacement
- Presidio Image Redactor for image redaction
- spaCy for NLP-based PII detection
- Tesseract OCR and pytesseract for text extraction from images
- Pillow for image handling

Custom recognizers add DevOps-specific detection for credential and secret
patterns that are commonly missed by general PII tools.

Examples include:

- AWS access keys and secret keys
- GitHub tokens
- JWTs
- bearer tokens
- private keys
- password assignments
- client secrets
- generic API keys and access tokens
- database connection strings
- Tailscale keys
- n8n encryption keys

## Redaction Behavior

For text files, detected sensitive spans are replaced with entity labels such as:

```text
<EMAIL_ADDRESS>
<PERSON>
<PASSWORD>
<GITHUB_TOKEN>
<CONNECTION_STRING>
```

For assignment-style secrets, the tool attempts to preserve useful structure by
redacting only the value:

```text
password=Secret123
```

becomes:

```text
password=<PASSWORD>
```

For images, the tool uses OCR to detect text, analyzes the extracted text, and
overwrites detected regions with opaque boxes. Opaque replacement is used instead
of blur because blurred content may sometimes remain partially recoverable.

## Security Boundaries

The primary security boundary is locality.

The tool is designed to keep source material on the user's machine during
runtime. It should be reviewed and deployed like any other local developer tool
that processes sensitive files.

The primary responsibility boundary is human review. Local Redact can assist by
removing many commonly recognized sensitive values, but the final decision to
share content with an LLM, support portal, public issue tracker, vendor, or any
other downstream system belongs to the user or organization operating the tool.

Security-sensitive environments should consider:

- installing from pinned or internally mirrored packages
- reviewing dependency licenses and supply-chain posture
- running in a dedicated virtual environment or via `pipx`
- controlling which users may install and execute the tool
- testing the tool against internal sample data before approval
- documenting that redacted output still requires human review

## Known Risks And Limitations

Automated redaction is best effort. Important risks remain:

- False negatives: sensitive data may be missed.
- False positives: non-sensitive text may be redacted.
- Incorrect boundaries: only part of a secret may be redacted, or too much
  surrounding context may be removed.
- OCR limitations: screenshots with small fonts, poor contrast, unusual layouts,
  or cropped text may not be read correctly.
- Unknown secret formats: custom or uncommon token formats may not be detected.
- Context leakage: surrounding text can still reveal sensitive operational
  details even when values are redacted.
- Structured file behavior: JSON, YAML, XML, `.env`, and similar files are
  currently processed as text rather than parsed and reserialized.
- Git history: the tool does not remove secrets already committed to source
  control history.

Because of these limitations, redacted output should be reviewed before it is
sent to an LLM, support system, public issue, documentation site, or third
party.

Local Redact should be treated as a risk-reduction tool rather than a complete
security control. In practical terms, it may get common cases most of the way
there, but it cannot know every organization's data classification rules, every
internal identifier format, every custom token format, or every downstream
sharing policy.

## Extensibility And Customization

Local Redact is open source and intentionally open to review, extension, and
customization.

Organizations and individual users may need different recognizers, stricter
rules, additional file handling, different output conventions, or internal
approval workflows. Those requirements may not belong in the default package for
all users.

Contributions are welcome through pull requests. Proposed changes will be
reviewed before they are accepted into the main package. If a change is highly
specific to one environment, users are free to fork the project and customize it
for their own requirements.

## Recommended Approval Position

For controlled environments, Local Redact is best evaluated as a local
developer-assistance tool that reduces accidental exposure before sharing.

It should be approved only with the understanding that:

- it reduces risk but does not eliminate it
- it does not replace human review
- it is not a formal DLP control
- it is not one size fits all
- it should be installed from approved package sources
- it should be tested against the organization's common log and secret formats
- it should be accompanied by guidance on what may and may not be shared

## Responsible Use Guidance

Recommended workflow:

1. Run Local Redact on the file or screenshot.
2. Review the redacted output manually.
3. Remove any remaining sensitive context.
4. Share only the redacted output, not the original.
5. Treat highly sensitive production data as restricted even after redaction.

Never commit real secrets, customer data, or production logs simply to test the
tool. Use synthetic test data instead.

## Reporting Security Issues

If you find a case where Local Redact fails to redact a common sensitive value,
or if you identify a security issue in the tool itself, please open a GitHub
issue with a synthetic reproduction. Do not include real secrets, customer data,
or private production logs in bug reports.
