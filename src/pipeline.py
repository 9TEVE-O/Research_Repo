"""
Pipeline module
===============
Represents the agent pipeline with **explicit dependencies** between steps.

Dependency chain (as described in the problem statement)::

    VisualStep ──produces──► clue
        │
        ▼
    clue ──constrains──► SearchStep ──produces──► search result
        │                                              │
        │                                              ▼
        └──────────────────────────────► next VisualStep
                                                       │
                                                       ▼
                                                  reconcile_evidence()
                                                       │
                                                       ▼
                                                  AnswerStep (final answer)

Each :class:`StepResult` records what the step produced and whether the result
has been verified.  A :class:`DependencyGraph` tracks which steps depend on
which others and enforces that dependencies are present before a step runs.
:class:`AgentPipeline` wires everything together and delegates policy checks
to :class:`~src.guardrails.Guardrails`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from src.guardrails import Guardrails, GuardrailError  # noqa: F401 – re-exported


# ---------------------------------------------------------------------------
# Step types and results
# ---------------------------------------------------------------------------


class StepType(Enum):
    """Identifies the kind of work a pipeline step performs."""

    VISUAL = "visual"
    SEARCH = "search"
    ANSWER = "answer"


@dataclass
class StepResult:
    """Immutable record of what a single pipeline step produced.

    Attributes
    ----------
    step_id:
        Unique identifier for the step instance.
    step_type:
        The :class:`StepType` of the step.
    output:
        The primary output value of the step.
    clues:
        List of clue strings extracted during a visual step.  Empty for
        search and answer steps.
    verified:
        Whether the result has been explicitly verified (e.g. by a human
        or an automated checker).
    """

    step_id: str
    step_type: StepType
    output: Any
    clues: list[str] = field(default_factory=list)
    verified: bool = False

    def verify(self) -> None:
        """Mark this result as successfully verified."""
        self.verified = True


# ---------------------------------------------------------------------------
# Dependency graph
# ---------------------------------------------------------------------------


@dataclass
class _Node:
    """Internal graph node for a single pipeline step."""

    step_id: str
    step_type: StepType
    depends_on: list[str] = field(default_factory=list)
    result: StepResult | None = None

    @property
    def is_satisfied(self) -> bool:
        """True when the step has a result recorded."""
        return self.result is not None


class DependencyGraph:
    """Directed acyclic graph that tracks explicit inter-step dependencies.

    Usage::

        graph = DependencyGraph()
        graph.add_step("visual_1", StepType.VISUAL)
        graph.add_step("search_1", StepType.SEARCH, depends_on=["visual_1"])
        graph.add_step("answer_1", StepType.ANSWER, depends_on=["search_1"])
    """

    def __init__(self) -> None:
        self._nodes: dict[str, _Node] = {}

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def add_step(
        self,
        step_id: str,
        step_type: StepType,
        depends_on: list[str] | None = None,
    ) -> _Node:
        """Register a new step node.

        :param step_id: Unique identifier for this step.
        :param step_type: The kind of work the step performs.
        :param depends_on: List of *step_id* values that must have results
            before this step may record its own result.
        :returns: The newly created :class:`_Node`.
        :raises ValueError: If *step_id* is already registered.
        """
        if step_id in self._nodes:
            raise ValueError(f"Step '{step_id}' is already registered in the graph.")
        node = _Node(step_id=step_id, step_type=step_type, depends_on=depends_on or [])
        self._nodes[step_id] = node
        return node

    # ------------------------------------------------------------------
    # Result recording
    # ------------------------------------------------------------------

    def record_result(self, step_id: str, result: StepResult) -> None:
        """Store the result produced by a step.

        :raises KeyError: If *step_id* is not registered.
        :raises ValueError: If *result* does not match the registered step's
            identifier or type.
        :raises RuntimeError: If one or more declared dependencies have not
            yet recorded results.
        """
        if step_id not in self._nodes:
            raise KeyError(f"Step '{step_id}' is not registered in the dependency graph.")
        node = self._nodes[step_id]
        if result.step_id != step_id:
            raise ValueError(
                f"Result step_id '{result.step_id}' does not match registered step "
                f"'{step_id}'."
            )
        if result.step_type != node.step_type:
            raise ValueError(
                f"Result step_type '{result.step_type}' does not match registered "
                f"step type '{node.step_type}' for step '{step_id}'."
            )
        unsatisfied = self._unsatisfied_dependencies(step_id)
        if unsatisfied:
            raise RuntimeError(
                f"Step '{step_id}' cannot record a result because the "
                f"following dependencies have not yet completed: {unsatisfied}"
            )
        node.result = result

    def _unsatisfied_dependencies(self, step_id: str) -> list[str]:
        node = self._nodes[step_id]
        return [
            dep
            for dep in node.depends_on
            if dep not in self._nodes or not self._nodes[dep].is_satisfied
        ]

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_result(self, step_id: str) -> StepResult | None:
        """Return the result for *step_id*, or ``None`` if not yet recorded."""
        node = self._nodes.get(step_id)
        return node.result if node else None

    def dependencies_satisfied(self, step_id: str) -> bool:
        """Return ``True`` when all declared dependencies of *step_id* have results."""
        node = self._nodes.get(step_id)
        if node is None:
            return False
        return not self._unsatisfied_dependencies(step_id)

    def all_clues(self) -> list[str]:
        """Aggregate all clues produced across every visual step in the graph."""
        clues: list[str] = []
        for node in self._nodes.values():
            if node.step_type is StepType.VISUAL and node.result:
                clues.extend(node.result.clues)
        return clues

    def all_search_results(self) -> list[StepResult]:
        """Return all results produced by search steps."""
        return [
            node.result
            for node in self._nodes.values()
            if node.step_type is StepType.SEARCH and node.result is not None
        ]

    def all_visual_results(self) -> list[StepResult]:
        """Return all results produced by visual steps."""
        return [
            node.result
            for node in self._nodes.values()
            if node.step_type is StepType.VISUAL and node.result is not None
        ]


# ---------------------------------------------------------------------------
# Agent pipeline
# ---------------------------------------------------------------------------


class AgentPipeline:
    """Orchestrates the multi-step agent pipeline with guardrails.

    Each public ``run_*`` method corresponds to one pipeline step type and
    enforces the relevant guardrail before executing.

    Typical usage::

        pipeline = AgentPipeline()

        # Step 1 – visual step extracts a clue
        v1 = pipeline.run_visual_step(
            "visual_1",
            transform_id="edge_detection",
            clues=["suspect wears red hat"],
        )
        pipeline.verify_visual_step("visual_1", "edge_detection")

        # Step 2 – search constrained by the clue
        s1 = pipeline.run_search_step(
            "search_1",
            clue=v1.clues[0],
            query="hat colour sightings",
            depends_on=["visual_1"],
        )

        # Step 3 – reconcile evidence before answering
        pipeline.reconcile_evidence()

        # Step 4 – produce the final answer
        answer = pipeline.run_answer_step("answer_1", depends_on=["search_1"])
    """

    def __init__(self) -> None:
        self.graph = DependencyGraph()
        self._guardrails = Guardrails()
        # Tracks visual transforms: transform_id -> True (verified) | False (failed)
        self._completed_transforms: dict[str, bool] = {}
        self._evidence: list[StepResult] = []
        self._evidence_reconciled: bool = False

    # ------------------------------------------------------------------
    # Visual step
    # ------------------------------------------------------------------

    def run_visual_step(
        self,
        step_id: str,
        transform_id: str,
        *,
        clues: list[str] | None = None,
        output: Any = None,
        depends_on: list[str] | None = None,
        processor: Callable[[Any], tuple[list[str], Any]] | None = None,
        input_data: Any = None,
    ) -> StepResult:
        """Execute a visual processing step that produces clues.

        The step is rejected if the same *transform_id* was previously applied
        and verified successfully (guardrail 3).

        :param step_id: Unique identifier for this step.
        :param transform_id: Logical name for the visual transform being
            applied (e.g. ``"edge_detection"``).  Repeated applications of
            the same transform are blocked once the transform is verified.
        :param clues: Pre-computed list of clues (used when no *processor* is
            supplied).
        :param output: Pre-computed output value (used when no *processor* is
            supplied).
        :param depends_on: Step IDs whose results must exist before this step
            is registered in the dependency graph.
        :param processor: Optional callable ``(input_data) -> (clues, output)``
            that computes clues and output from raw input.
        :param input_data: Raw input forwarded to *processor* when supplied.
        :returns: The :class:`StepResult` produced by this step.
        :raises GuardrailError: If *transform_id* was already applied and
            verified.
        """
        self._guardrails.check_visual_transform_not_repeated(
            transform_id, self._completed_transforms
        )
        self.graph.add_step(step_id, StepType.VISUAL, depends_on)

        if processor is not None:
            extracted_clues, computed_output = processor(input_data)
        else:
            extracted_clues = list(clues or [])
            computed_output = output

        result = StepResult(
            step_id=step_id,
            step_type=StepType.VISUAL,
            output=computed_output,
            clues=extracted_clues,
        )
        self.graph.record_result(step_id, result)
        self._evidence.append(result)
        # Mark transform as not-yet-verified until verify_visual_step() is called
        self._completed_transforms[transform_id] = False
        return result

    def verify_visual_step(self, step_id: str, transform_id: str) -> None:
        """Mark a visual step result as successfully verified.

        Once verified, re-applying the same *transform_id* is blocked by
        guardrail 3.

        :param step_id: The step whose result is being verified.
        :param transform_id: The logical transform name to mark as verified.
        """
        result = self.graph.get_result(step_id)
        if result is not None:
            result.verify()
        self._completed_transforms[transform_id] = True

    def fail_visual_verification(self, transform_id: str) -> None:
        """Record that verification of a visual transform failed.

        This allows the same *transform_id* to be retried.

        :param transform_id: The logical transform name whose verification
            failed.
        """
        self._completed_transforms[transform_id] = False

    # ------------------------------------------------------------------
    # Search step
    # ------------------------------------------------------------------

    def run_search_step(
        self,
        step_id: str,
        *,
        clue: str | None = None,
        query: str,
        depends_on: list[str] | None = None,
        requires_clue: bool = True,
        searcher: Callable[[str], Any] | None = None,
    ) -> StepResult:
        """Execute a search step constrained by an extracted clue.

        The step is rejected if no clue is available and *requires_clue* is
        ``True`` (guardrail 1).

        :param step_id: Unique identifier for this step.
        :param clue: The clue extracted by a preceding visual step.
        :param query: Base search query; the clue is appended to form the
            final constrained query.
        :param depends_on: Step IDs whose results must exist before this step.
        :param requires_clue: When ``False``, the clue-check is skipped.
        :param searcher: Optional callable ``(constrained_query) -> output``
            that executes the actual search.
        :returns: The :class:`StepResult` produced by this step.
        :raises GuardrailError: If *requires_clue* is ``True`` and *clue* is
            absent.
        """
        self._guardrails.check_search_has_clue(clue, requires_clue=requires_clue)
        self.graph.add_step(step_id, StepType.SEARCH, depends_on)

        constrained_query = f"{query} {clue}".strip() if clue else query

        if searcher is not None:
            raw_output = searcher(constrained_query)
        else:
            raw_output = {"query": constrained_query, "results": []}

        result = StepResult(
            step_id=step_id,
            step_type=StepType.SEARCH,
            output=raw_output,
        )
        self.graph.record_result(step_id, result)
        self._evidence.append(result)
        return result

    # ------------------------------------------------------------------
    # Evidence reconciliation
    # ------------------------------------------------------------------

    def reconcile_evidence(self) -> bool:
        """Cross-validate all collected evidence before the final answer step.

        Reconciliation checks that at least one visual step and one search
        step have completed, and that every clue extracted by visual steps
        is represented in the search results.

        :returns: ``True`` when evidence is consistent and sufficient;
            ``False`` otherwise.
        """
        visual_results = self.graph.all_visual_results()
        search_results = self.graph.all_search_results()

        if not visual_results or not search_results:
            self._evidence_reconciled = False
            return False

        # Cross-validation: every clue must appear in at least one search query
        all_clues = self.graph.all_clues()
        uncovered_clues = [
            clue
            for clue in all_clues
            if not any(
                clue in (str(sr.output) if sr.output is not None else '')
                for sr in search_results
            )
        ]

        self._evidence_reconciled = len(uncovered_clues) == 0
        return self._evidence_reconciled

    # ------------------------------------------------------------------
    # Answer step
    # ------------------------------------------------------------------

    def run_answer_step(
        self,
        step_id: str,
        *,
        depends_on: list[str] | None = None,
        answer_producer: Callable[[dict[str, Any]], Any] | None = None,
    ) -> StepResult:
        """Produce the final answer, requiring cross-validated evidence.

        The step is rejected if :meth:`reconcile_evidence` has not been called
        and returned ``True`` (guardrail 2).

        :param step_id: Unique identifier for this step.
        :param depends_on: Step IDs whose results must exist before this step.
        :param answer_producer: Optional callable
            ``(evidence_summary) -> output`` that generates the answer.
        :returns: The :class:`StepResult` produced by this step.
        :raises GuardrailError: If evidence has not been reconciled.
        """
        self._guardrails.check_answer_has_reconciliation(
            self._evidence, self._evidence_reconciled
        )
        self.graph.add_step(step_id, StepType.ANSWER, depends_on)

        evidence_summary: dict[str, Any] = {
            "visual_clues": self.graph.all_clues(),
            "search_results": [r.output for r in self.graph.all_search_results()],
        }

        if answer_producer is not None:
            output = answer_producer(evidence_summary)
        else:
            output = evidence_summary

        result = StepResult(
            step_id=step_id,
            step_type=StepType.ANSWER,
            output=output,
            verified=True,
        )
        self.graph.record_result(step_id, result)
        return result
