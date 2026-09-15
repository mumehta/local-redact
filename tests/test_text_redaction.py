from presidio_analyzer import RecognizerResult

from redact import filter_analyzer_results, is_identifier_like


def test_identifier_like_detection():
    assert is_identifier_like("AWS_SECRET_ACCESS_KEY")
    assert is_identifier_like("N8N_ENCRYPTION_KEY")
    assert not is_identifier_like("John Smith")
    assert not is_identifier_like("client_secret")


def test_filter_removes_identifier_like_nlp_false_positive():
    text = "AWS_SECRET_ACCESS_KEY=abcdefghijklmnopqrstuvwxyz1234567890ABCD"
    key_result = RecognizerResult(
        entity_type="LOCATION",
        start=0,
        end=len("AWS_SECRET_ACCESS_KEY"),
        score=0.85,
    )
    value_result = RecognizerResult(
        entity_type="AWS_SECRET_KEY",
        start=len("AWS_SECRET_ACCESS_KEY="),
        end=len(text),
        score=0.99,
    )

    filtered = filter_analyzer_results(text, [key_result, value_result])

    assert filtered == [value_result]


def test_filter_keeps_non_identifier_pii():
    text = "John Smith"
    result = RecognizerResult(
        entity_type="PERSON",
        start=0,
        end=len(text),
        score=0.85,
    )

    assert filter_analyzer_results(text, [result]) == [result]
