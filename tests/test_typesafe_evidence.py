"""Transport/schema boundary tests; these do not measure Jev accuracy."""
import copy
import json
from unittest.mock import MagicMock
from urllib.error import HTTPError, URLError

import pytest

from typesafe_evidence import ClassificationError, ENDPOINT, classify, no_redirect_opener

RECORD = dict(claim="The project is MIT licensed.", source_text="License: MIT",
              source_url="https://example.org/source", source_accessed_at="2026-10-07")
RESPONSE = dict(model="jev-test", answers={"source_support": dict(
    type="choice", choice="SUPPORTED", confidence=1,
    probabilities=dict(SUPPORTED=1, CONTRADICTED=0, INSUFFICIENT=0, ABSTAIN=0))},
    usage=dict(input_tokens=100, output_tokens=20))


def transport(data):
    opener = MagicMock()
    response = opener.return_value.__enter__.return_value
    response.read.return_value = json.dumps(data).encode()
    response.geturl.return_value = ENDPOINT
    return opener


def test_request_and_review_boundary():
    opener = transport(RESPONSE)
    result = classify({**RECORD, "private_extra": "must not be sent"}, api_key="test", opener=opener)
    request = opener.call_args.args[0]
    assert request.full_url == ENDPOINT
    assert json.loads(request.data)["state"] == RECORD
    assert result["raw_response"] == RESPONSE
    assert result["review_required"] is True
    assert result["promotion_status"] == "NOT_PROMOTED"
    assert "Authorization" not in json.dumps(result)


@pytest.mark.parametrize("label", ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT", "ABSTAIN"])
def test_every_label_requires_review(label):
    data = copy.deepcopy(RESPONSE)
    answer = data["answers"]["source_support"]
    answer["choice"] = label
    answer["probabilities"] = {k: int(k == label) for k in answer["probabilities"]}
    result = classify(RECORD, api_key="key", opener=transport(data))
    assert result["classification"] == label
    assert result["review_required"] and result["promotion_status"] == "NOT_PROMOTED"


@pytest.mark.parametrize("field,value", [("confidence", True), ("confidence", float('nan')),
                                         ("choice", "VERIFIED"), ("type", "score"),
                                         ("probabilities", {"SUPPORTED": 1})])
def test_malformed_answers_fail_closed(field, value):
    data = copy.deepcopy(RESPONSE)
    data["answers"]["source_support"][field] = value
    with pytest.raises(ClassificationError):
        classify(RECORD, api_key="key", opener=transport(data))


def test_missing_key_or_source_never_calls_api():
    opener = MagicMock()
    for record, key in [(RECORD, ""), ({**RECORD, "source_text": ""}, "key")]:
        with pytest.raises(ClassificationError):
            classify(record, api_key=key, opener=opener)
    opener.assert_not_called()


@pytest.mark.parametrize("error", [HTTPError(ENDPOINT, 401, "secret", {}, None), URLError("secret")])
def test_transport_errors_do_not_leak_details(error):
    opener = MagicMock(side_effect=error)
    with pytest.raises(ClassificationError) as exc:
        classify(RECORD, api_key="key", opener=opener)
    assert "secret" not in str(exc.value)


def test_redirect_handler_refuses_redirects():
    opener = no_redirect_opener().__self__
    handler = next(h for h in opener.handlers if hasattr(h, "redirect_request"))
    assert handler.redirect_request(None, None, 302, "", {}, "https://other.org") is None


@pytest.mark.parametrize("data", [[], {}, {**RESPONSE, "usage": {"input_tokens": True, "output_tokens": 0}}])
def test_malformed_envelope_fails_closed(data):
    with pytest.raises(ClassificationError):
        classify(RECORD, api_key="key", opener=transport(data))


def test_invalid_distribution_fails_closed():
    data = copy.deepcopy(RESPONSE)
    data["answers"]["source_support"]["probabilities"]["SUPPORTED"] = 0.5
    with pytest.raises(ClassificationError):
        classify(RECORD, api_key="key", opener=transport(data))
