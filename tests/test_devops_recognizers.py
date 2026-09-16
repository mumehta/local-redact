from presidio_anonymizer import AnonymizerEngine

from presidio_redactor.recognizers import get_devops_recognizers


def analyze_with_devops_recognizers(text: str):
    results = []

    for recognizer in get_devops_recognizers():
        results.extend(
            recognizer.analyze(
                text=text,
                entities=recognizer.get_supported_entities(),
                nlp_artifacts=None,
            )
        )

    return sorted(results, key=lambda result: result.start)


def anonymize_with_devops_recognizers(text: str) -> str:
    results = analyze_with_devops_recognizers(text)
    return AnonymizerEngine().anonymize(
        text=text,
        analyzer_results=results,
    ).text


def test_custom_recognizers_construct_without_presidio_pattern_error():
    recognizers = get_devops_recognizers()

    assert recognizers
    assert {entity for recognizer in recognizers for entity in recognizer.get_supported_entities()} >= {
        "AWS_ACCESS_KEY",
        "AWS_SECRET_KEY",
        "BEARER_TOKEN",
        "GITHUB_TOKEN",
    }


def test_assignment_recognizers_redact_values_only():
    text = "\n".join(
        [
            "AWS_SECRET_ACCESS_KEY=abcdefghijklmnopqrstuvwxyz1234567890ABCD",
            "N8N_ENCRYPTION_KEY=FAKE_ENCRYPTION_KEY_123456",
            "password=FakePassword123",
            "client_secret=FakeClientSecret123",
            "api_key=FakeApiKey123456789",
        ]
    )

    redacted = anonymize_with_devops_recognizers(text)

    assert "AWS_SECRET_ACCESS_KEY=<AWS_SECRET_KEY>" in redacted
    assert "N8N_ENCRYPTION_KEY=<N8N_ENCRYPTION_KEY>" in redacted
    assert "password=<PASSWORD>" in redacted
    assert "client_secret=<CLIENT_SECRET>" in redacted
    assert "api_key=<GENERIC_SECRET>" in redacted
    assert "FakePassword123" not in redacted


def test_bearer_recognizer_redacts_token_value_only():
    text = "Authorization: Bearer fake-token-1234567890abcdef"

    redacted = anonymize_with_devops_recognizers(text)

    assert redacted == "Authorization: Bearer <BEARER_TOKEN>"
