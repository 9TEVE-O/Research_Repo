"""Compare discoveries with an observed repository inventory; retain local recall.

Standard library only. This command never calls a model, sends email, or publishes.
Inventory presence does not establish installation or successful execution.
"""

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
from urllib.parse import urlsplit


def repo_id(value):
    """Accept exact owner/repo identities or HTTPS GitHub repository URLs."""
    if not isinstance(value, str):
        raise ValueError("repository identity must be a string")
    if value.startswith("https://"):
        parsed = urlsplit(value)
        if parsed.netloc.lower() != "github.com" or parsed.query or parsed.fragment:
            raise ValueError("expected a GitHub repository URL")
        value = parsed.path.strip("/")
    value = value.removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        raise ValueError("expected owner/repo, not a name or file URL")
    return value.lower()


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("observed_at must be a timezone-aware ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid observed_at") from exc
    if parsed.utcoffset() is None:
        raise ValueError("observed_at must include a timezone")
    return value


def capabilities(record):
    values = record.get("capabilities", [])
    if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values):
        raise ValueError("capabilities must be non-empty strings in a list")
    return set(values)


def assess(inventory, candidates):
    """Identity matching and explicitly supplied capability overlap, separately."""
    if not isinstance(inventory, dict):
        raise ValueError("inventory must be an object")
    observed_at = timestamp(inventory.get("observed_at"))
    if not isinstance(inventory.get("complete"), bool):
        raise ValueError("inventory.complete must explicitly be true or false")
    repos = inventory.get("repositories")
    if not isinstance(repos, list) or not isinstance(candidates, list):
        raise ValueError("repositories and candidates must be lists")
    indexed = []
    ancestry_complete = True
    for record in repos:
        if not isinstance(record, dict):
            raise ValueError("each repository must be an object")
        name = repo_id(record["full_name"])
        identities = {name}
        fork = record.get("fork")
        if fork is not None and not isinstance(fork, bool):
            raise ValueError("fork must be true, false or null")
        ancestry = [record.get("parent_full_name"), record.get("source_full_name")]
        if fork is False and any(ancestry):
            raise ValueError("non-fork repository cannot have fork ancestry")
        for identity in ancestry:
            if identity:
                identities.add(repo_id(identity))
        # Parent and root identify the whole chain only for a direct fork.
        # A multi-hop fork may have unresolved ancestors between those two.
        if fork is not False and (
            not all(ancestry) or repo_id(ancestry[0]) != repo_id(ancestry[1])
        ):
            ancestry_complete = False
        indexed.append((record, name, identities, capabilities(record)))

    results = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("each candidate must be an object")
        identity = repo_id(candidate["full_name"])
        tags = capabilities(candidate)
        matches = []
        overlap = []
        for record, name, identities, existing_tags in indexed:
            if identity in identities:
                matches.append({"repository": name,
                                "basis": "exact_identity" if identity == name else "fork_ancestry"})
            common = sorted(tags & existing_tags)
            if common:
                overlap.append({"repository": name, "capabilities": common,
                                "evidence": record.get("capability_evidence", "supplied mapping; unverified")})
        ownership = "PRESENT" if matches else (
            "NOT_IN_SNAPSHOT" if inventory["complete"] and ancestry_complete else "UNKNOWN")
        action = "REUSE_OR_TEST_EXISTING" if matches else (
            "COMPARE_WITH_EXISTING" if overlap else "INVESTIGATE")
        results.append({"candidate": identity, "ownership": ownership,
                        "identity_matches": matches, "capability_overlap": overlap,
                        "next_action": action, "runtime_status": "NOT_ESTABLISHED"})
    payload = json.dumps({"inventory": inventory, "candidates": candidates},
                         sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {"schema_version": 1, "observed_at": observed_at,
            "inventory_complete": inventory["complete"],
            "repository_count": len(repos), "input_sha256": hashlib.sha256(payload.encode()).hexdigest(),
            "results": results,
            "boundary": "Repository presence and capability overlap do not establish installation, equivalence or performance."}


def private_file(path, *, create=True):
    """Open a regular output without following symlinks or truncating it yet."""
    flags = os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    if create:
        flags |= os.O_CREAT
    descriptor = os.open(path, flags, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError("output must be a regular file")
        if os.name == "posix":
            os.fchmod(descriptor, 0o600)
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def remember(db_path, report):
    """Append a report to SQLite without changing the existing scored_repos table."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Restrict both new and reused databases before writing private identities.
    os.close(private_file(path))
    # A reused WAL database can have existing sidecars with broader permissions
    # than its main file. SQLite retains their modes when appending new data.
    for suffix in ("-wal", "-shm", "-journal"):
        try:
            descriptor = private_file(Path(str(path) + suffix), create=False)
        except FileNotFoundError:
            continue
        os.close(descriptor)
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS ownership_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            saved_at TEXT NOT NULL, input_sha256 TEXT NOT NULL, report_json TEXT NOT NULL)""")
        cursor = conn.execute("INSERT INTO ownership_runs (saved_at,input_sha256,report_json) VALUES (?,?,?)",
                              (datetime.now(timezone.utc).isoformat(), report["input_sha256"],
                               json.dumps(report, ensure_ascii=False)))
        return cursor.lastrowid


def recall(db_path):
    """Read the last completed report; opening a missing database is an error."""
    path = Path(db_path)
    if not path.is_file():
        raise ValueError("no saved research memory at this path")
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as conn:
        try:
            row = conn.execute("SELECT report_json FROM ownership_runs ORDER BY id DESC LIMIT 1").fetchone()
        except sqlite3.OperationalError as exc:
            raise ValueError("no ownership memory in this database") from exc
    if row is None:
        raise ValueError("no saved research report")
    return json.loads(row[0])


def markdown(report):
    def safe(value):
        return html.escape(str(value)).replace("|", "&#124;").replace("\n", " ").replace("\r", " ")
    lines = ["# Existing software comparison", "",
             f"Observed: {safe(report['observed_at'])}; repositories: {report['repository_count']}; "
             f"complete inventory: {report['inventory_complete']}.", "",
             "| Candidate | Identity match | Capability overlap | Next action |",
             "|---|---|---|---|"]
    for result in report["results"]:
        matches = ", ".join(r["repository"] for r in result["identity_matches"]) or result["ownership"]
        overlap = ", ".join(r["repository"] for r in result["capability_overlap"]) or "None supplied"
        lines.append("| " + " | ".join(safe(v) for v in
                     [result["candidate"], matches, overlap, result["next_action"]]) + " |")
    return "\n".join(lines + ["", report["boundary"], "",
                              "Runtime status: NOT_ESTABLISHED for all entries.", ""])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--candidates", type=Path)
    parser.add_argument("--database", type=Path, default=Path(".local-research/research_agent.db"))
    parser.add_argument("--recall", action="store_true")
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)
    try:
        # An export must never overwrite the database or its source inputs.
        if args.markdown:
            # SQLite may hold uncheckpointed rows in WAL sidecars. An export to
            # any of these paths can truncate or corrupt saved research memory.
            protected = [args.database, args.inventory, args.candidates]
            protected.extend(Path(str(args.database) + suffix)
                             for suffix in ("-wal", "-shm", "-journal"))
            for source in protected:
                if source is not None and (
                    args.markdown.resolve() == source.resolve()
                    or (args.markdown.exists() and source.exists() and args.markdown.samefile(source))
                ):
                    raise ValueError("--markdown must differ from the database, SQLite sidecars and input paths")
        if args.recall:
            if args.inventory or args.candidates:
                raise ValueError("--recall cannot accept new inputs")
            report = recall(args.database)
        else:
            if not args.inventory or not args.candidates:
                raise ValueError("--inventory and --candidates are required")
            report = assess(json.loads(args.inventory.read_text(encoding="utf-8")),
                            json.loads(args.candidates.read_text(encoding="utf-8")))
            remember(args.database, report)
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            rendered = markdown(report)
            descriptor = private_file(args.markdown)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.truncate(0)
                handle.write(rendered)
        # ASCII JSON escapes also work when the terminal locale is not UTF-8.
        print(json.dumps(report, indent=2))
    except (ValueError, KeyError, TypeError, OSError, sqlite3.Error) as exc:
        parser.exit(2, f"owned_research: {exc}\n")


if __name__ == "__main__":
    main()
