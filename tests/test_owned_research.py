"""Ownership truth, private local recall and credential-free CLI regression."""

import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from owned_research import assess, markdown, recall, remember, repo_id


class OwnedResearchTests(unittest.TestCase):
    def inventory(self, repos=None, complete=True):
        return {"observed_at": "2026-10-30T00:00:00Z", "complete": complete,
                "repositories": repos if repos is not None else [{"full_name": "me/tool", "fork": False}]}

    def result(self, inventory, name="me/tool", **extra):
        return assess(inventory, [{"full_name": name, **extra}])["results"][0]

    def test_exact_case_insensitive(self):
        self.assertEqual(self.result(self.inventory(), "ME/TOOL")["ownership"], "PRESENT")

    def test_parent_and_source(self):
        inv = self.inventory([{"full_name": "me/renamed", "fork": True,
                               "parent_full_name": "upstream/child", "source_full_name": "original/root"}])
        for name in ["upstream/child", "original/root"]:
            self.assertEqual(self.result(inv, name)["identity_matches"][0]["basis"], "fork_ancestry")

    def test_same_basename_is_not_identity(self):
        self.assertEqual(self.result(self.inventory(), "other/tool")["ownership"], "NOT_IN_SNAPSHOT")

    def test_incomplete_or_missing_ancestry_is_unknown(self):
        for inv in [self.inventory(complete=False), self.inventory([{"full_name": "me/tool", "fork": True}]),
                    self.inventory([{"full_name": "me/tool"}])]:
            self.assertEqual(self.result(inv, "other/tool")["ownership"], "UNKNOWN")

    def test_partial_fork_ancestry_does_not_prove_absence(self):
        for ancestry in [{"parent_full_name": "intermediate/tool"},
                         {"source_full_name": "original/tool"}]:
            inv = self.inventory([{"full_name": "me/tool", "fork": True, **ancestry}])
            self.assertEqual(self.result(inv, "other/tool")["ownership"], "UNKNOWN")

    def test_contradictory_fork_metadata_rejected(self):
        inv = self.inventory([{"full_name": "me/tool", "fork": False,
                               "parent_full_name": "other/tool"}])
        with self.assertRaises(ValueError):
            self.result(inv, "other/tool")

    def test_malformed_record_shapes_rejected(self):
        for inv, candidates in [([], []), (self.inventory([None]), []),
                                (self.inventory(), [None]),
                                (self.inventory([{"full_name": "me/tool", "fork": "false"}]), [])]:
            with self.assertRaises(ValueError):
                assess(inv, candidates)

    def test_capability_overlap_is_not_identity_or_runtime(self):
        inv = self.inventory([{"full_name": "me/tool", "fork": False, "capabilities": ["memory"]}])
        result = self.result(inv, "other/alternative", capabilities=["memory"])
        self.assertEqual(result["next_action"], "COMPARE_WITH_EXISTING")
        self.assertEqual(result["identity_matches"], [])
        self.assertEqual(result["runtime_status"], "NOT_ESTABLISHED")

    def test_reject_ambiguous_or_unsafe_identity(self):
        for value in ["tool", "https://evil.test/a/b", "https://github.com/a/b/blob/main/x", "a/b?x"]:
            with self.assertRaises(ValueError):
                repo_id(value)
        self.assertEqual(repo_id("https://github.com/Owner/Tool.git"), "owner/tool")

    def test_require_timestamp_and_completeness(self):
        for key, value in [("observed_at", None), ("observed_at", "2026-10-30"), ("complete", "yes")]:
            inv = self.inventory()
            inv[key] = value
            with self.assertRaises(ValueError):
                assess(inv, [])

    def test_input_digest_tracks_content(self):
        a = assess(self.inventory(), [])
        b = assess(self.inventory(complete=False), [])
        self.assertNotEqual(a["input_sha256"], b["input_sha256"])

    def test_append_recall_preserves_existing_table(self):
        with tempfile.TemporaryDirectory() as root:
            db = Path(root) / "memory.db"
            with sqlite3.connect(db) as conn:
                conn.execute("CREATE TABLE scored_repos (value TEXT)")
                conn.execute("INSERT INTO scored_repos VALUES ('retained')")
            first = assess(self.inventory(), [])
            second = assess(self.inventory(complete=False), [])
            remember(db, first)
            remember(db, second)
            self.assertEqual(recall(db), second)
            with sqlite3.connect(db) as conn:
                self.assertEqual(conn.execute("SELECT count(*) FROM ownership_runs").fetchone()[0], 2)
                self.assertEqual(conn.execute("SELECT value FROM scored_repos").fetchone()[0], "retained")

    def test_missing_recall_does_not_create_database(self):
        with tempfile.TemporaryDirectory() as root:
            db = Path(root) / "missing.db"
            with self.assertRaises(ValueError):
                recall(db)
            self.assertFalse(db.exists())

    @unittest.skipUnless(os.name == "posix", "POSIX permission semantics")
    def test_new_memory_database_is_owner_only_even_with_permissive_umask(self):
        with tempfile.TemporaryDirectory() as root:
            db = Path(root) / "private.db"
            previous = os.umask(0)
            try:
                remember(db, assess(self.inventory(), []))
            finally:
                os.umask(previous)
            self.assertEqual(db.stat().st_mode & 0o777, 0o600)

    def test_markdown_escapes_supplied_time_text(self):
        report = assess(self.inventory(), [])
        report["observed_at"] = "<script>|\n"
        rendered = markdown(report)
        self.assertNotIn("<script>", rendered)
        self.assertIn("&#124;", rendered)

    def test_cli_restart_recall_without_credentials(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            inv, candidates, db = root / "inventory.json", root / "candidates.json", root / "memory.db"
            inv.write_text(json.dumps(self.inventory()))
            candidates.write_text(json.dumps([{"full_name": "me/tool"}]))
            command = [sys.executable, str(Path(__file__).resolve().parents[1] / "owned_research.py")]
            env = {"PATH": os.environ.get("PATH", "")}
            written = subprocess.run(command + ["--inventory", str(inv), "--candidates", str(candidates),
                                               "--database", str(db)], env=env, capture_output=True, text=True, check=True)
            restored = subprocess.run(command + ["--recall", "--database", str(db)],
                                      env=env, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(written.stdout), json.loads(restored.stdout))


if __name__ == "__main__":
    unittest.main()
