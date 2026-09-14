# Presidio Redactor

A local command-line redaction tool built on top of [Microsoft Presidio](https://github.com/microsoft/presidio).

The goal of this project is to provide a simple command such as:

```powershell
redact sensitive-file.txt
```

which detects personally identifiable information (PII) and creates a sanitized copy that is safer to share in public forums, GitHub issues, support tickets, AI tools, documentation, and other external systems.

The project is designed to run locally so that the original sensitive data does not need to be uploaded to a third-party redaction service.

---

## Why This Project Exists

Engineers regularly need to share:

- Application logs
- Terminal output
- Configuration files
- JSON/YAML
- Error messages
- Screenshots
- Debugging information
- Infrastructure configuration
- Support diagnostics

These files can unintentionally contain sensitive information such as:

- Names
- Email addresses
- Phone numbers
- IP addresses
- URLs
- Account identifiers
- Authentication tokens
- API keys
- Cloud credentials
- Private keys
- Connection strings

Manually finding and redacting every sensitive value is slow and error-prone.

This project provides a local automated redaction layer before information is shared externally.

---

# Current Status

The current version supports text-based files using:

- Presidio Analyzer
- Presidio Anonymizer
- spaCy
- `en_core_web_lg`

Image redaction dependencies are also installed and the project is being extended to support screenshots using:

- Presidio Image Redactor
- Tesseract OCR
- pytesseract

DevOps-specific secret detection is planned.

---

# Architecture

## Text Redaction

```text
Input file
    |
    v
Presidio Analyzer
    |
    +-- Pattern recognizers
    |
    +-- spaCy NLP model
    |
    v
Detected entities
    |
    v
Presidio Anonymizer
    |
    v
Redacted output file
```

Example:

```text
munish-pii.txt
        |
        v
Presidio Analyzer
        |
        v
PERSON
EMAIL_ADDRESS
PHONE_NUMBER
        |
        v
Presidio Anonymizer
        |
        v
munish-pii.redacted.txt
```

## Planned Image Redaction

```text
Screenshot
    |
    v
Tesseract OCR
    |
    v
Extracted text + coordinates
    |
    v
Presidio Analyzer
    |
    v
Sensitive entities
    |
    v
Presidio Image Redactor
    |
    v
Opaque redaction boxes
    |
    v
screenshot.redacted.png
```

---

# Requirements

## Operating System

Development is currently being performed on Windows.

The Python portion should also be portable to Linux and macOS, although installation steps may differ.

## Python

Python 3 is required.

Check your installation:

```powershell
python --version
```

## Tesseract OCR

Tesseract is required for image redaction.

Tesseract is a native system dependency and is **not installed by pip**.

On Windows:

```powershell
winget search tesseract
```

Install:

```powershell
winget install -e --id tesseract-ocr.tesseract
```

A typical installation location is:

```text
C:\Program Files\Tesseract-OCR
```

Verify:

```powershell
tesseract --version
```

and:

```powershell
tesseract --list-langs
```

At minimum, the English language model should be available:

```text
eng
```

If Windows cannot find `tesseract`, verify the executable exists:

```powershell
Get-ChildItem "C:\Program Files" `
    -Filter tesseract.exe `
    -Recurse `
    -ErrorAction SilentlyContinue
```

Test it directly:

```powershell
& "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
```

If this works but:

```powershell
tesseract --version
```

does not, add:

```text
C:\Program Files\Tesseract-OCR
```

to your Windows `PATH`.

---

# Installation

## 1. Clone the repository

```powershell
git clone <repository-url>
cd presidio
```

Replace `<repository-url>` with the actual Git repository URL.

---

## 2. Create a virtual environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Your prompt should now show something similar to:

```text
(.venv) PS C:\Users\<username>\tools\presidio>
```

Using a dedicated virtual environment prevents Presidio, spaCy, OpenCV, OCR libraries, and other dependencies from interfering with system-wide Python packages.

---

## 3. Upgrade pip

```powershell
python -m pip install --upgrade pip
```

---

## 4. Install Python dependencies

```powershell
python -m pip install -r requirements.txt
```

The primary dependencies are:

```text
presidio-analyzer==2.2.364
presidio-anonymizer==2.2.364
presidio-image-redactor==0.0.60
```

---

## 5. Install the spaCy English model

```powershell
python -m spacy download en_core_web_lg
```

Verify the spaCy installation:

```powershell
python -m spacy validate
```

A working installation should show `en_core_web_lg` as compatible.

For example:

```text
NAME             SPACY            VERSION
en_core_web_lg   >=3.8.0,<3.9.0   3.8.0   OK
```

---

# Verify Presidio

Test the analyzer:

```powershell
python -c "from presidio_analyzer import AnalyzerEngine; a=AnalyzerEngine(); print(a.analyze(text='My name is John Smith and my email is john@example.com and my phone is +61 412 345 678', language='en'))"
```

Expected detections include:

```text
EMAIL_ADDRESS
PERSON
PHONE_NUMBER
```

Presidio may also return overlapping detections from different recognizers. This is normal.

---

# Verify Tesseract Integration

Ensure Tesseract works directly:

```powershell
tesseract --version
```

Then activate the project's virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Verify that Python can invoke Tesseract:

```powershell
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

If this returns the installed Tesseract version, the Python-to-Tesseract integration is working.

---

# Using the Redactor

## Run directly with Python

While the virtual environment is activated:

```powershell
python .\redact.py .\example.txt
```

The tool creates:

```text
example.redacted.txt
```

The original file is left unchanged.

---

## Display detected entities

Use:

```powershell
python .\redact.py .\example.txt --show-detections
```

Example:

```text
Detections:

PERSON               score=0.85 position=11:21
EMAIL_ADDRESS        score=1.00 position=38:54
PHONE_NUMBER         score=0.75 position=71:86
```

This is useful when testing detection accuracy.

---

## Specify an output file

```powershell
python .\redact.py .\example.txt -o .\safe-to-share.txt
```

---

## Overwrite an existing redacted file

By default, the tool will not overwrite an existing output file.

Use:

```powershell
python .\redact.py .\example.txt --force
```

when intentional overwriting is required.

---

# Global `redact` Command

The project can be exposed as a global Windows command without installing Presidio into the global Python environment.

This allows:

```powershell
redact example.txt
```

from any directory without manually activating `.venv`.

## Create a command directory

```powershell
New-Item -ItemType Directory -Force "$HOME\bin"
```

Create:

```text
%USERPROFILE%\bin\redact.cmd
```

with:

```bat
@echo off
"C:\Users\<username>\tools\presidio\.venv\Scripts\python.exe" "C:\Users\<username>\tools\presidio\redact.py" %*
```

Replace `<username>` and the project path as necessary.

---

## Add the command directory to PATH

Add:

```text
%USERPROFILE%\bin
```

to the user `PATH`.

This can also be done from PowerShell:

```powershell
$bin = "$HOME\bin"

$currentPath = [Environment]::GetEnvironmentVariable(
    "Path",
    "User"
)

if (($currentPath -split ";") -notcontains $bin) {
    [Environment]::SetEnvironmentVariable(
        "Path",
        "$currentPath;$bin",
        "User"
    )
}
```

Open a new PowerShell window and verify:

```powershell
Get-Command redact
```

Then use:

```powershell
redact C:\path\to\sensitive-file.txt
```

The virtual environment does not need to be manually activated because the wrapper invokes its Python interpreter directly.

---

# Supported Text Files

The current implementation supports text-based formats including:

```text
.txt
.log
.json
.yaml
.yml
.env
.conf
.config
.ini
.xml
.csv
.md
```

Files are expected to contain UTF-8 text.

---

# Example

Input:

```text
My name is John Smith.
My email address is john@example.com.
My phone number is +61 412 345 678.
```

Run:

```powershell
redact example.txt
```

Output:

```text
My name is <PERSON>.
My email address is <EMAIL_ADDRESS>.
My phone number is <PHONE_NUMBER>.
```

The resulting file is:

```text
example.redacted.txt
```

---

# Dependency Management

The project uses two dependency files.

## `requirements.txt`

Contains the direct dependencies intentionally selected by the project.

Example:

```text
presidio-analyzer==2.2.364
presidio-anonymizer==2.2.364
presidio-image-redactor==0.0.60
```

This file should remain relatively small and human-maintained.

## `requirements-lock.txt`

Captures the complete known-working Python environment, including transitive dependencies.

Generate it with:

```powershell
python -m pip freeze > requirements-lock.txt
```

Use `requirements.txt` for normal development installations:

```powershell
python -m pip install -r requirements.txt
```

Use `requirements-lock.txt` when an exact environment needs to be reproduced:

```powershell
python -m pip install -r requirements-lock.txt
```

---

# System Dependencies

Some dependencies cannot be represented in `requirements.txt`.

Currently:

```text
Tesseract OCR 5.x
```

Tesseract must be installed separately on the operating system.

The spaCy language model is also installed separately:

```powershell
python -m spacy download en_core_web_lg
```

---

# Security Considerations

## Automated redaction is not a security guarantee

The output of this tool should **not automatically be assumed safe for public disclosure**.

PII and secret detection systems can produce:

- False positives
- False negatives
- Incorrect entity boundaries
- OCR errors
- Unrecognized credential formats

Review highly sensitive output before publishing it.

---

## DevOps Secrets

Standard Presidio recognizers are primarily designed for PII.

Infrastructure and DevOps material may contain secrets that are not detected by default, including:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY

ghp_...
github_pat_...

Authorization: Bearer ...

JWT tokens

client_secret=...

password=...

N8N_ENCRYPTION_KEY=...

privkey:...

nlpriv:...

Kubernetes secrets

database connection strings

SSH/private keys

OAuth credentials

cloud provider credentials
```

Custom recognizers for these patterns are planned.

Until those recognizers are implemented, manually inspect infrastructure-related output before sharing it publicly.

---

# Image Redaction

Image redaction is under development.

The intended interface is:

```powershell
redact screenshot.png
```

producing:

```text
screenshot.redacted.png
```

The pipeline will use:

```text
Image
  |
  v
Tesseract OCR
  |
  v
Presidio
  |
  v
Sensitive text coordinates
  |
  v
Opaque pixel replacement
  |
  v
Redacted image
```

The implementation should use opaque redaction rather than visual blur so that sensitive pixels are actually replaced.

Planned image formats:

```text
.png
.jpg
.jpeg
```

---

# Planned Features

Future development includes:

- PNG/JPG/JPEG redaction
- Automatic text vs image detection
- DevOps-specific secret recognizers
- API key detection
- JWT detection
- OAuth token detection
- AWS/GCP/Azure credential detection
- GitHub/GitLab token detection
- Tailscale key detection
- Private key detection
- Connection-string detection
- Kubernetes secret detection
- Batch directory redaction
- Dry-run mode
- Configurable entity selection
- Confidence thresholds
- Windows Explorer "Redact before sharing" integration
- Automated tests using synthetic sensitive data
- Native Python CLI packaging

---

# Repository Structure

Current structure:

```text
local-presidio/
|
+-- .gitignore
+-- README.md
+-- requirements.txt
+-- requirements-lock.txt
+-- redact.py
|
+-- .venv/                  # ignored by Git
```

As the project grows, it may evolve toward:

```text
presidio-redactor/
|
+-- pyproject.toml
+-- README.md
+-- requirements.txt
|
+-- src/
|   +-- presidio_redactor/
|       +-- __init__.py
|       +-- cli.py
|       +-- text.py
|       +-- image.py
|       +-- recognizers/
|
+-- tests/
|   +-- fixtures/
|
+-- .gitignore
```

---

# Git Safety

Never commit real sensitive data simply to test the redactor.

Avoid committing:

```text
.env
real application logs
credentials
private keys
access tokens
unredacted screenshots
production configuration
customer information
personal information
```

Use synthetic test data instead.

A `.gitignore` should include at minimum:

```gitignore
.venv/
__pycache__/
*.pyc

# Generated redacted files
*.redacted.*

# Environment/secrets
.env
.env.*
*.pem
*.key

# Local sensitive test files
munish-pii.txt
```

Do not rely on `.gitignore` as a security boundary. A file that has already been committed remains in Git history even if it is subsequently added to `.gitignore`.

---

# Development Roadmap

The recommended implementation order is:

```text
1. Text PII redaction                 DONE
        |
2. Global redact command              DONE
        |
3. Tesseract installation             DONE
        |
4. Image redaction
        |
5. DevOps secret recognizers
        |
6. Automated synthetic tests
        |
7. Batch redaction
        |
8. Proper Python CLI packaging
        |
9. Windows Explorer integration
```

---

# Privacy Model

The primary design principle of this project is:

> Sensitive source material should remain local wherever possible.

Unlike an online redaction service, the local pipeline processes source files on the user's machine.

However, users remain responsible for validating that redaction was successful before publishing or transmitting the resulting files.

---

# License

Choose and add an appropriate open-source license before distributing the project publicly.

For a small open-source utility of this type, the MIT License is one possible option.

---

# Acknowledgements

This project builds on:

- Microsoft Presidio
- spaCy
- Tesseract OCR
- pytesseract

These projects provide the underlying PII detection, natural-language processing, and optical character recognition capabilities.