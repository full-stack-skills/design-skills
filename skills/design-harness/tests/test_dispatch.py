import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "design_harness.py"
spec = importlib.util.spec_from_file_location("design_harness_dispatch", MODULE_PATH)
design_harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design_harness)


class DesignHarnessDispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def start_product_run(self):
        return design_harness.start_run(
            store=self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            authorities={},
            profile_id="product-to-ui",
        )

    def evidence(self, stage, status="pass", producer="worker"):
        return {
            "stage": stage,
            "status": status,
            "producer": producer,
            "observed_result": f"{stage}:{status}",
            "artifact_ids": [],
            "input_versions": {},
            "limitations": [],
        }

    def test_next_action_is_derived_from_profile_stage(self):
        run = self.start_product_run()

        action = design_harness.get_next_action(self.store, run["run_id"])

        self.assertEqual(action["kind"], "dispatch")
        self.assertEqual(action["handler"], "product-design")
        self.assertEqual(action["evidence_stage"], "baseline")
        self.assertEqual(action["target_state"], "BASELINE_BOUND")
        self.assertEqual(action["scope"], "page:P01")
        self.assertIn("authorities", action["inputs"])

    def test_issue_dispatch_is_idempotent_while_outstanding(self):
        run = self.start_product_run()

        first = design_harness.issue_dispatch(self.store, run["run_id"])
        second = design_harness.issue_dispatch(self.store, run["run_id"])

        self.assertEqual(first["dispatch_id"], second["dispatch_id"])
        persisted = design_harness.load_run(self.store, run["run_id"])
        self.assertEqual(len(persisted["dispatches"]), 1)
        self.assertEqual(persisted["active_dispatch_id"], first["dispatch_id"])

    def test_next_action_reports_active_dispatch_instead_of_new_dispatch(self):
        run = self.start_product_run()
        dispatch = design_harness.issue_dispatch(self.store, run["run_id"])

        action = design_harness.get_next_action(self.store, run["run_id"])

        self.assertEqual(action["kind"], "inflight")
        self.assertEqual(action["operation"], "complete-dispatch")
        self.assertEqual(action["dispatch_id"], dispatch["dispatch_id"])
        self.assertEqual(action["handler"], "product-design")
        self.assertEqual(action["evidence_stage"], "baseline")

    def test_complete_dispatch_rejects_wrong_dispatch_id(self):
        run = self.start_product_run()
        dispatch = design_harness.issue_dispatch(self.store, run["run_id"])

        with self.assertRaises(design_harness.TransitionError):
            design_harness.complete_dispatch(
                self.store,
                run["run_id"],
                "dispatch_wrong",
                self.evidence("baseline"),
            )

        current = design_harness.load_run(self.store, run["run_id"])
        self.assertEqual(current["state"], "INIT")
        self.assertEqual(current["active_dispatch_id"], dispatch["dispatch_id"])

    def test_complete_dispatch_rejects_evidence_for_wrong_stage(self):
        run = self.start_product_run()
        dispatch = design_harness.issue_dispatch(self.store, run["run_id"])

        with self.assertRaises(design_harness.TransitionError):
            design_harness.complete_dispatch(
                self.store,
                run["run_id"],
                dispatch["dispatch_id"],
                self.evidence("navigation"),
            )

    def test_complete_dispatch_pass_advances_and_closes_dispatch(self):
        run = self.start_product_run()
        dispatch = design_harness.issue_dispatch(self.store, run["run_id"])

        advanced = design_harness.complete_dispatch(
            self.store,
            run["run_id"],
            dispatch["dispatch_id"],
            self.evidence("baseline", producer="product-design"),
        )

        self.assertEqual(advanced["state"], "BASELINE_BOUND")
        self.assertIsNone(advanced["active_dispatch_id"])
        self.assertEqual(advanced["dispatches"][-1]["status"], "completed")
        self.assertEqual(advanced["dispatches"][-1]["evidence_id"], advanced["evidence"][-1]["evidence_id"])

        next_action = design_harness.get_next_action(self.store, run["run_id"])
        self.assertEqual(next_action["handler"], "feature-design")
        self.assertEqual(next_action["evidence_stage"], "behavior")

    def test_complete_dispatch_unknown_enters_reconciling_and_records_receipt(self):
        run = self.start_product_run()
        dispatch = design_harness.issue_dispatch(self.store, run["run_id"])

        current = design_harness.complete_dispatch(
            self.store,
            run["run_id"],
            dispatch["dispatch_id"],
            self.evidence("baseline", status="unknown", producer="provider"),
        )

        self.assertEqual(current["state"], "RECONCILING")
        self.assertIsNone(current["active_dispatch_id"])
        self.assertEqual(current["dispatches"][-1]["status"], "unknown")

        next_action = design_harness.get_next_action(self.store, run["run_id"])
        self.assertEqual(next_action["kind"], "control")
        self.assertEqual(next_action["operation"], "reconcile")
        self.assertEqual(next_action["handler"], "design-harness")

    def test_waiting_approval_next_action_is_human_gate_not_skill_dispatch(self):
        run = self.start_product_run()
        run["state"] = "AWAITING_USER_APPROVAL"
        run["stage_cursor"] = len(run["stage_plan"])
        design_harness.save_run(self.store, run)

        action = design_harness.get_next_action(self.store, run["run_id"])

        self.assertEqual(action["kind"], "human")
        self.assertEqual(action["operation"], "approve")
        self.assertEqual(action["scope"], "page:P01")

        with self.assertRaises(design_harness.TransitionError):
            design_harness.issue_dispatch(self.store, run["run_id"])

    def test_approved_next_action_requests_delivery_verification(self):
        run = self.start_product_run()
        run["state"] = "APPROVED"
        run["stage_cursor"] = len(run["stage_plan"])
        design_harness.save_run(self.store, run)

        action = design_harness.get_next_action(self.store, run["run_id"])

        self.assertEqual(action["kind"], "verification")
        self.assertEqual(action["operation"], "verify")
        self.assertEqual(action["evidence_stage"], "delivery")

    def test_batch_parent_next_action_spawns_children_after_baseline(self):
        parent = design_harness.start_run(
            store=self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page-family",
            scope_ids=["family"],
            authorities={
                "feature_contract": "feature@v3",
                "navigation_contract": "navigation@v5",
                "baseline": "shell@v2",
            },
            profile_id="page-family-batch",
        )
        parent = design_harness.resume_run(
            self.store,
            parent["run_id"],
            self.evidence("baseline", producer="product-design"),
        )

        action = design_harness.get_next_action(self.store, parent["run_id"])

        self.assertEqual(action["kind"], "control")
        self.assertEqual(action["operation"], "spawn-children")
        self.assertEqual(action["shared_baseline"], "shell@v2")

    def test_dispatch_packet_contains_stable_input_and_evidence_contract(self):
        run = self.start_product_run()

        dispatch = design_harness.issue_dispatch(self.store, run["run_id"])

        self.assertEqual(dispatch["contract_version"], 1)
        self.assertEqual(dispatch["run_id"], run["run_id"])
        self.assertEqual(dispatch["profile"]["id"], "product-to-ui")
        self.assertEqual(dispatch["profile"]["version"], 1)
        self.assertEqual(dispatch["expected_evidence"]["stage"], "baseline")
        self.assertEqual(
            set(dispatch["expected_evidence"]["allowed_statuses"]),
            {"pass", "fail", "unknown", "needs-decision"},
        )
        self.assertIn("stop_conditions", dispatch)
        self.assertIn("authority_versions", dispatch["inputs"])


if __name__ == "__main__":
    unittest.main()
