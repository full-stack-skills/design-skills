import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "design_harness.py"
spec = importlib.util.spec_from_file_location("design_harness", MODULE_PATH)
design_harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design_harness)


class DesignHarnessRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def start_run(self):
        return design_harness.start_run(
            store=self.store,
            product_id="demo-product",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            authorities={
                "feature_contract": "feature@v1",
                "navigation_contract": "navigation@v1",
                "baseline": "shell@v2",
            },
        )

    def pass_evidence(self, run_id, stage):
        return design_harness.resume_run(
            self.store,
            run_id,
            {
                "stage": stage,
                "status": "pass",
                "producer": "test",
                "observed_result": f"{stage} ready",
                "artifact_ids": [],
                "input_versions": {},
                "limitations": [],
            },
        )

    def test_start_persists_init_run_with_authority_bindings(self):
        run = self.start_run()

        self.assertEqual(run["state"], "INIT")
        self.assertEqual(run["authorities"]["baseline"], "shell@v2")
        self.assertTrue((self.store / "runs" / f'{run["run_id"]}.json').exists())

    def test_resume_advances_only_one_expected_stage(self):
        run = self.start_run()

        advanced = self.pass_evidence(run["run_id"], "baseline")

        self.assertEqual(advanced["state"], "BASELINE_BOUND")
        self.assertEqual(len(advanced["evidence"]), 1)

        with self.assertRaises(design_harness.TransitionError):
            self.pass_evidence(run["run_id"], "navigation")

    def test_unknown_evidence_enters_reconciling_without_promotion(self):
        run = self.start_run()

        reconciliating = design_harness.resume_run(
            self.store,
            run["run_id"],
            {
                "stage": "baseline",
                "status": "unknown",
                "producer": "provider",
                "observed_result": "timeout after write request",
                "artifact_ids": [],
                "input_versions": {},
                "limitations": ["provider acknowledgement missing"],
            },
        )

        self.assertEqual(reconciliating["state"], "RECONCILING")
        self.assertEqual(reconciliating["reconciliation"]["return_state"], "INIT")

    def test_reconciliation_blocks_after_three_unresolved_attempts(self):
        run = self.start_run()
        design_harness.resume_run(
            self.store,
            run["run_id"],
            {
                "stage": "baseline",
                "status": "unknown",
                "producer": "provider",
                "observed_result": "timeout",
                "artifact_ids": [],
                "input_versions": {},
                "limitations": [],
            },
        )

        for attempt in range(1, 4):
            current = design_harness.reconcile_run(
                self.store,
                run["run_id"],
                resolved=False,
                note=f"probe {attempt} unresolved",
            )

        self.assertEqual(current["state"], "BLOCKED")
        self.assertEqual(current["reconciliation"]["attempts"], 3)

    def test_explicit_approval_is_required_for_named_scope(self):
        run = self.start_run()
        run["state"] = "AWAITING_USER_APPROVAL"
        design_harness.save_run(self.store, run)

        with self.assertRaises(design_harness.TransitionError):
            design_harness.approve_run(self.store, run["run_id"], scope="different-page")

        approved = design_harness.approve_run(
            self.store,
            run["run_id"],
            scope="page:P01",
            expected_scope="page:P01",
            actor="human",
        )

        self.assertEqual(approved["state"], "APPROVED")
        self.assertEqual(approved["decisions"][-1]["kind"], "approval")

    def test_correction_invalidates_only_evidence_at_or_after_affected_stage(self):
        run = self.start_run()
        for stage in [
            "baseline",
            "behavior",
            "navigation",
            "task",
            "continuity",
            "candidate",
            "guard",
        ]:
            run = self.pass_evidence(run["run_id"], stage)

        corrected = design_harness.correct_run(
            self.store,
            run["run_id"],
            affected_state="NAVIGATION_READY",
            reason="Fix navigation hierarchy only",
        )

        self.assertEqual(corrected["state"], "CORRECTION")
        self.assertEqual(corrected["correction"]["resume_from"], "NAVIGATION_READY")

        evidence_by_stage = {item["stage"]: item for item in corrected["evidence"]}
        self.assertEqual(evidence_by_stage["baseline"]["validity"], "valid")
        self.assertEqual(evidence_by_stage["behavior"]["validity"], "valid")
        self.assertEqual(evidence_by_stage["navigation"]["validity"], "invalidated")
        self.assertEqual(evidence_by_stage["candidate"]["validity"], "invalidated")

    def test_archive_requires_delivery_verified_state(self):
        run = self.start_run()

        with self.assertRaises(design_harness.TransitionError):
            design_harness.archive_run(self.store, run["run_id"])

        run["state"] = "DELIVERY_VERIFIED"
        design_harness.save_run(self.store, run)
        archived = design_harness.archive_run(self.store, run["run_id"])

        self.assertEqual(archived["state"], "ARCHIVED")
        self.assertIsNotNone(archived["archived_at"])

    def test_status_returns_persisted_next_action_and_artifact_ledger(self):
        run = self.start_run()
        design_harness.set_next_action(
            self.store,
            run["run_id"],
            {
                "kind": "skill",
                "target": "feature-design",
                "required_inputs": ["feature@v1"],
                "expected_evidence": "behavior",
            },
        )
        design_harness.record_artifact(
            self.store,
            run["run_id"],
            {
                "artifact_id": "artifact-1",
                "type": "spec",
                "producer": "feature-design",
                "input_versions": {"feature_contract": "feature@v1"},
                "maturity": "candidate",
                "status": "valid",
                "location": "docs/feature.md",
                "evidence_ids": [],
            },
        )

        status = design_harness.status_run(self.store, run["run_id"])

        self.assertEqual(status["next_action"]["target"], "feature-design")
        self.assertEqual(status["artifacts"][0]["artifact_id"], "artifact-1")

    def test_record_artifact_rejects_duplicate_artifact_id(self):
        run = self.start_run()
        artifact = {
            "artifact_id": "artifact-1",
            "type": "render",
            "producer": "renderer",
            "input_versions": {"baseline": "shell@v2"},
            "maturity": "candidate",
            "status": "valid",
            "location": "renders/p01.png",
            "evidence_ids": [],
        }
        design_harness.record_artifact(self.store, run["run_id"], artifact)

        with self.assertRaises(design_harness.ValidationError):
            design_harness.record_artifact(self.store, run["run_id"], artifact)


if __name__ == "__main__":
    unittest.main()
