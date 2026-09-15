"""
Custom Microsoft Presidio recognizers for DevOps secrets.

The recognizers in this module are intended to detect common credentials
and secrets found in:

- configuration files
- environment files
- logs
- terminal output
- CI/CD output
- screenshots after OCR

Where possible, assignment-based recognizers return ONLY the secret value
as the sensitive span.

Example:

    password=Secret123
             ^^^^^^^^^

This allows the anonymizer to preserve useful structure:

    password=<REDACTED>
"""

from __future__ import annotations

import re

from presidio_analyzer import (
    EntityRecognizer,
    Pattern,
    PatternRecognizer,
    RecognizerResult,
)


# ---------------------------------------------------------------------------
# Helper for ordinary regex-based recognizers
# ---------------------------------------------------------------------------

def _recognizer(
    name: str,
    entity: str,
    patterns: list[tuple[str, str, float]],
) -> PatternRecognizer:
    """
    Create a standard Presidio PatternRecognizer.
    """

    return PatternRecognizer(
        name=name,
        supported_entity=entity,
        patterns=[
            Pattern(
                name=pattern_name,
                regex=regex,
                score=score,
            )
            for pattern_name, regex, score in patterns
        ],
    )


# ---------------------------------------------------------------------------
# Assignment recognizer
# ---------------------------------------------------------------------------

class AssignmentValueRecognizer(EntityRecognizer):
    """
    Detect key=value or key:value assignments while returning only
    the VALUE as the sensitive span.

    Examples:

        password=Secret123
        client_secret: abc123
        N8N_ENCRYPTION_KEY="abcdef"

    become:

        password=<REDACTED>
        client_secret: <REDACTED>
        N8N_ENCRYPTION_KEY="<REDACTED>"
    """

    def __init__(
        self,
        name: str,
        supported_entity: str,
        keys: list[str],
        score: float = 0.95,
        min_length: int = 4,
    ):
        super().__init__(
            name=name,
            supported_entities=[supported_entity],
        )

        escaped_keys = "|".join(
            re.escape(key)
            for key in sorted(keys, key=len, reverse=True)
        )

        self.assignment_regex = re.compile(
            rf"""
            \b(?:{escaped_keys})\b
            \s*[:=]\s*
            (?P<quote>["']?)
            (?P<value>[^\s"'#,;]{{{min_length},}})
            (?P=quote)
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        self.score = score

    def analyze(
        self,
        text: str,
        entities: list[str],
        nlp_artifacts=None,
    ) -> list[RecognizerResult]:

        if self.supported_entities[0] not in entities:
            return []

        results = []

        for match in self.assignment_regex.finditer(text):
            results.append(
                RecognizerResult(
                    entity_type=self.supported_entity,
                    start=match.start("value"),
                    end=match.end("value"),
                    score=self.score,
                )
            )

        return results

    @property
    def supported_entity(self) -> str:
        return self.supported_entities[0]

    def load(self) -> None:
        return None


# ---------------------------------------------------------------------------
# Bearer token recognizer
# ---------------------------------------------------------------------------

class BearerValueRecognizer(EntityRecognizer):
    """
    Detect only the credential portion of a Bearer token.

    Example:

        Authorization: Bearer abcdef123456

    becomes:

        Authorization: Bearer <REDACTED>
    """

    def __init__(self):
        super().__init__(
            name="Bearer Token Recognizer",
            supported_entities=["BEARER_TOKEN"],
        )

        self.bearer_regex = re.compile(
            r"\bbearer\s+(?P<value>[A-Za-z0-9._~+/=-]{8,})",
            re.IGNORECASE,
        )

    def analyze(
        self,
        text: str,
        entities: list[str],
        nlp_artifacts=None,
    ) -> list[RecognizerResult]:

        if self.supported_entities[0] not in entities:
            return []

        results = []

        for match in self.bearer_regex.finditer(text):
            results.append(
                RecognizerResult(
                    entity_type=self.supported_entity,
                    start=match.start("value"),
                    end=match.end("value"),
                    score=0.99,
                )
            )

        return results

    @property
    def supported_entity(self) -> str:
        return self.supported_entities[0]

    def load(self) -> None:
        return None


# ---------------------------------------------------------------------------
# Public recognizer collection
# ---------------------------------------------------------------------------

def get_devops_recognizers():
    """
    Return all custom DevOps/security recognizers.
    """

    recognizers = []

    # -----------------------------------------------------------------------
    # AWS Access Key ID
    #
    # Common AWS access key prefixes:
    # AKIA - long-term access key
    # ASIA - temporary STS credential
    # -----------------------------------------------------------------------

    recognizers.append(
        _recognizer(
            name="AWS Access Key Recognizer",
            entity="AWS_ACCESS_KEY",
            patterns=[
                (
                    "AWS access key ID",
                    r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
                    0.99,
                ),
            ],
        )
    )

    # -----------------------------------------------------------------------
    # AWS Secret Access Key
    #
    # We intentionally require an assignment name because arbitrary
    # 40-character strings would create too many false positives.
    # -----------------------------------------------------------------------

    recognizers.append(
        AssignmentValueRecognizer(
            name="AWS Secret Key Recognizer",
            supported_entity="AWS_SECRET_KEY",
            keys=[
                "AWS_SECRET_ACCESS_KEY",
                "AWS_SECRET_KEY",
            ],
            score=0.99,
            min_length=20,
        )
    )

    # -----------------------------------------------------------------------
    # GitHub tokens
    # -----------------------------------------------------------------------

    recognizers.append(
        _recognizer(
            name="GitHub Token Recognizer",
            entity="GITHUB_TOKEN",
            patterns=[
                (
                    "GitHub classic personal access token",
                    r"\bghp_[A-Za-z0-9]{36}\b",
                    0.99,
                ),
                (
                    "GitHub fine-grained personal access token",
                    r"\bgithub_pat_[A-Za-z0-9_]{20,255}\b",
                    0.99,
                ),
                (
                    "GitHub OAuth token",
                    r"\bgho_[A-Za-z0-9]{36}\b",
                    0.99,
                ),
                (
                    "GitHub user token",
                    r"\bghu_[A-Za-z0-9]{36}\b",
                    0.99,
                ),
                (
                    "GitHub server token",
                    r"\bghs_[A-Za-z0-9]{36}\b",
                    0.99,
                ),
                (
                    "GitHub refresh token",
                    r"\bghr_[A-Za-z0-9]{36}\b",
                    0.99,
                ),
            ],
        )
    )

    # -----------------------------------------------------------------------
    # JWT
    # -----------------------------------------------------------------------

    recognizers.append(
        _recognizer(
            name="JWT Recognizer",
            entity="JWT",
            patterns=[
                (
                    "JSON Web Token",
                    (
                        r"\beyJ[A-Za-z0-9_-]{5,}"
                        r"\.[A-Za-z0-9_-]{5,}"
                        r"\.[A-Za-z0-9_-]{5,}\b"
                    ),
                    0.99,
                ),
            ],
        )
    )

    # -----------------------------------------------------------------------
    # HTTP Bearer token
    # -----------------------------------------------------------------------

    recognizers.append(
        BearerValueRecognizer()
    )

    # -----------------------------------------------------------------------
    # PEM private keys
    #
    # This works particularly well for text files. OCR of multiline PEM
    # blocks will be handled separately by the image pipeline.
    # -----------------------------------------------------------------------

    recognizers.append(
        _recognizer(
            name="Private Key Recognizer",
            entity="PRIVATE_KEY",
            patterns=[
                (
                    "PEM private key",
                    (
                        r"-----BEGIN "
                        r"(?:RSA |EC |OPENSSH |DSA )?"
                        r"PRIVATE KEY-----"
                        r"[\s\S]+?"
                        r"-----END "
                        r"(?:RSA |EC |OPENSSH |DSA )?"
                        r"PRIVATE KEY-----"
                    ),
                    1.0,
                ),
            ],
        )
    )

    # -----------------------------------------------------------------------
    # Tailscale
    # -----------------------------------------------------------------------

    recognizers.append(
        _recognizer(
            name="Tailscale Key Recognizer",
            entity="TAILSCALE_KEY",
            patterns=[
                (
                    "Tailscale private node key",
                    r"\bprivkey:[A-Za-z0-9_-]{8,}\b",
                    0.99,
                ),
                (
                    "Tailscale network-lock private key",
                    r"\bnlpriv:[A-Za-z0-9_-]{8,}\b",
                    0.99,
                ),
                (
                    "Tailscale auth key",
                    r"\btskey-auth-[A-Za-z0-9_-]{8,}\b",
                    0.99,
                ),
                (
                    "Tailscale API key",
                    r"\btskey-api-[A-Za-z0-9_-]{8,}\b",
                    0.99,
                ),
                (
                    "Tailscale OAuth client secret",
                    r"\btskey-client-[A-Za-z0-9_-]{8,}\b",
                    0.99,
                ),
            ],
        )
    )

    # -----------------------------------------------------------------------
    # n8n encryption key
    # -----------------------------------------------------------------------

    recognizers.append(
        AssignmentValueRecognizer(
            name="n8n Encryption Key Recognizer",
            supported_entity="N8N_ENCRYPTION_KEY",
            keys=[
                "N8N_ENCRYPTION_KEY",
            ],
            score=0.99,
            min_length=8,
        )
    )

    # -----------------------------------------------------------------------
    # Password assignments
    # -----------------------------------------------------------------------

    recognizers.append(
        AssignmentValueRecognizer(
            name="Password Assignment Recognizer",
            supported_entity="PASSWORD",
            keys=[
                "password",
                "passwd",
                "pwd",
            ],
            score=0.95,
            min_length=4,
        )
    )

    # -----------------------------------------------------------------------
    # Client secrets
    # -----------------------------------------------------------------------

    recognizers.append(
        AssignmentValueRecognizer(
            name="Client Secret Recognizer",
            supported_entity="CLIENT_SECRET",
            keys=[
                "client_secret",
                "client-secret",
                "clientsecret",
            ],
            score=0.99,
            min_length=6,
        )
    )

    # -----------------------------------------------------------------------
    # Generic secret assignments
    # -----------------------------------------------------------------------

    recognizers.append(
        AssignmentValueRecognizer(
            name="Generic Secret Recognizer",
            supported_entity="GENERIC_SECRET",
            keys=[
                "api_key",
                "api-key",
                "apikey",
                "access_token",
                "access-token",
                "accesstoken",
                "auth_token",
                "auth-token",
                "authtoken",
                "secret_key",
                "secret-key",
                "secretkey",
            ],
            score=0.95,
            min_length=8,
        )
    )

    # -----------------------------------------------------------------------
    # Connection strings
    #
    # Entire credential-bearing connection strings are redacted because
    # usernames, passwords, hosts and database names may all be sensitive.
    # -----------------------------------------------------------------------

    recognizers.append(
        _recognizer(
            name="Connection String Recognizer",
            entity="CONNECTION_STRING",
            patterns=[
                (
                    "Database URI containing credentials",
                    (
                        r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|"
                        r"redis|amqp|mssql)"
                        r"://[^\s\"'<>]+"
                    ),
                    0.99,
                ),
                (
                    "Server connection string containing password",
                    (
                        r"\b(?:server|data source)\s*=\s*[^;\r\n]+;"
                        r"[^\r\n]*"
                        r"\b(?:password|pwd)\s*=\s*[^;\r\n]+"
                    ),
                    0.99,
                ),
            ],
        )
    )

    return recognizers


# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------

def register_devops_recognizers(analyzer):
    """
    Register all custom DevOps recognizers with an AnalyzerEngine.

    Usage:

        analyzer = AnalyzerEngine()
        register_devops_recognizers(analyzer)
    """

    for recognizer in get_devops_recognizers():
        analyzer.registry.add_recognizer(recognizer)

    return analyzer
