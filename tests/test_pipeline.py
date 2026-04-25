"""
Tests for src/pipeline.py
===========================
Covers:
- DependencyGraph: step registration, result recording, dependency checks, queries.
- AgentPipeline: full happy-path, and each of the three guardrail rejection
  scenarios wired through the pipeline.
"""

import pytest

from src.guardrails import GuardrailError
from src.pipeline import AgentPipeline, DependencyGraph, StepResult, StepType


# ---------------------------------------------------------------------------
# DependencyGraph
# ---------------------------------------------------------------------------


class TestDependencyGraph:
    def test_add_and_retrieve_step(self) -> None:
        graph = DependencyGraph()
        graph.add_step("s1", StepType.VISUAL)
        assert graph.get_result("s1") is None

    def test_duplicate_step_raises(self) -> None:
        graph = DependencyGraph()
        graph.add_step("s1", StepType.VISUAL)
        with pytest.raises(ValueError, match="already registered"):
            graph.add_step("s1", StepType.VISUAL)

    def test_record_result_sets_result(self) -> None:
        graph = DependencyGraph()
        graph.add_step("s1", StepType.VISUAL)
        result = StepResult("s1", StepType.VISUAL, output="img", clues=["hat"])
        graph.record_result("s1", result)
        assert graph.get_result("s1") is result

    def test_record_result_unknown_step_raises(self) -> None:
        graph = DependencyGraph()
        with pytest.raises(KeyError):
            graph.record_result(
                "nonexistent",
                StepResult("nonexistent", StepType.VISUAL, output=None),
            )

    def test_record_result_unsatisfied_dependency_raises(self) -> None:
        graph = DependencyGraph()
        graph.add_step("s1", StepType.VISUAL)
        graph.add_step("s2", StepType.SEARCH, depends_on=["s1"])
        with pytest.raises(RuntimeError, match="s1"):
            graph.record_result(
                "s2",
                StepResult("s2", StepType.SEARCH, output={}),
            )

    def test_dependencies_satisfied_after_dep_records_result(self) -> None:
        graph = DependencyGraph()
        graph.add_step("s1", StepType.VISUAL)
        graph.add_step("s2", StepType.SEARCH, depends_on=["s1"])

        assert not graph.dependencies_satisfied("s2")

        result_s1 = StepResult("s1", StepType.VISUAL, output="img", clues=["c1"])
        graph.record_result("s1", result_s1)

        assert graph.dependencies_satisfied("s2")

    def test_all_clues_aggregates_across_visual_steps(self) -> None:
        graph = DependencyGraph()
        graph.add_step("v1", StepType.VISUAL)
        graph.add_step("v2", StepType.VISUAL)

        graph.record_result("v1", StepResult("v1", StepType.VISUAL, output=None, clues=["a", "b"]))
        graph.record_result("v2", StepResult("v2", StepType.VISUAL, output=None, clues=["c"]))

        assert sorted(graph.all_clues()) == ["a", "b", "c"]

    def test_all_clues_ignores_search_and_answer_steps(self) -> None:
        graph = DependencyGraph()
        graph.add_step("v1", StepType.VISUAL)
        graph.add_step("s1", StepType.SEARCH, depends_on=["v1"])

        graph.record_result("v1", StepResult("v1", StepType.VISUAL, output=None, clues=["x"]))
        graph.record_result(
            "s1",
            StepResult("s1", StepType.SEARCH, output={"query": "x search", "results": []}),
        )

        assert graph.all_clues() == ["x"]

    def test_all_search_results(self) -> None:
        graph = DependencyGraph()
        graph.add_step("v1", StepType.VISUAL)
        graph.add_step("s1", StepType.SEARCH, depends_on=["v1"])
        graph.record_result("v1", StepResult("v1", StepType.VISUAL, output=None, clues=["c"]))
        r = StepResult("s1", StepType.SEARCH, output={"query": "c search"})
        graph.record_result("s1", r)
        assert graph.all_search_results() == [r]

    def test_get_result_unknown_step_returns_none(self) -> None:
        graph = DependencyGraph()
        assert graph.get_result("does_not_exist") is None


# ---------------------------------------------------------------------------
# StepResult.verify()
# ---------------------------------------------------------------------------


class TestStepResultVerify:
    def test_verify_sets_verified_flag(self) -> None:
        r = StepResult("s1", StepType.VISUAL, output=None)
        assert not r.verified
        r.verify()
        assert r.verified


# ---------------------------------------------------------------------------
# AgentPipeline – happy path (full dependency chain)
# ---------------------------------------------------------------------------


class TestAgentPipelineHappyPath:
    def test_full_pipeline_succeeds(self) -> None:
        pipeline = AgentPipeline()

        # Step 1: visual step extracts clue
        v1 = pipeline.run_visual_step(
            "visual_1",
            transform_id="edge_detection",
            clues=["red hat"],
            output="processed_image",
        )
        assert v1.clues == ["red hat"]
        assert v1.step_type is StepType.VISUAL

        # Verify the visual step (marks transform as done)
        pipeline.verify_visual_step("visual_1", "edge_detection")
        assert pipeline.graph.get_result("visual_1").verified

        # Step 2: search constrained by clue
        s1 = pipeline.run_search_step(
            "search_1",
            clue="red hat",
            query="hat colour sightings",
            depends_on=["visual_1"],
        )
        assert "red hat" in s1.output["query"]
        assert s1.step_type is StepType.SEARCH

        # Step 3: reconcile evidence
        reconciled = pipeline.reconcile_evidence()
        assert reconciled

        # Step 4: final answer
        answer = pipeline.run_answer_step("answer_1", depends_on=["search_1"])
        assert answer.step_type is StepType.ANSWER
        assert "red hat" in answer.output["visual_clues"]
        assert answer.verified

    def test_visual_step_with_processor(self) -> None:
        pipeline = AgentPipeline()

        def my_processor(data: str) -> tuple[list[str], str]:
            return [data.upper()], f"processed:{data}"

        result = pipeline.run_visual_step(
            "v1",
            transform_id="upper_transform",
            processor=my_processor,
            input_data="hello",
        )
        assert result.clues == ["HELLO"]
        assert result.output == "processed:hello"

    def test_search_step_with_searcher(self) -> None:
        pipeline = AgentPipeline()
        pipeline.run_visual_step("v1", transform_id="t1", clues=["clue_x"])

        def fake_search(query: str) -> dict:
            return {"query": query, "results": ["result_a"]}

        s = pipeline.run_search_step(
            "s1",
            clue="clue_x",
            query="base query",
            depends_on=["v1"],
            searcher=fake_search,
        )
        assert s.output["results"] == ["result_a"]

    def test_answer_step_with_answer_producer(self) -> None:
        pipeline = AgentPipeline()
        pipeline.run_visual_step("v1", transform_id="t1", clues=["clue_y"])
        pipeline.run_search_step("s1", clue="clue_y", query="q", depends_on=["v1"])
        pipeline.reconcile_evidence()

        def produce_answer(evidence: dict) -> str:
            return f"answer based on {evidence['visual_clues']}"

        result = pipeline.run_answer_step("a1", answer_producer=produce_answer)
        assert "clue_y" in result.output


# ---------------------------------------------------------------------------
# AgentPipeline – guardrail 1: search blocked without clue
# ---------------------------------------------------------------------------


class TestGuardrail1SearchWithoutClue:
    def test_search_without_clue_raises(self) -> None:
        pipeline = AgentPipeline()
        with pytest.raises(GuardrailError, match="no clue has been extracted"):
            pipeline.run_search_step("s1", clue=None, query="something")

    def test_search_with_empty_clue_raises(self) -> None:
        pipeline = AgentPipeline()
        with pytest.raises(GuardrailError):
            pipeline.run_search_step("s1", clue="", query="something")

    def test_search_without_clue_allowed_when_requires_clue_false(self) -> None:
        pipeline = AgentPipeline()
        result = pipeline.run_search_step(
            "s1", clue=None, query="independent query", requires_clue=False
        )
        assert result.output["query"] == "independent query"


# ---------------------------------------------------------------------------
# AgentPipeline – guardrail 2: answer blocked without reconciliation
# ---------------------------------------------------------------------------


class TestGuardrail2AnswerWithoutReconciliation:
    def test_answer_without_reconcile_raises(self) -> None:
        pipeline = AgentPipeline()
        pipeline.run_visual_step("v1", transform_id="t1", clues=["c"])
        pipeline.run_search_step("s1", clue="c", query="q", depends_on=["v1"])
        # Deliberately skip reconcile_evidence()
        with pytest.raises(GuardrailError, match="evidence has not been reconciled"):
            pipeline.run_answer_step("a1")

    def test_answer_with_no_evidence_raises(self) -> None:
        pipeline = AgentPipeline()
        with pytest.raises(GuardrailError):
            pipeline.run_answer_step("a1")

    def test_answer_after_failed_reconciliation_raises(self) -> None:
        # reconcile_evidence returns False when there are no search results
        pipeline = AgentPipeline()
        pipeline.run_visual_step("v1", transform_id="t1", clues=["c"])
        # No search step → reconcile returns False
        pipeline.reconcile_evidence()
        with pytest.raises(GuardrailError):
            pipeline.run_answer_step("a1")


# ---------------------------------------------------------------------------
# AgentPipeline – guardrail 3: repeated visual transform blocked
# ---------------------------------------------------------------------------


class TestGuardrail3RepeatedVisualTransform:
    def test_repeat_verified_transform_raises(self) -> None:
        pipeline = AgentPipeline()
        pipeline.run_visual_step("v1", transform_id="edge_detection", clues=["c"])
        pipeline.verify_visual_step("v1", "edge_detection")

        with pytest.raises(GuardrailError, match="edge_detection"):
            pipeline.run_visual_step("v2", transform_id="edge_detection", clues=["d"])

    def test_repeat_unverified_transform_is_allowed(self) -> None:
        pipeline = AgentPipeline()
        pipeline.run_visual_step("v1", transform_id="edge_detection", clues=["c"])
        # Not verified → retry should be permitted
        result = pipeline.run_visual_step("v2", transform_id="edge_detection", clues=["d"])
        assert result.step_id == "v2"

    def test_fail_verification_allows_retry(self) -> None:
        pipeline = AgentPipeline()
        pipeline.run_visual_step("v1", transform_id="edge_detection", clues=["c"])
        pipeline.verify_visual_step("v1", "edge_detection")  # Mark as verified

        # Now fail the verification to allow a retry
        pipeline.fail_visual_verification("edge_detection")

        result = pipeline.run_visual_step("v2", transform_id="edge_detection", clues=["d"])
        assert result.step_id == "v2"

    def test_different_transforms_are_independent(self) -> None:
        pipeline = AgentPipeline()
        pipeline.run_visual_step("v1", transform_id="edge_detection", clues=["c"])
        pipeline.verify_visual_step("v1", "edge_detection")

        # A different transform should still be allowed
        result = pipeline.run_visual_step(
            "v2", transform_id="colour_histogram", clues=["d"]
        )
        assert result.step_id == "v2"


# ---------------------------------------------------------------------------
# AgentPipeline – reconcile_evidence corner cases
# ---------------------------------------------------------------------------


class TestReconcileEvidence:
    def test_returns_false_with_no_steps(self) -> None:
        pipeline = AgentPipeline()
        assert pipeline.reconcile_evidence() is False

    def test_returns_false_with_only_visual_step(self) -> None:
        pipeline = AgentPipeline()
        pipeline.run_visual_step("v1", transform_id="t1", clues=["c"])
        assert pipeline.reconcile_evidence() is False

    def test_returns_true_when_clue_covered_by_search(self) -> None:
        pipeline = AgentPipeline()
        pipeline.run_visual_step("v1", transform_id="t1", clues=["red hat"])
        pipeline.run_search_step("s1", clue="red hat", query="sightings", depends_on=["v1"])
        assert pipeline.reconcile_evidence() is True

    def test_returns_false_when_clue_not_covered_by_any_search(self) -> None:
        pipeline = AgentPipeline()
        pipeline.run_visual_step("v1", transform_id="t1", clues=["red hat"])
        # Search uses a different (unrelated) clue – "red hat" not in query
        pipeline.run_search_step(
            "s1", clue=None, query="blue shoe", requires_clue=False
        )
        assert pipeline.reconcile_evidence() is False
