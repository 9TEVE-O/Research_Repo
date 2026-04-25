"""
Guardrails module
=================
Enforces dependency rules that prevent unjustified jumps in the agent pipeline.

Three rules are applied:

1. **No search without a clue** – for clue-dependent tasks a search step may
   only proceed when a visual step has already extracted at least one clue.

2. **No final answer without evidence reconciliation** – an answer step may
   only proceed after all collected evidence has been cross-validated.

3. **No repeated visual transform unless prior verification failed** – a visual
   transform may only be re-applied if the previous application of that same
   transform did not pass verification.
"""

from __future__ import annotations


class GuardrailError(Exception):
    """Raised when a guardrail rejects a pipeline action."""


class Guardrails:
    """Stateless checker that enforces the three pipeline guardrails.

    Every method raises :class:`GuardrailError` when the corresponding rule is
    violated; it returns ``None`` silently when the rule is satisfied.
    """

    # ------------------------------------------------------------------
    # Rule 1: no search without an extracted clue
    # ------------------------------------------------------------------

    def check_search_has_clue(
        self,
        clue: str | None,
        *,
        requires_clue: bool = True,
    ) -> None:
        """Reject a search step when no clue has been extracted yet.

        :param clue: The clue extracted by the most recent visual step, or
            ``None`` / empty string if no clue is available.
        :param requires_clue: When ``False`` the check is skipped (allows
            search steps that are not driven by a visual clue).
        :raises GuardrailError: If *requires_clue* is ``True`` and *clue* is
            absent or empty.
        """
        if requires_clue and not clue:
            raise GuardrailError(
                "Search rejected: no clue has been extracted. "
                "A visual step must produce a clue before a clue-dependent "
                "search is executed."
            )

    # ------------------------------------------------------------------
    # Rule 2: no final answer without evidence reconciliation
    # ------------------------------------------------------------------

    def check_answer_has_reconciliation(
        self,
        evidence: list,
        reconciled: bool,
    ) -> None:
        """Reject a final-answer step when evidence has not been reconciled.

        :param evidence: All evidence items collected so far.
        :param reconciled: Whether :meth:`AgentPipeline.reconcile_evidence`
            has been called and returned ``True``.
        :raises GuardrailError: If *evidence* is empty or *reconciled* is
            ``False``.
        """
        if not evidence or not reconciled:
            raise GuardrailError(
                "Final answer rejected: evidence has not been reconciled. "
                "Call reconcile_evidence() to cross-validate all evidence "
                "before producing a final answer."
            )

    # ------------------------------------------------------------------
    # Rule 3: no repeated visual transform unless prior verification failed
    # ------------------------------------------------------------------

    def check_visual_transform_not_repeated(
        self,
        transform_id: str,
        completed_transforms: dict[str, bool],
    ) -> None:
        """Reject a visual transform that was already applied and verified.

        :param transform_id: Unique identifier for the visual transform type.
        :param completed_transforms: Mapping of *transform_id* → *verified*
            (``True`` means the previous application passed verification).
        :raises GuardrailError: If *transform_id* is already in
            *completed_transforms* with a ``True`` (verified) value.
        """
        if completed_transforms.get(transform_id) is True:
            raise GuardrailError(
                f"Visual transform '{transform_id}' rejected: it has already "
                "been applied and verified successfully. Repeating a "
                "successful visual transform is not allowed."
            )
