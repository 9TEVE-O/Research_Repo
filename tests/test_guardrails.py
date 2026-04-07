"""
Tests for src/guardrails.py
============================
Covers all three guardrail rules:

1. No search without an extracted clue (on clue-dependent tasks).
2. No final answer without evidence reconciliation.
3. No repeated visual transform unless prior verification failed.
"""

import pytest

from src.guardrails import GuardrailError, Guardrails


@pytest.fixture()
def guardrails() -> Guardrails:
    return Guardrails()


# ---------------------------------------------------------------------------
# Rule 1 – no search without a clue
# ---------------------------------------------------------------------------


class TestSearchHasClue:
    def test_raises_when_clue_is_none(self, guardrails: Guardrails) -> None:
        with pytest.raises(GuardrailError, match="no clue has been extracted"):
            guardrails.check_search_has_clue(None, requires_clue=True)

    def test_raises_when_clue_is_empty_string(self, guardrails: Guardrails) -> None:
        with pytest.raises(GuardrailError, match="no clue has been extracted"):
            guardrails.check_search_has_clue("", requires_clue=True)

    def test_passes_when_clue_is_present(self, guardrails: Guardrails) -> None:
        # Should not raise
        guardrails.check_search_has_clue("red hat", requires_clue=True)

    def test_passes_when_requires_clue_is_false_and_clue_absent(
        self, guardrails: Guardrails
    ) -> None:
        # Clue-independent searches are allowed without a clue
        guardrails.check_search_has_clue(None, requires_clue=False)
        guardrails.check_search_has_clue("", requires_clue=False)

    def test_default_requires_clue_is_true(self, guardrails: Guardrails) -> None:
        with pytest.raises(GuardrailError):
            guardrails.check_search_has_clue(None)


# ---------------------------------------------------------------------------
# Rule 2 – no final answer without reconciliation
# ---------------------------------------------------------------------------


class TestAnswerHasReconciliation:
    def test_raises_when_not_reconciled(self, guardrails: Guardrails) -> None:
        with pytest.raises(GuardrailError, match="evidence has not been reconciled"):
            guardrails.check_answer_has_reconciliation(evidence=["item"], reconciled=False)

    def test_raises_when_evidence_is_empty(self, guardrails: Guardrails) -> None:
        with pytest.raises(GuardrailError, match="evidence has not been reconciled"):
            guardrails.check_answer_has_reconciliation(evidence=[], reconciled=True)

    def test_raises_when_evidence_empty_and_not_reconciled(
        self, guardrails: Guardrails
    ) -> None:
        with pytest.raises(GuardrailError):
            guardrails.check_answer_has_reconciliation(evidence=[], reconciled=False)

    def test_passes_when_reconciled_with_evidence(self, guardrails: Guardrails) -> None:
        # Should not raise
        guardrails.check_answer_has_reconciliation(
            evidence=["search result"], reconciled=True
        )


# ---------------------------------------------------------------------------
# Rule 3 – no repeated visual transform unless prior failed
# ---------------------------------------------------------------------------


class TestVisualTransformNotRepeated:
    def test_raises_when_transform_already_verified(
        self, guardrails: Guardrails
    ) -> None:
        completed = {"edge_detection": True}
        with pytest.raises(GuardrailError, match="edge_detection"):
            guardrails.check_visual_transform_not_repeated("edge_detection", completed)

    def test_passes_when_transform_not_yet_applied(
        self, guardrails: Guardrails
    ) -> None:
        guardrails.check_visual_transform_not_repeated("edge_detection", {})

    def test_passes_when_prior_verification_failed(
        self, guardrails: Guardrails
    ) -> None:
        # False means "applied but not verified" → retry is allowed
        completed = {"edge_detection": False}
        guardrails.check_visual_transform_not_repeated("edge_detection", completed)

    def test_different_transform_ids_are_independent(
        self, guardrails: Guardrails
    ) -> None:
        completed = {"edge_detection": True}
        # A different transform should be permitted even if edge_detection is blocked
        guardrails.check_visual_transform_not_repeated("colour_histogram", completed)
