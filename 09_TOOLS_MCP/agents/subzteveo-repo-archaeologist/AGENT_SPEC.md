# Agent Spec: Subzteveø Repo Archaeologist

## Purpose
Discover high-signal GitHub science / CS / maths / physics repositories and collections, reverse-engineer them into evidence-backed analyses, and return a thesis-driven packet suitable for audit and reuse.

## Non-negotiable invariants
1. **No invention**: any consequential claim MUST be tied to at least one Evidence Anchor (repo, commit SHA, path, line range / notebook cell).
2. **Always return**: a Return Packet is produced even when partial failures occur (with explicit error reporting).
3. **No execution of untrusted code**: analysis is static. No running repo scripts/tests/build systems unless explicitly allow-listed.
4. **Budgeted branching**: each branch has time/call/bytes budgets. Exceeding budget triggers graceful degradation and return.
5. **Atomic output**: write packet to a temp directory, validate schema, then move into place.


## Default branch budgets (anti-degeneration)
- Data limit (`max_bytes`): **50 MiB** per branch (`50 * 1024 * 1024`).
- API limit (`max_requests` / `max_api_calls`): **100** requests per branch.
- Time limit (`max_seconds`): **60.0s** wall-clock per branch.

Branches may override these defaults, but must remain budgeted and must degrade gracefully on budget exhaustion.

## Decision loop
1. **Plan**: expand the user query into sub-queries per branch.
2. **Branch**: run discovery branches concurrently under budgets.
3. **Merge**: canonicalise and dedupe candidates; rank using stored heuristics.
4. **Select**: choose top N for deep-dive analysis.
5. **Analyse**: safe checkout (pin commit SHA) + extract evidence anchors + generate artefacts.
6. **Quality Gate**: fail-closed for unanchored claims; mark hypotheses/open questions.
7. **Return**: write + validate Return Packet; optionally commit.

## Branch catalogue
- `CollectionScoutBranch`: find curated lists (“awesome-*”, topic hubs, course repos).
- `RepoScoutBranch`: direct repo search by keywords.
- `StackFitScoutBranch`: search for components (parsers, solvers, simulators, compilers).
- `MaintainerScoutBranch`: identify labs/orgs/maintainers with consistent high-signal output.

## Quality Gate rules (summary)
- A thesis claim must be one of: **Claim(Evidenced)**, **Hypothesis**, **OpenQuestion**.
- **Claim(Evidenced)** requires ≥1 Evidence Anchor.
- Any missing evidence forces downgrade to **Hypothesis** with a verification plan.
- Licence absence/ambiguity must be flagged in `RISKS.md`.
- Suspicious patterns (secrets, obfuscation, unusual install scripts) must be surfaced.

## Self-diagnosis and “relearning”
- `self_diagnose()` runs:
  - schema validation for last packet
  - internal consistency checks (all evidenced claims anchored)
  - health checks (cache writable, learning store writable)
- `relearn()` updates ranking heuristics weights based on observed outcomes (e.g., later manual labels), writing a provenance log that cites packet IDs and hashes.

See `docs/RETURN_PACKET_SCHEMA.md` for the contract.
