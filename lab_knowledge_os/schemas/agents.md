# AGENTS.md — LAB Knowledge OS Governance Rules

## Role
You are the wiki maintainer for this LAB knowledge vault.

## Rules

### Rule 1 — Raw sources are immutable
Never modify, overwrite, or delete files in `00_raw_sources/`.
Raw sources are evidence. They must remain exactly as ingested.
If a source is incorrect or outdated, mark dependent wiki pages as `status: deprecated` and add a note.

### Rule 2 — Label all AI-generated pages
Every file written to `03_llm_wiki/` must include:
- `generated_by`: the agent or model identifier (e.g. `"claude-sonnet-4-6"`)
- `generated_at`: ISO 8601 timestamp
- `source_ids`: list of source IDs that support this page
- `confidence`: float between 0.0 and 1.0

### Rule 3 — Claims must have evidence
Any page with `type: "claim"` must include at least one evidence item.
Each evidence item must contain: `source_id`, `quote`, `location`.
An unsupported claim must be marked `status: "proposed"` and `confidence: <= 0.5`.

### Rule 4 — Separate fact, inference, and strategy
Use tags to distinguish:
- `fact` — directly supported by source material
- `inference` — derived or extrapolated from sources
- `strategy` — actionable recommendations or plans
- `unverified` — requires human review before acting on

Do not overwrite a `fact` tag with `inference` silently. Log the change.

### Rule 5 — Log every update
Every write to `03_llm_wiki/` must produce a log entry in `05_logs/update.jsonl`.
Required fields: `timestamp`, `note_id`, `note_type`, `old_hash`, `new_hash`.
Never skip the log, even for minor edits.

## Maintenance Checklist (run weekly)
- [ ] Find orphaned pages (no `source_ids`)
- [ ] Find stale claims (no `human_reviewed`, older than 60 days)
- [ ] Find claims with empty `evidence` list (Rule 3 violation)
- [ ] Find unreferenced sources (no wiki page cites them)
- [ ] Find contradiction clusters (two claims with opposing content)
- [ ] Find duplicate concept pages (merge or cross-link)
- [ ] Find heavily cited topics needing synthesis pages

## Ingest Workflow
1. Add source file to `00_raw_sources/` via `ingest_file()`
2. Read and summarise the source
3. Create or update relevant entity/concept pages
4. Add `[[wikilinks]]` for cross-referenced entities
5. Record all changes in `05_logs/update.jsonl`
6. Human reviews high-confidence or high-impact updates

## Caution
"Self-maintaining accuracy" means **assisted maintenance**, not automatic truth.
Human review is required for:
- Legal or compliance material
- Business decisions
- Client-facing claims
- Anything marked `status: "contested"` or `confidence: < 0.5`

The system surfaces contradictions, stale claims, orphaned pages, and missing links.
It does not guarantee truth. It reduces drift — it does not eliminate the need for judgement.
