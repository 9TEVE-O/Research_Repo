"""Offline validator for Research_Repo's existing TypeSafe classification receipts.

Checks a receipt against caller-supplied input bytes and schema only. A matching
hash is NOT a signature, a provider attestation, source authentication, truth,
or authority to promote/execute a decision. No network, persistence or effects.
"""

import hashlib
import json
import math

CONTRACT_VERSION = "claim-source-support-v0.1"
FIELDS = ("claim", "source_text", "source_url", "source_accessed_at")
LABELS = frozenset(("SUPPORTED", "CONTRADICTED", "INSUFFICIENT", "ABSTAIN"))


class ReceiptValidationError(ValueError):
    """Supplied receipt cannot be matched to supplied source under this contract."""


def _probability(value):
    return type(value) in (int, float) and 0 <= value <= 1 and math.isfinite(value)


def validate_receipt(supplied_source, receipt):
    """Validate a *supplied* classifier receipt without contacting TypeSafe.

    Result is always review-required and unpromoted. The input digest follows
    typesafe_evidence.classify's existing exact JSON serialization contract.
    """
    if not isinstance(supplied_source, dict) or not isinstance(receipt, dict):
        raise ReceiptValidationError("Source and receipt must be objects")
    if any(type(supplied_source.get(k)) is not str or not supplied_source[k].strip()
           for k in FIELDS):
        raise ReceiptValidationError("Missing or invalid supplied source fields")
    state = {k: supplied_source[k] for k in FIELDS}
    expected = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
    if receipt.get("contract_version") != CONTRACT_VERSION:
        raise ReceiptValidationError("Unsupported receipt contract")
    if receipt.get("input_sha256") != expected:
        raise ReceiptValidationError("Receipt input digest does not match supplied source")
    if receipt.get("review_required") is not True or receipt.get("promotion_status") != "NOT_PROMOTED":
        raise ReceiptValidationError("Receipt must remain unpromoted and human-reviewable")
    if not isinstance(receipt.get("requested_model"), str) or not receipt["requested_model"].strip():
        raise ReceiptValidationError("Missing requested model identity")
    if not isinstance(receipt.get("evaluated_at"), str) or not receipt["evaluated_at"].strip():
        raise ReceiptValidationError("Missing evaluation timestamp")
    response = receipt.get("raw_response")
    if not isinstance(response, dict) or not isinstance(response.get("model"), str) or not response["model"]:
        raise ReceiptValidationError("Missing response model identity")
    try:
        answer = response["answers"]["source_support"]
        usage = response["usage"]
    except (KeyError, TypeError):
        raise ReceiptValidationError("Incomplete classifier response") from None
    if (not isinstance(answer, dict) or answer.get("type") != "choice" or
            not isinstance(answer.get("choice"), str) or answer["choice"] not in LABELS):
        raise ReceiptValidationError("Unsupported classifier answer")
    probabilities = answer.get("probabilities")
    if not isinstance(probabilities, dict) or set(probabilities) != LABELS:
        raise ReceiptValidationError("Classifier labels have changed")
    if not all(_probability(value) for value in probabilities.values()):
        raise ReceiptValidationError("Invalid probability")
    if not math.isclose(sum(probabilities.values()), 1.0, rel_tol=0, abs_tol=1e-6):
        raise ReceiptValidationError("Probabilities do not sum to one")
    if probabilities[answer["choice"]] != max(probabilities.values()):
        raise ReceiptValidationError("Selected class does not have highest probability")
    if not _probability(answer.get("confidence")):
        raise ReceiptValidationError("Invalid confidence")
    if receipt.get("classification") != answer["choice"]:
        raise ReceiptValidationError("Receipt classification disagrees with model answer")
    if not isinstance(usage, dict) or any(type(usage.get(k)) is not int or usage[k] < 0
                                          for k in ("input_tokens", "output_tokens")):
        raise ReceiptValidationError("Invalid token usage")
    return {
        "status": "MATCHES_SUPPLIED_INPUT",
        "contract_version": CONTRACT_VERSION,
        "input_sha256": expected,
        "classification": answer["choice"],
        "model_returned": response["model"],
        "review_required": True,
        "promotion_status": "NOT_PROMOTED",
        "source_authenticity": "NOT_VERIFIED",
        "semantic_accuracy": "NOT_VERIFIED",
        "provider_authenticity": "NOT_VERIFIED",
        "external_effect": "NONE",
    }
