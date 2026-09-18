import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "design_harness.py"
spec = importlib.util.spec_from_file_location("design_harness_journal", MODULE_PATH)
design_harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design_harness)


class DesignHarnessRunJournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Path(self.tmp.name)
        self.run = design_harness.start_run(
            store=self.store,
            run_id="journal_run",
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            authorities={},
            profile_id="product-to-ui",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def read_events(self):
        path = design_harness.run_journal_path(self.store, self.run["run_id"])
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_new_run_writes_revision_one_journal_event(self):
        events = self.read_events()

        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["run_id"], self.run["run_id"])
        self.assertEqual(event["revision"], 1)
        self.assertEqual(event["previous_revision"], 0)
        self.assertEqual(event["event_type"], "run.created")
        self.assertEqual(event["snapshot"]["revision"], 1)
        self.assertIsNone(event["previous_event_hash"])
        self.assertTrue(event["event_hash"])
        self.assertTrue(event["snapshot_hash"])

    def test_successful_mutation_appends_hash_chained_event(self):
        updated = design_harness.set_next_action(
            self.store,
            self.run["run_id"],
            {
                "kind": "skill",
                "target": "feature-design",
                "expected_evidence": "behavior",
            },
        )

        events = self.read_events()

        self.assertEqual([e["revision"] for e in events], [1, 2])
        self.assertEqual(events[1]["previous_revision"], 1)
        self.assertEqual(events[1]["previous_event_hash"], events[0]["event_hash"])
        self.assertEqual(events[1]["snapshot"]["revision"], updated["revision"])
        self.assertEqual(events[1]["snapshot"]["next_action"]["target"], "feature-design")

    def test_failed_stale_cas_does_not_append_journal_event(self):
        first = design_harness.load_run(self.store, self.run["run_id"])
        stale = design_harness.load_run(self.store, self.run["run_id"])

        first["next_action"] = {"writer": "first"}
        design_harness.save_run(self.store, first)

        before = self.read_events()

        stale["next_action"] = {"writer": "stale"}
        with self.assertRaises(design_harness.RunConflictError):
            design_harness.save_run(self.store, stale)

        after = self.read_events()
        self.assertEqual(len(after), len(before))
        self.assertEqual(after[-1]["snapshot"]["next_action"], {"writer": "first"})

    def test_verify_journal_accepts_intact_hash_chain(self):
        design_harness.set_next_action(
            self.store,
            self.run["run_id"],
            {
                "kind": "skill",
                "target": "feature-design",
                "expected_evidence": "behavior",
            },
        )

        result = design_harness.verify_run_journal(
            self.store, self.run["run_id"]
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["event_count"], 2)
        self.assertEqual(result["latest_revision"], 2)
        self.assertEqual(result["errors"], [])

    def test_verify_journal_detects_tampered_event(self):
        design_harness.set_next_action(
            self.store,
            self.run["run_id"],
            {
                "kind": "skill",
                "target": "feature-design",
                "expected_evidence": "behavior",
            },
        )
        path = design_harness.run_journal_path(self.store, self.run["run_id"])
        events = self.read_events()
        events[0]["snapshot"]["product_id"] = "tampered"
        path.write_text(
            "\n".join(json.dumps(e, sort_keys=True) for e in events) + "\n",
            encoding="utf-8",
        )

        result = design_harness.verify_run_journal(
            self.store, self.run["run_id"]
        )

        self.assertFalse(result["valid"])
        self.assertGreaterEqual(len(result["errors"]), 1)

    def test_replay_returns_latest_snapshot(self):
        updated = design_harness.set_next_action(
            self.store,
            self.run["run_id"],
            {
                "kind": "skill",
                "target": "feature-design",
                "expected_evidence": "behavior",
            },
        )

        replayed = design_harness.replay_run_from_journal(
            self.store, self.run["run_id"]
        )

        self.assertEqual(replayed["revision"], updated["revision"])
        self.assertEqual(
            replayed["next_action"],
            {
                "kind": "skill",
                "target": "feature-design",
                "expected_evidence": "behavior",
                "required_inputs": [],
            },
        )

    def test_replay_fails_on_invalid_journal_by_default(self):
        path = design_harness.run_journal_path(self.store, self.run["run_id"])
        events = self.read_events()
        events[0]["revision"] = 99
        path.write_text(
            "\n".join(json.dumps(e, sort_keys=True) for e in events) + "\n",
            encoding="utf-8",
        )

        with self.assertRaises(design_harness.JournalIntegrityError):
            design_harness.replay_run_from_journal(
                self.store, self.run["run_id"]
            )

    def test_recover_restores_deleted_materialized_snapshot_without_new_revision(self):
        updated = design_harness.set_next_action(
            self.store,
            self.run["run_id"],
            {
                "kind": "skill",
                "target": "feature-design",
                "expected_evidence": "behavior",
            },
        )
        run_path = self.store / "runs" / f'{self.run["run_id"]}.json'
        run_path.unlink()

        restored = design_harness.recover_run_snapshot(
            self.store, self.run["run_id"]
        )

        self.assertEqual(restored["revision"], updated["revision"])
        self.assertTrue(run_path.exists())
        persisted = design_harness.load_run(self.store, self.run["run_id"])
        self.assertEqual(persisted["revision"], updated["revision"])
        self.assertEqual(len(self.read_events()), 2)

    def test_recover_rejects_when_materialized_snapshot_is_newer_than_journal(self):
        current = design_harness.load_run(self.store, self.run["run_id"])
        current["revision"] = 99
        path = self.store / "runs" / f'{self.run["run_id"]}.json'
        path.write_text(
            json.dumps(current, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        with self.assertRaises(design_harness.JournalRecoveryError):
            design_harness.recover_run_snapshot(
                self.store, self.run["run_id"]
            )

    def test_journal_summary_exposes_latest_commit_metadata(self):
        design_harness.set_next_action(
            self.store,
            self.run["run_id"],
            {
                "kind": "skill",
                "target": "feature-design",
                "expected_evidence": "behavior",
            },
        )

        summary = design_harness.run_journal_summary(
            self.store, self.run["run_id"]
        )

        self.assertEqual(summary["event_count"], 2)
        self.assertEqual(summary["latest_revision"], 2)
        self.assertTrue(summary["latest_event_hash"])
        self.assertEqual(summary["run_id"], self.run["run_id"])


if __name__ == "__main__":
    unittest.main()
