---
title: "Redact Sensitive Data Locally Before Sharing It with AI"
date: 2026-09-15
draft: false
description: "How I use a local Presidio-based redaction command to remove PII and DevOps secrets from files and screenshots before sharing them with AI agents."
tags:
  - ai
  - privacy
  - security
  - python
  - windows
categories:
  - Tools
---

AI agents are becoming part of everyday engineering work. We paste logs into them, share screenshots, ask them to inspect config files, debug stack traces, review YAML, explain JSON payloads, and help us understand messy production behavior.

That workflow is powerful, but it has a sharp edge: the best debugging context often contains information that should not leave the machine unchanged.

Logs may contain email addresses, phone numbers, names, session IDs, bearer tokens, database connection strings, cloud keys, or internal URLs. Screenshots may show the same information visually. Even when the target system is trusted, I do not want to casually send raw PII or secrets into an AI prompt when a redacted version would work just as well.

So I built and configured a small local redaction tool called `local-redactor`. It gives me a simple command:

```powershell
redact <input-file>
```

The goal is simple: before I give a file or screenshot to an AI agent, I run it through a local redaction step and share the safer copy.

## Why Local Redaction Helps

The practical problem is not that I want to publish data publicly. Most of the time I just want help.

For example:

```text
Can you check this application log and tell me why the job is failing?
```

Or:

```text
Here is a screenshot of my local n8n config. What am I missing?
```

Those are normal AI-assisted development questions. But the input might contain values that do not belong in a chat window:

- Personal information such as names, emails, and phone numbers
- Password-style assignments such as `password=...`
- API tokens and bearer tokens
- AWS-shaped access keys and secret keys
- GitHub tokens
- JWTs
- Private key blocks
- n8n encryption keys
- Database connection strings

Manual cleanup is slow, easy to forget, and easy to do badly. A local command gives me a repeatable first pass. The original file stays on my machine, the redacted copy is generated beside it, and I can inspect the result before sharing.

This is not a replacement for security judgment. It is a guardrail for everyday work.

## What The Tool Does

`local-redactor` is a Python command-line tool built on Microsoft Presidio. It currently supports both text files and screenshots.

For text, it uses Presidio's standard PII detection plus custom DevOps recognizers for infrastructure-style secrets. That matters because standard PII detectors are good at things like names and email addresses, but engineering files often contain tokens, keys, and connection strings.

For images, it uses Tesseract OCR to read visible text from screenshots, then passes the detected text through the same analyzer pipeline. Sensitive regions are covered with opaque redaction boxes so the pixels are replaced, not just blurred.

Supported text-style inputs include:

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

Supported image inputs include:

```text
.png
.jpg
.jpeg
```

## Installation On Windows

I keep the project in its own Python virtual environment so Presidio, spaCy, OCR libraries, and related dependencies do not interfere with the rest of my system.

Clone the project:

```powershell
cd $HOME\tools
git clone https://github.com/mumehta/local-redact.git local-redactor
cd local-redactor
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Upgrade pip and install the Python dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Install the spaCy English model used by Presidio:

```powershell
python -m spacy download en_core_web_lg
python -m spacy validate
```

For screenshot redaction, Tesseract OCR must also be installed as a native Windows dependency. It is not installed by pip.

One option is:

```powershell
winget install -e --id tesseract-ocr.tesseract
```

Then verify it:

```powershell
tesseract --version
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

At this point the tool can be run from the project directory:

```powershell
python .\redact.py .\application.log
```

## Making `redact` Available Everywhere

I did not want to activate the virtual environment every time I needed to sanitize a file. The smoother workflow is to make `redact` available from any PowerShell, Command Prompt, Windows Terminal, or IDE terminal.

Create a user `bin` directory:

```powershell
New-Item -ItemType Directory -Force "$HOME\bin"
```

Create this wrapper file:

```text
C:\Users\<username>\bin\redact.cmd
```

Use this content, adjusting the paths for your username and install location:

```bat
@echo off
"C:\Users\<username>\tools\local-redactor\.venv\Scripts\python.exe" "C:\Users\<username>\tools\local-redactor\redact.py" %*
```

The wrapper deliberately calls Python from the project's `.venv`, so the virtual environment remains isolated but does not need to be activated manually.

Add the user `bin` directory to your Windows user PATH:

```powershell
$bin = "$HOME\bin"
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

if (($currentPath -split ";") -notcontains $bin) {
    [Environment]::SetEnvironmentVariable(
        "Path",
        "$currentPath;$bin",
        "User"
    )
}
```

Close and reopen the terminal, then verify:

```powershell
Get-Command redact
redact --help
```

Now the command works from anywhere:

```powershell
redact application.log
redact config.yaml
redact .env
redact screenshot.png
```

## Daily Workflow

The workflow is intentionally boring:

```powershell
redact application.log
```

That creates:

```text
application.redacted.log
```

The original file is left unchanged.

For screenshots:

```powershell
redact Screenshot.png
```

That creates:

```text
Screenshot.redacted.png
```

If I want to choose the output path:

```powershell
redact application.log -o sanitized.log
```

If I want to see what the text analyzer detected:

```powershell
redact application.log --show-detections
```

If I intentionally want to overwrite an existing generated file:

```powershell
redact application.log --force
```

## Text Example

Here is a small dummy input file:

```text
Name: Alex Rivera
Email: alex.rivera@example.com
Phone: +1 202-555-0147
password=ExamplePassword123!
```

After running:

```powershell
redact user-pii.txt
```

The redacted version becomes:

```text
Name: <PERSON>
Email: <EMAIL_ADDRESS>
Phone: <PHONE_NUMBER>
password=<PASSWORD>
```

The values above are synthetic examples. They are deliberately shaped like real data so the redaction pipeline has something meaningful to detect.

## Screenshot Example

The same idea works for screenshots. If a screenshot contains visible text such as an email address, a password assignment, a token, or a phone number, the image pipeline uses OCR to find the text and then covers sensitive regions.

```powershell
redact devops-secrets.png
```

Output:

```text
devops-secrets.redacted.png
```

Here is the kind of before and after comparison I want in the post. These example screenshots should use dummy values only.

![Screenshot before redaction](/images/local-redactor/devops-secrets-before.png)

![Screenshot after redaction](/images/local-redactor/devops-secrets-after.png)

The important detail is that image redaction is not just cosmetic blur. The tool writes opaque boxes over the detected regions, so the sensitive pixels are replaced in the generated output image.

## What I Use It For

This tool is useful whenever I need to share local context with an AI assistant, a teammate, a GitHub issue, or documentation, but I do not want raw sensitive values to travel with it.

Common use cases:

- Sanitizing application logs before pasting them into an AI chat
- Redacting `.env`, `.ini`, `.yaml`, or `.json` examples before asking for help
- Cleaning screenshots before sharing UI or configuration problems
- Preparing safer examples for documentation and blog posts
- Checking whether obvious DevOps secrets are present in a sample file

It is especially useful in AI workflows because the redacted file usually preserves enough structure for debugging. The assistant does not need the real email address, real password, real AWS-looking key, or real bearer token to reason about the problem.

## Limitations

Automated redaction is not a security guarantee.

Detection tools can miss things. They can also redact too much or choose imperfect boundaries. OCR can misread screenshots. A token format that is obvious to a human may not match a recognizer yet. A screenshot with tiny text, unusual fonts, low contrast, or overlapping UI can reduce accuracy.

There is also an important structured-data limitation in the current version: JSON, YAML, XML, `.env`, and similar files are processed as text. That means the redactor may replace sensitive values successfully, but it does not yet guarantee the output remains valid JSON, YAML, or XML in every case.

For example, the future version should ideally parse JSON as JSON, redact values while preserving syntax, then serialize it back as valid JSON. The same idea can apply to YAML, XML, `.env`, `.properties`, TOML, and other structured formats. Today, I treat structured-file output as something to review before reusing as machine-readable input.

The current version also processes one file at a time. Batch directory redaction and deeper format-aware parsing are good next steps.

## My Rule Of Thumb

I use `redact` as a local privacy checkpoint before sending context outward.

The flow is:

```text
raw local file
        |
        v
redact <file>
        |
        v
redacted output
        |
        v
manual review
        |
        v
share with AI agent or teammate
```

That small habit reduces accidental exposure without slowing the work down much. It keeps the useful part of AI-assisted debugging while removing a lot of the data that the AI agent never needed in the first place.
