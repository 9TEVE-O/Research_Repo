# AI Studio research terminal, isolated review candidate

**Status: UNVERIFIED DEMO. Do not deploy or merge as a production replacement.**

The source here is a minimally modified import of an AI Studio workspace ZIP
recovered from the account's ChatGPT Library on 2026-11-04. It is intentionally
isolated from the repository's existing Python research agent and its existing
`academic-paper-terminal` application.

The import does **not** include the ZIP's replacement top-level README, Python
project snippets, `.github` workflows, Firebase live config, or `.env.example`.
The Firebase config has been replaced by an unconfigured placeholder. The
source Firestore rules and adversarial case **definitions** have been moved into
`security-review/`; they are not deployed, and the test definitions do not run
the Firestore emulator.

## Demonstrated limitations in source

- RepoScoringPipeline.tsx assigns random scores, repository counts and policy
  summaries to added candidates. They are not produced by `scoring.py`.
- AcademicTerminal.tsx selects bundled paper records and can synthesize a
  paper with a randomly generated arXiv-shaped identifier. It does not
  retrieve authoritative sources live.
- TypeSafeClassifier.tsx computes a local SHA-256 but derives outcomes from
  local text logic; no TypeSafe provider request is made.
- Firebase authentication, Firestore persistence, authorisation rules, actual
  saved data, hosting and project ownership have not been validated.

## Local build gate

Install Bun in a disposable environment, then run from this directory:

```bash
bun install --frozen-lockfile --ignore-scripts
bun run lint
bun run build
```

The code has not been built or executed. The `--ignore-scripts` option reduces dependency lifecycle execution during installation, but installing untrusted packages still belongs in a disposable environment. These commands are a **required gate**, not a
claim of passing tests. A successful build would not establish that the
research results are accurate or that Firestore security is correct.

Do not replace `src/firebase-applet-config.json` with real production details
until the Firebase account, rules and data handling have been independently
reviewed. Treat the preview UI as synthetic demonstration material.

## Important correction from independent recheck

`src/firebase.ts` calls `testConnection()` at module load and initialises Firebase
with placeholders in this review copy. Thus the candidate is **not an offline
functional preview**; do not assume all UI flows work simply because the
TypeScript parses. Firestore emulator tests are not wired up. The only supplied
script is staging-only; no automatic PR publication or dependency execution.
