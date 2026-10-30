"""Ownership truth, private local recall and credential-free CLI regression."""

import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from owned_research import assess, markdown, recall, remember, repo_id, private_markdown_file


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

    def test_multi_hop_fork_preserves_unknown_intermediate(self):
        inv = self.inventory([{"full_name": "me/tool", "fork": True,
                               "parent_full_name": "parent/tool", "source_full_name": "root/tool"}])
        self.assertEqual(self.result(inv, "intermediate/tool")["ownership"], "UNKNOWN")
        for known in ["parent/tool", "root/tool"]:
            self.assertEqual(self.result(inv, known)["ownership"], "PRESENT")

    def test_direct_fork_can_establish_snapshot_absence(self):
        inv = self.inventory([{"full_name": "me/tool", "fork": True,
                               "parent_full_name": "Root/Tool", "source_full_name": "root/tool"}])
        self.assertEqual(self.result(inv, "other/tool")["ownership"], "NOT_IN_SNAPSHOT")

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

    def test_recall_specific_id_preserves_latest_legacy_and_missing_id(self):
        with tempfile.TemporaryDirectory() as root:
            db = Path(root) / "memory.db"
            first = assess(self.inventory(), [{"full_name": "me/first"}])
            second = assess(self.inventory(), [{"full_name": "me/second"}])
            first_id = remember(db, first)
            second_id = remember(db, second)
            self.assertEqual(recall(db, first_id), first)
            self.assertEqual(recall(db, second_id), second)
            self.assertEqual(recall(db), second)
            for invalid in (0, -1, True, "1"):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    recall(db, invalid)
            with self.assertRaisesRegex(ValueError, "ID 9999"):
                recall(db, 9999)
            self.assertEqual(recall(db), second)

    def test_cli_recall_by_id_and_opt_in_receipt_across_processes(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            db = root / "memory.db"
            inv = root / "inventory.json"
            candidates = root / "candidates.json"
            inv.write_text(json.dumps(self.inventory()), encoding="utf-8")
            candidates.write_text(json.dumps([{"full_name": "me/first"}]), encoding="utf-8")
            cmd = [sys.executable, str(Path(__file__).resolve().parents[1] / "owned_research.py")]
            saved = subprocess.run(cmd + ["--inventory", str(inv), "--candidates", str(candidates),
                                          "--database", str(db), "--emit-assessment-id"],
                                   capture_output=True, text=True, check=True)
            self.assertIn("assessment_id=1", saved.stderr)
            first_report = json.loads(saved.stdout)
            candidates.write_text(json.dumps([{"full_name": "me/second"}]), encoding="utf-8")
            saved2 = subprocess.run(cmd + ["--inventory", str(inv), "--candidates", str(candidates),
                                           "--database", str(db), "--emit-assessment-id"],
                                    capture_output=True, text=True, check=True)
            self.assertIn("assessment_id=2", saved2.stderr)
            retrieved = subprocess.run(cmd + ["--recall", "--assessment-id", "1", "--database", str(db)],
                                       capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(retrieved.stdout), first_report)
            latest = subprocess.run(cmd + ["--recall", "--database", str(db)],
                                    capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(latest.stdout), json.loads(saved2.stdout))
            unknown = subprocess.run(cmd + ["--recall", "--assessment-id", "9999", "--database", str(db)],
                                     capture_output=True, text=True)
            self.assertEqual(unknown.returncode, 2)
            self.assertIn("ID 9999", unknown.stderr)
            self.assertFalse(unknown.stdout)
            invalid = subprocess.run(cmd + ["--assessment-id", "1", "--database", str(db)],
                                     capture_output=True, text=True)
            self.assertEqual(invalid.returncode, 2)
            self.assertIn("requires --recall", invalid.stderr)

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

    @unittest.skipUnless(os.name == "posix", "POSIX permission semantics")
    def test_reused_memory_database_is_made_private(self):
        with tempfile.TemporaryDirectory() as root:
            db = Path(root) / "existing.db"
            db.touch(mode=0o644)
            db.chmod(0o644)
            remember(db, assess(self.inventory(), []))
            self.assertEqual(db.stat().st_mode & 0o777, 0o600)

    @unittest.skipUnless(os.name == "posix", "POSIX permission semantics")
    def test_existing_wal_sidecars_are_private_before_append(self):
        with tempfile.TemporaryDirectory() as root:
            db = Path(root) / "existing.db"
            conn = sqlite3.connect(db)
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("CREATE TABLE existing (value TEXT)")
                conn.execute("INSERT INTO existing VALUES ('retained')")
                conn.commit()
                sidecars = [Path(str(db) + suffix) for suffix in ("-wal", "-shm")]
                for path in sidecars:
                    path.chmod(0o644)
                report = assess(self.inventory(), [{"full_name": "me/tool"}])
                remember(db, report)
                for path in sidecars:
                    self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                self.assertEqual(recall(db), report)
                self.assertEqual(conn.execute("SELECT value FROM existing").fetchone()[0], "retained")
                self.assertEqual(conn.execute("PRAGMA journal_mode").fetchone()[0], "wal")
            finally:
                conn.close()

    def test_database_connections_are_closed(self):
        real_connect = sqlite3.connect
        closed = []

        class TrackedConnection(sqlite3.Connection):
            def close(self):
                closed.append(self)
                super().close()

        def connect(*args, **kwargs):
            return real_connect(*args, **kwargs, factory=TrackedConnection)

        with tempfile.TemporaryDirectory() as root:
            db = Path(root) / "memory.db"
            with patch("owned_research.sqlite3.connect", side_effect=connect):
                remember(db, assess(self.inventory(), []))
                recall(db)
                with self.assertRaises(KeyError):
                    remember(db, {})
            self.assertEqual(len(closed), 3)

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

    def run_cli(self, root, *options, extra_env=None):
        root = Path(root)
        inv, candidates, db = root / "inventory.json", root / "candidates.json", root / "memory.db"
        if not inv.exists():
            inventory = self.inventory([{"full_name": "me/tool", "fork": False,
                                        "capabilities": ["mémoire"], "capability_evidence": "日本語"}])
            inv.write_text(json.dumps(inventory, ensure_ascii=False), encoding="utf-8")
            candidates.write_text(json.dumps([{"full_name": "me/tool", "capabilities": ["mémoire"]}],
                                             ensure_ascii=False), encoding="utf-8")
        command = [sys.executable, str(Path(__file__).resolve().parents[1] / "owned_research.py"),
                   "--inventory", str(inv), "--candidates", str(candidates), "--database", str(db), *options]
        env = {"PATH": os.environ.get("PATH", ""), **(extra_env or {})}
        return subprocess.run(command, env=env, capture_output=True)

    def test_cli_utf8_inputs_under_ascii_locale(self):
        with tempfile.TemporaryDirectory() as root:
            result = self.run_cli(root, extra_env={"LC_ALL": "C", "PYTHONUTF8": "0",
                                                   "PYTHONCOERCECLOCALE": "0"})
            self.assertEqual(result.returncode, 0, result.stderr)
            decoded = json.loads(result.stdout)
            self.assertEqual(decoded["results"][0]["capability_overlap"][0]["evidence"], "日本語")

    @unittest.skipUnless(os.name == "posix", "POSIX permission semantics")
    def test_markdown_new_and_reused_outputs_are_private(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "comparison.md"
            result = self.run_cli(root, "--markdown", str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            output.write_text("stale" * 10000, encoding="utf-8")
            output.chmod(0o644)
            result = self.run_cli(root, "--markdown", str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            self.assertTrue(output.read_text(encoding="utf-8").endswith("NOT_ESTABLISHED for all entries.\n"))
            self.assertNotIn("stalestale", output.read_text(encoding="utf-8"))

    def test_markdown_cannot_overwrite_inputs_or_database(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(self.run_cli(root).returncode, 0)
            for name in ["inventory.json", "candidates.json", "memory.db"]:
                path = Path(root) / name
                before = path.read_bytes()
                result = self.run_cli(root, "--markdown", str(path))
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(path.read_bytes(), before)

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires no-follow open support")
    def test_markdown_symlink_does_not_truncate_target(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "unrelated.txt"
            target.write_text("retained", encoding="utf-8")
            output = Path(root) / "comparison.md"
            output.symlink_to(target)
            result = self.run_cli(root, "--markdown", str(output))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), "retained")

    def test_markdown_cannot_use_reserved_database_sidecar_paths(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(self.run_cli(root).returncode, 0)
            db = Path(root) / "memory.db"
            before = db.read_bytes()
            for suffix in ("-wal", "-shm", "-journal"):
                with self.subTest(suffix=suffix):
                    output = Path(str(db) + suffix)
                    self.assertFalse(output.exists())
                    result = self.run_cli(root, "--markdown", str(output))
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertFalse(output.exists())
                    self.assertEqual(db.read_bytes(), before)

    @unittest.skipUnless(os.name == "posix", "POSIX link semantics")
    def test_markdown_sidecar_aliases_preserve_active_wal(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            self.assertEqual(self.run_cli(root).returncode, 0)
            db = root / "memory.db"
            conn = sqlite3.connect(db)
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA wal_autocheckpoint=0")
                conn.execute("CREATE TABLE retained (value TEXT)")
                conn.execute("INSERT INTO retained VALUES ('original')")
                conn.commit()
                wal = Path(str(db) + "-wal")
                before = wal.read_bytes()
                symlink = root / "symlink.md"
                symlink.symlink_to(wal)
                hardlink = root / "hardlink.md"
                os.link(wal, hardlink)
                database_alias = root / "alias.db"
                database_alias.symlink_to(db)
                for output in (wal, symlink, hardlink):
                    for database in (db, database_alias):
                        with self.subTest(output=output.name, database=database.name):
                            result = self.run_cli(root, "--database", str(database),
                                                  "--markdown", str(output))
                            self.assertEqual(result.returncode, 2, result.stderr)
                            self.assertEqual(wal.read_bytes(), before)
                            reader = sqlite3.connect(db)
                            try:
                                self.assertEqual(reader.execute("SELECT value FROM retained").fetchall(),
                                                 [("original",)])
                                self.assertEqual(reader.execute("SELECT count(*) FROM ownership_runs").fetchone()[0], 1)
                            finally:
                                reader.close()
            finally:
                conn.close()


    @unittest.skipUnless(os.name == "posix" and os.open in os.supports_dir_fd
                         and hasattr(os, "O_NOFOLLOW"), "POSIX directory-descriptor semantics")
    def test_markdown_parent_directory_replacement_cannot_hit_wal(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            self.assertEqual(self.run_cli(root).returncode, 0)
            db = root / "memory.db"
            conn = sqlite3.connect(db)
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA wal_autocheckpoint=0")
                conn.execute("CREATE TABLE retained2 (value TEXT)")
                conn.execute("INSERT INTO retained2 VALUES ('original')")
                conn.commit()
                wal = Path(str(db) + "-wal")
                before = wal.read_bytes()
                output_dir = root / "reports"
                output_dir.mkdir()
                output = output_dir / wal.name
                self.assertNotEqual(output.resolve(), wal.resolve())
                # Simulate a replacement between destination validation and open.
                output_dir.rename(root / "old-reports")
                output_dir.symlink_to(root, target_is_directory=True)
                with self.assertRaises(OSError):
                    private_markdown_file(output, [db, wal])
                self.assertEqual(wal.read_bytes(), before)
                self.assertEqual(conn.execute("SELECT value FROM retained2").fetchall(),
                                 [("original",)])
            finally:
                conn.close()

    @unittest.skipUnless(os.name == "posix" and os.open in os.supports_dir_fd
                         and hasattr(os, "O_NOFOLLOW"), "POSIX directory-descriptor semantics")
    def test_markdown_open_rechecks_hardlink_inode_before_truncate(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            self.assertEqual(self.run_cli(root).returncode, 0)
            db = root / "memory.db"
            conn = sqlite3.connect(db)
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA wal_autocheckpoint=0")
                conn.execute("CREATE TABLE retained2 (value TEXT)")
                conn.execute("INSERT INTO retained2 VALUES ('original')")
                conn.commit()
                wal = Path(str(db) + "-wal")
                before = wal.read_bytes()
                output = root / "report.md"
                # Simulate a newly introduced hardlink after path validation.
                os.link(wal, output)
                with self.assertRaisesRegex(ValueError, "aliases a protected"):
                    private_markdown_file(output, [db, wal])
                self.assertEqual(wal.read_bytes(), before)
                self.assertEqual(conn.execute("SELECT value FROM retained2").fetchall(),
                                 [("original",)])
                ordinary = root / "ordinary.md"
                descriptor = private_markdown_file(ordinary, [db, wal])
                with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                    handle.write("safe")
                self.assertEqual(ordinary.read_text(encoding="utf-8"), "safe")
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
