# Evidence-Grade Marketing
## Treatment-Only Shared Evidence Contract v0.2

**Status:** FROZEN CORRECTED TEST BASELINE  
**Supersedes:** v0.1  
**Execution status:** NOT TESTED

The governing separation is:

evidence != interpretation != claim != recommendation != authority != outcome

## 1. MarketingEvidenceRecord

```text
MarketingEvidenceRecord
evidence_id
subject_ref
origin
source_ref
source_date
observed_or_retrieved_at
source_role
evidence_form
identity_integrity
verification
freshness
applicability
source_lineage_id
independence_status
statement_or_observation
market_scope
audience_scope
time_scope
limitations[]
supports[]
contradicts[]
```

## 2. Source role

`source_role` identifies whose evidence or material is being represented.

```text
CUSTOMER
COMPETITOR
BUSINESS
THIRD_PARTY
EXPERT
SYSTEM
OTHER
UNKNOWN
```

It does not describe the form of the evidence and does not establish truth.

## 3. Evidence form

`evidence_form` describes what kind of evidentiary material the record contains.

```text
DIRECT_OBSERVATION
SELF_REPORT
SOURCE_STATEMENT
DERIVED_METRIC
EXPERIMENTAL_RESULT
INTERPRETATION
OTHER
UNKNOWN
```

A third-party report may therefore contain several separate evidence records. These must not be silently collapsed into one evidentiary status.

## 4. Identity and integrity

```text
VALIDATED
ATTESTED
CLAIMED
UNKNOWN
FAILED
```

This dimension concerns whether the source or evidence object is what it purports to be. It does not establish whether the substantive claim is correct.

## 5. Verification

```text
VERIFIED
CORROBORATED
UNVERIFIED
DISPUTED
FAILED_VERIFICATION
NOT_APPLICABLE
UNKNOWN
```

Verification remains independent of source identity, freshness and applicability.

## 6. Freshness

```text
CURRENT
STALE
UNKNOWN
NOT_TIME_SENSITIVE
```

Freshness concerns time. It does not establish whether evidence is relevant or comparable to the current decision.

## 7. Applicability

```text
APPLICABLE
PARTIALLY_APPLICABLE
NOT_COMPARABLE
UNKNOWN
```

Applicability asks whether the evidence can legitimately inform the current subject, market, audience, decision or comparison.

## 8. Source lineage and independence

`source_lineage_id` identifies the underlying source lineage when known.

`independence_status`:

```text
INDEPENDENT_EVIDENCE
PARTIALLY_INDEPENDENT
NOT_INDEPENDENT
UNKNOWN
NOT_APPLICABLE
```

Independence is assessed relative to the claim and evidence set under review. Shared lineage does not automatically answer every independence question. Repetition must never be treated as independent corroboration merely because it appears in several publications.

## 9. Marketing claim assessment

```text
MarketingClaimAssessment
claim_id
claim_text
claim_scope
evidence_refs[]
support_status
limitations[]
required_recheck
```

Allowed support states:

```text
SUPPORTED
PARTIALLY_SUPPORTED
INSUFFICIENT
CONTRADICTED
NOT_TESTED
```

Support is always relative to the exact claim and scope.

## 10. Causal status

```text
DESCRIPTIVE_ONLY
ATTRIBUTED_BY_MODEL
CAUSAL_EFFECT_ESTIMATED
CAUSAL_EFFECT_NOT_ESTABLISHED
EVIDENCE_AGAINST_CAUSAL_EFFECT
INCONCLUSIVE
```

- `DESCRIPTIVE_ONLY`: an outcome or association was observed; no attribution or causal conclusion is established.
- `ATTRIBUTED_BY_MODEL`: an explicit attribution model assigned some outcome to a channel, campaign or touchpoint; this is not causal proof.
- `CAUSAL_EFFECT_ESTIMATED`: a design intended to estimate incremental causal effect produced an effect estimate; uncertainty and methodological limitations remain.
- `CAUSAL_EFFECT_NOT_ESTABLISHED`: available evidence does not justify causal inference; this does not prove no effect exists.
- `EVIDENCE_AGAINST_CAUSAL_EFFECT`: an appropriate causal evaluation produced evidence weighing against the specified material causal effect; do not infer this merely from absence of significance.
- `INCONCLUSIVE`: a causal-capable evaluation was attempted, but uncertainty remains too large to support the relevant decision.

## 11. Authority assessment

```text
AuthorityAssessment
action_ref
authority_requirement
authority_evidence
authority_basis_ref
limitations[]
```

`authority_requirement`:

```text
REQUIRED
NOT_REQUIRED
UNKNOWN
```

`authority_evidence`:

```text
PRESENT
ABSENT
UNKNOWN
```

Evidence quality never supplies missing authority.

## 12. Experiment integrity

```text
ExperimentRecord
experiment_id
revision
question
hypothesis
intervention
comparison
primary_metric
secondary_metrics[]
guardrails[]
success_rule
stop_rule
declared_at
observations
analysis
limitations[]
result
decision
```

Any post-declaration change records:

```text
changed_at
change_reason
result_visible_at_change
```

If the relevant result was already visible, the original experiment cannot be retrospectively rewritten. The new proposition becomes `EXPLORATORY_FINDING` or `NEW_EXPERIMENT`.

## 13. Loop integrity

```text
LoopRunRecord
loop_id
run_id
trigger
checked_at
input_state_ref
deduplication_key
threshold_result
candidate_action
authority_requirement
authority_evidence
execution_status
postcondition
next_check
```

Allowed execution states:

```text
NO_ACTION
CANDIDATE_ONLY
EXECUTED
FAILED
UNKNOWN
```

`NO_ACTION` is a valid successful run.

## 14. Shared invariants

1. Evidence does not become stronger because marketing copy sounds confident.
2. Customer anecdotes cannot silently become population claims.
3. Genuine competitor material does not automatically verify the claims contained within it.
4. Repetition through one source lineage does not create independent corroboration.
5. Source lineage and substantive independence remain separate.
6. Identity, verification, freshness and applicability remain separate.
7. Attribution is not causation.
8. Failure to establish causation is not evidence that no causal effect exists.
9. A result cannot rewrite its original hypothesis or success criterion.
10. Evidence cannot create spending or publication authority.
11. A recommendation is not permission.
12. Missing evidence may legitimately produce `UNKNOWN`, `INSUFFICIENT` or `INCONCLUSIVE`.
13. Automated actions require duplicate-action protection where retries or recurrence could repeat the action.
14. A loop that correctly finds nothing requiring action has succeeded.
