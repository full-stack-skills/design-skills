import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "design_harness.py"
spec = importlib.util.spec_from_file_location("design_harness_changeset", MODULE_PATH)
design_harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design_harness)


class DesignHarnessAuthorityChangeSetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def make_run(self, run_id, scope_id, baseline="shell@v2"):
        run = design_harness.start_run(
            store=self.store,
            run_id=run_id,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=[scope_id],
            authorities={"baseline": baseline},
            profile_id="product-to-ui",
        )
        run = design_harness.resume_run(
            self.store,
            run_id,
            {
                "stage": "baseline",
                "status": "pass",
                "producer": "product-design",
                "observed_result": "baseline ready",
                "input_versions": {"baseline": baseline},
            },
        )
        evidence_id = run["evidence"][-1]["evidence_id"]
        run = design_harness.record_artifact(
            self.store,
            run_id,
            {
                "artifact_id": f"artifact-{scope_id}",
                "type": "render",
                "producer": "renderer",
                "maturity": "candidate",
                "status": "valid",
                "location": f"renders/{scope_id}.png",
                "input_versions": {"baseline": baseline},
                "evidence_ids": [evidence_id],
            },
        )
        return run, evidence_id, f"artifact-{scope_id}"

    def test_prepare_change_set_is_read_only_and_pins_run_revision(self):
        run, evidence_id, artifact_id = self.make_run("run_a", "P01")
        before = design_harness.load_run(self.store, run["run_id"])

        change_set = design_harness.prepare_authority_change_set(
            self.store,
            authority_key="baseline",
            from_value="shell@v2",
            to_value="shell@v3",
        )
        after = design_harness.load_run(self.store, run["run_id"])

        self.assertEqual(change_set["status"], "PREPARED")
        self.assertFalse(change_set["applied"])
        self.assertEqual(before["revision"], after["revision"])
        self.assertEqual(len(change_set["run_changes"]), 1)
        item = change_set["run_changes"][0]
        self.assertEqual(item["run_id"], "run_a")
        self.assertEqual(item["expected_revision"], before["revision"])
        self.assertIn(evidence_id, item["affected_entities"]["evidence"])
        self.assertIn(artifact_id, item["affected_entities"]["artifact"])
        self.assertEqual(item["status"], "PENDING")
        self.assertTrue(
            design_harness.authority_change_set_path(
                self.store, change_set["change_set_id"]
            ).exists()
        )

    def test_prepare_is_idempotent_for_same_plan(self):
        self.make_run("run_a", "P01")

        first = design_harness.prepare_authority_change_set(
            self.store,
            authority_key="baseline",
            from_value="shell@v2",
            to_value="shell@v3",
        )
        second = design_harness.prepare_authority_change_set(
            self.store,
            authority_key="baseline",
            from_value="shell@v2",
            to_value="shell@v3",
        )

        self.assertEqual(first["change_set_id"], second["change_set_id"])
        self.assertEqual(
            len(design_harness.list_authority_change_sets(self.store)),
            1,
        )

    def test_apply_requires_explicit_approval(self):
        self.make_run("run_a", "P01")
        change_set = design_harness.prepare_authority_change_set(
            self.store,
            authority_key="baseline",
            from_value="shell@v2",
            to_value="shell@v3",
        )

        with self.assertRaises(design_harness.TransitionError):
            design_harness.apply_authority_change_set(
                self.store, change_set["change_set_id"]
            )

    def test_approval_does_not_mutate_runs(self):
        run, _, _ = self.make_run("run_a", "P01")
        before = design_harness.load_run(self.store, run["run_id"])

        change_set = design_harness.prepare_authority_change_set(
            self.store,
            authority_key="baseline",
            from_value="shell@v2",
            to_value="shell@v3",
        )
        approved = design_harness.approve_authority_change_set(
            self.store,
            change_set["change_set_id"],
            actor="human",
        )
        after = design_harness.load_run(self.store, run["run_id"])

        self.assertEqual(approved["status"], "APPROVED")
        self.assertEqual(approved["approved_by"], "human")
        self.assertEqual(before["revision"], after["revision"])

    def test_apply_migrates_authority_invalidates_dependencies_and_enters_correction(self):
        run, evidence_id, artifact_id = self.make_run("run_a", "P01")
        change_set = design_harness.prepare_authority_change_set(
            self.store,
            authority_key="baseline",
            from_value="shell@v2",
            to_value="shell@v3",
        )
        design_harness.approve_authority_change_set(
            self.store, change_set["change_set_id"], actor="human"
        )

        applied = design_harness.apply_authority_change_set(
            self.store, change_set["change_set_id"]
        )
        current = design_harness.load_run(self.store, run["run_id"])

        self.assertEqual(applied["status"], "APPLIED")
        self.assertTrue(applied["applied"])
        self.assertEqual(current["authorities"]["baseline"], "shell@v3")
        self.assertEqual(current["state"], "CORRECTION")
        self.assertEqual(
            current["correction"]["resume_from"],
            "CONTINUITY_READY",
        )
        evidence = next(
            item for item in current["evidence"]
            if item["evidence_id"] == evidence_id
        )
        artifact = next(
            item for item in current["artifacts"]
            if item["artifact_id"] == artifact_id
        )
        self.assertEqual(evidence["validity"], "invalidated")
        self.assertEqual(artifact["status"], "invalidated")
        decision = current["decisions"][-1]
        self.assertEqual(decision["kind"], "authority-migration")
        self.assertEqual(
            decision["change_set_id"],
            change_set["change_set_id"],
        )
        self.assertEqual(
            current["invalidations"][-1]["change_set_id"],
            change_set["change_set_id"],
        )

    def test_batch_parent_baseline_migration_updates_shared_baseline(self):
        parent = design_harness.start_run(
            store=self.store,
            run_id="batch_parent",
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page-family",
            scope_ids=["family"],
            authorities={
                "feature_contract": "feature@v1",
                "navigation_contract": "navigation@v1",
                "baseline": "shell@v2",
            },
            profile_id="page-family-batch",
        )
        parent = design_harness.resume_run(
            self.store,
            parent["run_id"],
            {
                "stage": "baseline",
                "status": "pass",
                "producer": "product-design",
                "observed_result": "shared baseline bound",
            },
        )
        parent["shared_baseline"] = "shell@v2"
        design_harness.save_run(self.store, parent)

        change_set = design_harness.prepare_authority_change_set(
            self.store,
            authority_key="baseline",
            from_value="shell@v2",
            to_value="shell@v3",
        )
        design_harness.approve_authority_change_set(
            self.store, change_set["change_set_id"], actor="human"
        )
        design_harness.apply_authority_change_set(
            self.store, change_set["change_set_id"]
        )

        current = design_harness.load_run(
            self.store, parent["run_id"]
        )
        self.assertEqual(current["authorities"]["baseline"], "shell@v3")
        self.assertEqual(current["shared_baseline"], "shell@v3")
        self.assertEqual(
            current["correction"]["resume_from"],
            "BASELINE_BOUND",
        )

    def test_active_affected_dispatch_blocks_without_mutating_run(self):
        run, _, _ = self.make_run("run_a", "P01")
        dispatch = design_harness.issue_dispatch(
            self.store, run["run_id"]
        )
        before = design_harness.load_run(self.store, run["run_id"])

        change_set = design_harness.prepare_authority_change_set(
            self.store,
            authority_key="baseline",
            from_value="shell@v2",
            to_value="shell@v3",
        )
        self.assertIn(
            dispatch["dispatch_id"],
            change_set["run_changes"][0]["affected_entities"]["dispatch"],
        )
        design_harness.approve_authority_change_set(
            self.store, change_set["change_set_id"], actor="human"
        )
        result = design_harness.apply_authority_change_set(
            self.store, change_set["change_set_id"]
        )
        after = design_harness.load_run(self.store, run["run_id"])

        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(
            result["run_changes"][0]["status"],
            "BLOCKED",
        )
        self.assertIn(
            "active affected dispatch",
            result["run_changes"][0]["error"],
        )
        self.assertEqual(before["revision"], after["revision"])
        self.assertEqual(after["authorities"]["baseline"], "shell@v2")

    def test_revision_drift_blocks_without_overwrite(self):
        run, _, _ = self.make_run("run_a", "P01")
        change_set = design_harness.prepare_authority_change_set(
            self.store,
            authority_key="baseline",
            from_value="shell@v2",
            to_value="shell@v3",
        )
        design_harness.approve_authority_change_set(
            self.store, change_set["change_set_id"], actor="human"
        )

        current = design_harness.load_run(self.store, run["run_id"])
        current["next_action"] = {"external": "change"}
        design_harness.save_run(self.store, current)
        drifted = design_harness.load_run(self.store, run["run_id"])

        result = design_harness.apply_authority_change_set(
            self.store, change_set["change_set_id"]
        )
        after = design_harness.load_run(self.store, run["run_id"])

        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn(
            "revision conflict",
            result["run_changes"][0]["error"],
        )
        self.assertEqual(after["revision"], drifted["revision"])
        self.assertEqual(after["authorities"]["baseline"], "shell@v2")

    def test_multi_run_apply_stops_on_conflict_and_records_partial(self):
        self.make_run("a_run", "P01")
        self.make_run("b_run", "P02")
        change_set = design_harness.prepare_authority_change_set(
            self.store,
            authority_key="baseline",
            from_value="shell@v2",
            to_value="shell@v3",
        )
        design_harness.approve_authority_change_set(
            self.store, change_set["change_set_id"], actor="human"
        )

        b = design_harness.load_run(self.store, "b_run")
        b["next_action"] = {"external": "change"}
        design_harness.save_run(self.store, b)

        result = design_harness.apply_authority_change_set(
            self.store, change_set["change_set_id"]
        )

        self.assertEqual(result["status"], "PARTIAL")
        a_change = next(
            item for item in result["run_changes"]
            if item["run_id"] == "a_run"
        )
        b_change = next(
            item for item in result["run_changes"]
            if item["run_id"] == "b_run"
        )
        self.assertEqual(a_change["status"], "APPLIED")
        self.assertEqual(b_change["status"], "BLOCKED")
        self.assertEqual(
            design_harness.load_run(
                self.store, "a_run"
            )["authorities"]["baseline"],
            "shell@v3",
        )
        self.assertEqual(
            design_harness.load_run(
                self.store, "b_run"
            )["authorities"]["baseline"],
            "shell@v2",
        )

    def test_apply_recovers_if_run_commit_succeeded_before_changeset_receipt(self):
        run, _, _ = self.make_run("run_a", "P01")
        change_set = design_harness.prepare_authority_change_set(
            self.store,
            authority_key="baseline",
            from_value="shell@v2",
            to_value="shell@v3",
        )
        approved = design_harness.approve_authority_change_set(
            self.store, change_set["change_set_id"], actor="human"
        )
        item = approved["run_changes"][0]

        migrated = design_harness.migrate_run_authority(
            self.store,
            change_set_id=approved["change_set_id"],
            plan_id=approved["plan_id"],
            actor=approved["approved_by"],
            authority_key=approved["authority_key"],
            from_value=approved["from_value"],
            to_value=approved["to_value"],
            run_change=item,
        )
        self.assertEqual(migrated["authorities"]["baseline"], "shell@v3")

        # Simulate process crash: the run commit exists, but the change-set
        # still says PENDING.
        result = design_harness.apply_authority_change_set(
            self.store, approved["change_set_id"]
        )

        self.assertEqual(result["status"], "APPLIED")
        self.assertEqual(result["run_changes"][0]["status"], "APPLIED")
        decisions = [
            d for d in design_harness.load_run(
                self.store, run["run_id"]
            )["decisions"]
            if d.get("change_set_id") == approved["change_set_id"]
        ]
        self.assertEqual(len(decisions), 1)

    def test_applied_change_set_is_idempotent(self):
        self.make_run("run_a", "P01")
        change_set = design_harness.prepare_authority_change_set(
            self.store,
            authority_key="baseline",
            from_value="shell@v2",
            to_value="shell@v3",
        )
        design_harness.approve_authority_change_set(
            self.store, change_set["change_set_id"], actor="human"
        )
        first = design_harness.apply_authority_change_set(
            self.store, change_set["change_set_id"]
        )
        current_revision = design_harness.load_run(
            self.store, "run_a"
        )["revision"]

        second = design_harness.apply_authority_change_set(
            self.store, change_set["change_set_id"]
        )

        self.assertEqual(first["status"], "APPLIED")
        self.assertEqual(second["status"], "APPLIED")
        self.assertEqual(
            design_harness.load_run(
                self.store, "run_a"
            )["revision"],
            current_revision,
        )


if __name__ == "__main__":
    unittest.main()
