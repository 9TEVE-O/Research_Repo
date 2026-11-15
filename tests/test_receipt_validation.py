"""Synthetic receipt-input contract tests. No provider calls or truth assessment."""
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from receipt_validation import ReceiptValidationError, validate_receipt

SOURCE = {"claim": "Supplier notice is 60 days", "source_text": "Notice: 60 days",
          "source_url": "https://example.org/contract", "source_accessed_at": "2026-11-16"}
RESPONSE = {"model": "jev-test", "answers": {"source_support": {"type": "choice", "choice": "SUPPORTED",
            "confidence": 0.99, "probabilities": {"SUPPORTED": 0.99, "CONTRADICTED": 0.0,
            "INSUFFICIENT": 0.01, "ABSTAIN": 0.0}}}, "usage": {"input_tokens": 23, "output_tokens": 5}}


def receipt_for(source=SOURCE, response=RESPONSE):
    state = {k: source[k] for k in ("claim", "source_text", "source_url", "source_accessed_at")}
    return {"contract_version": "claim-source-support-v0.1", "evaluated_at": "2026-11-16T00:00:00+00:00",
            "input_sha256": hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest(),
            "requested_model": "jev-latest", "raw_response": copy.deepcopy(response),
            "classification": "SUPPORTED", "review_required": True, "promotion_status": "NOT_PROMOTED"}


def test_matches_input_without_promotion():
    result = validate_receipt(SOURCE, receipt_for())
    assert result["status"] == "MATCHES_SUPPLIED_INPUT"
    assert result["review_required"] and result["promotion_status"] == "NOT_PROMOTED"
    assert result["semantic_accuracy"] == "NOT_VERIFIED"
    assert result["provider_authenticity"] == "NOT_VERIFIED"
    assert result["external_effect"] == "NONE"


@pytest.mark.parametrize("mutation", [
    lambda s,r: s.update(source_text="Notice: 30 days"),
    lambda s,r: r.update(input_sha256="0" * 64),
    lambda s,r: r.update(contract_version="different"),
    lambda s,r: r.update(review_required=False),
    lambda s,r: r.update(promotion_status="VERIFIED"),
    lambda s,r: r.update(classification="CONTRADICTED"),
    lambda s,r: r["raw_response"]["answers"]["source_support"].update(choice="ABSTAIN"),
    lambda s,r: r["raw_response"]["answers"]["source_support"].update(confidence=float("nan")),
    lambda s,r: r["raw_response"]["answers"]["source_support"].update(probabilities={"SUPPORTED": 1}),
    lambda s,r: r["raw_response"]["answers"]["source_support"].update(probabilities={"SUPPORTED": 0.2, "CONTRADICTED": 0.8, "INSUFFICIENT": 0, "ABSTAIN": 0}),
    lambda s,r: r["raw_response"]["usage"].update(input_tokens=True),
    lambda s,r: r.update(requested_model=""),
])
def test_fails_closed_on_mutation(mutation):
    source, receipt = copy.deepcopy(SOURCE), receipt_for()
    mutation(source, receipt)
    with pytest.raises(ReceiptValidationError):
        validate_receipt(source, receipt)


@pytest.mark.parametrize("label", ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT", "ABSTAIN"))
def test_all_four_classes_remain_review_only(label):
    receipt = receipt_for()
    receipt["classification"] = label
    answer = receipt["raw_response"]["answers"]["source_support"]
    answer["choice"] = label
    answer["probabilities"] = {k: int(k == label) for k in answer["probabilities"]}
    assert validate_receipt(SOURCE, receipt)["promotion_status"] == "NOT_PROMOTED"


def test_caller_extra_fields_not_in_original_digest():
    assert validate_receipt({**SOURCE, "private_notes": "not transmitted"}, receipt_for())["status"] == "MATCHES_SUPPLIED_INPUT"


def test_cli_receipt_path_runs_without_api_key_or_network(tmp_path):
    source_file, receipt_file = tmp_path / "source.json", tmp_path / "receipt.json"
    source_file.write_text(json.dumps(SOURCE))
    receipt_file.write_text(json.dumps(receipt_for()))
    env = {k: v for k, v in os.environ.items() if k != "TYPESAFE_API_KEY"}
    cp = subprocess.run([sys.executable, "typesafe_evidence.py", str(source_file), "--receipt", str(receipt_file)],
                        cwd=Path(__file__).parents[1], env=env, capture_output=True, text=True, timeout=10)
    assert cp.returncode == 0, cp.stderr
    result = json.loads(cp.stdout)
    assert result["status"] == "MATCHES_SUPPLIED_INPUT"
    assert result["review_required"] and result["external_effect"] == "NONE"


def test_cli_invalid_receipt_exits_nonzero(tmp_path):
    source_file, receipt_file = tmp_path / "source.json", tmp_path / "receipt.json"
    source_file.write_text(json.dumps(SOURCE))
    receipt_file.write_text(json.dumps({**receipt_for(), "input_sha256": "0" * 64}))
    cp = subprocess.run([sys.executable, "typesafe_evidence.py", str(source_file), "--receipt", str(receipt_file)],
                        cwd=Path(__file__).parents[1], capture_output=True, text=True, timeout=10)
    assert cp.returncode != 0
    assert "input digest" in cp.stderr
