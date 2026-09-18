import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "design_harness.py"
spec = importlib.util.spec_from_file_location("design_harness_audit", MODULE_PATH)
design_harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design_harness)


class DesignHarnessRunAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Path(self.tmp.name)
        self.run = design_harness.start_run(
            store=self.store,
            run_id="audit_run",
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            authorities={"baseline": "shell@v1"},
            profile_id="product-to-ui",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def pass_stage(self, stage, producer="test"):
        return design_harness.resume_run(
            self.store,
            self.run["run_id"],
            {
                "stage": stage,
                "status": "pass",
                "producer": producer,
                "observed_result": f"{stage} ready",
                "artifact_ids": [],
                "input_versions": {},
                "limitations": [],
            },
        )

    def test_snapshot_at_revision_returns_exact_historical_snapshot(self):
        design_harness.set_next_action(
            self.store,
            self.run["run_id"],
            {
                "kind": "skill",
                "target": "feature-design",
                "expected_evidence": "behavior",
            },
        )

        rev1 = design_harness.run_at_revision(
            self.store, self.run["run_id"], 1
        )
        rev2 = design_harness.run_at_revision(
            self.store, self.run["run_id"], 2
        )

        self.assertEqual(rev1["revision"], 1)
        self.assertIsNone(rev1["next_action"])
        self.assertEqual(rev2["revision"], 2)
        self.assertEqual(rev2["next_action"]["target"], "feature-design")

    def test_snapshot_at_revision_rejects_unknown_revision(self):
        with self.assertRaises(design_harness.JournalRevisionNotFoundError):
            design_harness.run_at_revision(
                self.store, self.run["run_id"], 999
            )

    def test_diff_revisions_reports_added_removed_and_changed_paths(self):
        before = design_harness.load_run(self.store, self.run["run_id"])
        before["authorities"]["feature_contract"] = "feature@v1"
        design_harness.save_run(self.store, before)

        after = design_harness.load_run(self.store, self.run["run_id"])
        after["authorities"]["feature_contract"] = "feature@v2"
        after["authorities"]["navigation_contract"] = "navigation@v1"
        after["shared_baseline"] = "shell@v1"
        design_harness.save_run(self.store, after)

        diff = design_harness.diff_run_revisions(
            self.store,
            self.run["run_id"],
            2,
            3,
        )

        changes = {item["path"]: item for item in diff["changes"]}
        self.assertEqual(
            changes["/authorities/feature_contract"]["kind"],
            "changed",
        )
        self.assertEqual(
            changes["/authorities/feature_contract"]["before"],
            "feature@v1",
        )
        self.assertEqual(
            changes["/authorities/feature_contract"]["after"],
            "feature@v2",
        )
        self.assertEqual(
            changes["/authorities/navigation_contract"]["kind"],
            "added",
        )
        self.assertEqual(changes["/shared_baseline"]["kind"], "changed")
        self.assertEqual(diff["from_revision"], 2)
        self.assertEqual(diff["to_revision"], 3)

    def test_diff_can_ignore_volatile_commit_metadata(self):
        design_harness.set_next_action(
            self.store,
            self.run["run_id"],
            {
                "kind": "skill",
                "target": "feature-design",
                "expected_evidence": "behavior",
            },
        )

        diff = design_harness.diff_run_revisions(
            self.store,
            self.run["run_id"],
            1,
            2,
            ignore_volatile=True,
        )

        paths = {item["path"] for item in diff["changes"]}
        self.assertNotIn("/revision", paths)
        self.assertNotIn("/updated_at", paths)
        self.assertIn("/next_action", paths)

    def test_timeline_returns_revision_state_cause_and_hash(self):
        design_harness.set_next_action(
            self.store,
            self.run["run_id"],
            {
                "kind": "skill",
                "target": "feature-design",
                "expected_evidence": "behavior",
            },
        )
        self.pass_stage("baseline", producer="product-design")

        timeline = design_harness.run_audit_timeline(
            self.store, self.run["run_id"]
        )

        self.assertEqual([row["revision"] for row in timeline], [1, 2, 3])
        self.assertEqual(timeline[0]["state"], "INIT")
        self.assertEqual(timeline[-1]["state"], "BASELINE_BOUND")
        self.assertTrue(timeline[-1]["event_hash"])
        self.assertEqual(timeline[-1]["cause"], "stage_advanced")

    def test_timeline_can_filter_revision_range(self):
        design_harness.set_next_action(
            self.store,
            self.run["run_id"],
            {
                "kind": "skill",
                "target": "feature-design",
                "expected_evidence": "behavior",
            },
        )
        self.pass_stage("baseline")

        timeline = design_harness.run_audit_timeline(
            self.store,
            self.run["run_id"],
            from_revision=2,
            to_revision=3,
        )

        self.assertEqual([row["revision"] for row in timeline], [2, 3])

    def test_trace_path_returns_only_value_changes(self):
        design_harness.set_next_action(
            self.store,
            self.run["run_id"],
            {
                "kind": "skill",
                "target": "feature-design",
                "expected_evidence": "behavior",
            },
        )
        self.pass_stage("baseline")
        self.pass_stage("behavior")

        trace = design_harness.trace_run_path(
            self.store,
            self.run["run_id"],
            "/state",
        )

        self.assertEqual(
            [row["value"] for row in trace["changes"]],
            ["INIT", "BASELINE_BOUND", "BEHAVIOR_READY"],
        )
        self.assertEqual(
            [row["revision"] for row in trace["changes"]],
            [1, 3, 4],
        )

    def test_trace_path_can_explain_when_approval_was_added(self):
        run = self.run
        for stage in [
            "baseline",
            "behavior",
            "navigation",
            "task",
            "continuity",
            "candidate",
            "guard",
            "approval-ready",
        ]:
            run = design_harness.resume_run(
                self.store,
                run["run_id"],
                {
                    "stage": stage,
                    "status": "pass",
                    "producer": "test",
                    "observed_result": f"{stage} ready",
                },
            )

        approved = design_harness.approve_run(
            self.store,
            run["run_id"],
            scope="page:P01",
            actor="human",
        )

        trace = design_harness.trace_run_path(
            self.store,
            self.run["run_id"],
            "/state",
        )
        approved_rows = [
            row for row in trace["changes"] if row["value"] == "APPROVED"
        ]

        self.assertEqual(len(approved_rows), 1)
        self.assertEqual(approved_rows[0]["revision"], approved["revision"])
        self.assertEqual(approved_rows[0]["cause"], "approved")

    def test_trace_path_records_missing_to_present_transition(self):
        run = design_harness.load_run(self.store, self.run["run_id"])
        run["correction"] = {
            "reason": "fix shell",
            "resume_from": "CONTINUITY_READY",
        }
        design_harness.save_run(self.store, run)

        trace = design_harness.trace_run_path(
            self.store,
            self.run["run_id"],
            "/correction/reason",
        )

        self.assertEqual(len(trace["changes"]), 2)
        self.assertFalse(trace["changes"][0]["exists"])
        self.assertTrue(trace["changes"][1]["exists"])
        self.assertEqual(trace["changes"][1]["value"], "fix shell")

    def test_audit_requires_valid_journal(self):
        path = design_harness.run_journal_path(
            self.store, self.run["run_id"]
        )
        events = path.read_text(encoding="utf-8").splitlines()
        events[0] = events[0].replace('"product_id":"demo"', '"product_id":"tampered"')
        path.write_text("\n".join(events) + "\n", encoding="utf-8")

        with self.assertRaises(design_harness.JournalIntegrityError):
            design_harness.run_audit_timeline(
                self.store, self.run["run_id"]
            )


if __name__ == "__main__":
    unittest.main()
