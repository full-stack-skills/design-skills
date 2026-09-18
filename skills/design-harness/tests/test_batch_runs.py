import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "design_harness.py"
spec = importlib.util.spec_from_file_location("design_harness_batch", MODULE_PATH)
design_harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design_harness)


class DesignHarnessBatchRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def start_parent(self):
        parent = design_harness.start_run(
            store=self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page-family",
            scope_ids=["project-pages"],
            authorities={
                "feature_contract": "feature@v3",
                "navigation_contract": "navigation@v5",
                "baseline": "shell@v2",
            },
            profile_id="page-family-batch",
        )
        return design_harness.resume_run(
            self.store,
            parent["run_id"],
            {
                "stage": "baseline",
                "status": "pass",
                "producer": "product-design",
                "observed_result": "shared baseline bound",
            },
        )

    def test_spawn_children_creates_page_runs_with_shared_baseline(self):
        parent = self.start_parent()

        updated = design_harness.spawn_child_runs(
            self.store,
            parent["run_id"],
            ["P01", "P02", "P03"],
        )

        self.assertEqual(len(updated["children"]), 3)
        self.assertEqual(updated["shared_baseline"], "shell@v2")

        for entry in updated["children"]:
            child = design_harness.load_run(self.store, entry["run_id"])
            self.assertEqual(child["parent_run_id"], parent["run_id"])
            self.assertEqual(child["scope_type"], "page")
            self.assertEqual(child["authorities"]["baseline"], "shell@v2")
            self.assertEqual(child["profile"]["id"], "existing-product-next-page")
            self.assertEqual(child["state"], "BASELINE_BOUND")
            self.assertEqual(child["stage_cursor"], 1)

    def test_spawn_children_rejects_non_batch_parent(self):
        parent = design_harness.start_run(
            store=self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            authorities={},
            profile_id="product-to-ui",
        )

        with self.assertRaises(design_harness.TransitionError):
            design_harness.spawn_child_runs(self.store, parent["run_id"], ["P02"])

    def test_spawn_children_rejects_duplicate_scope(self):
        parent = self.start_parent()
        design_harness.spawn_child_runs(self.store, parent["run_id"], ["P01"])

        with self.assertRaises(design_harness.ValidationError):
            design_harness.spawn_child_runs(self.store, parent["run_id"], ["P01"])

    def test_child_cannot_override_shared_baseline(self):
        parent = self.start_parent()

        with self.assertRaises(design_harness.ValidationError):
            design_harness.spawn_child_runs(
                self.store,
                parent["run_id"],
                ["P01"],
                authority_overrides={"baseline": "shell@v999"},
            )

    def test_batch_status_aggregates_children_and_blockers(self):
        parent = self.start_parent()
        parent = design_harness.spawn_child_runs(
            self.store, parent["run_id"], ["P01", "P02"]
        )
        first, second = parent["children"]

        child1 = design_harness.load_run(self.store, first["run_id"])
        child1["state"] = "AWAITING_USER_APPROVAL"
        design_harness.save_run(self.store, child1)

        child2 = design_harness.load_run(self.store, second["run_id"])
        child2["state"] = "BLOCKED"
        design_harness.save_run(self.store, child2)

        status = design_harness.batch_status(self.store, parent["run_id"])

        self.assertEqual(status["counts"]["AWAITING_USER_APPROVAL"], 1)
        self.assertEqual(status["counts"]["BLOCKED"], 1)
        self.assertEqual(status["overall_state"], "BLOCKED")
        self.assertFalse(status["ready_for_batch_approval"])

    def test_batch_status_ready_when_all_children_await_approval(self):
        parent = self.start_parent()
        parent = design_harness.spawn_child_runs(
            self.store, parent["run_id"], ["P01", "P02"]
        )
        for entry in parent["children"]:
            child = design_harness.load_run(self.store, entry["run_id"])
            child["state"] = "AWAITING_USER_APPROVAL"
            design_harness.save_run(self.store, child)

        status = design_harness.batch_status(self.store, parent["run_id"])

        self.assertEqual(status["overall_state"], "READY_FOR_APPROVAL")
        self.assertTrue(status["ready_for_batch_approval"])

    def test_batch_approve_requires_all_children_ready(self):
        parent = self.start_parent()
        parent = design_harness.spawn_child_runs(
            self.store, parent["run_id"], ["P01", "P02"]
        )
        child = design_harness.load_run(self.store, parent["children"][0]["run_id"])
        child["state"] = "AWAITING_USER_APPROVAL"
        design_harness.save_run(self.store, child)

        with self.assertRaises(design_harness.TransitionError):
            design_harness.batch_approve(
                self.store,
                parent["run_id"],
                actor="human",
            )

    def test_batch_approve_approves_every_child_and_parent(self):
        parent = self.start_parent()
        parent = design_harness.spawn_child_runs(
            self.store, parent["run_id"], ["P01", "P02"]
        )
        for entry in parent["children"]:
            child = design_harness.load_run(self.store, entry["run_id"])
            child["state"] = "AWAITING_USER_APPROVAL"
            design_harness.save_run(self.store, child)

        approved = design_harness.batch_approve(
            self.store,
            parent["run_id"],
            actor="human",
        )

        self.assertEqual(approved["state"], "APPROVED")
        self.assertEqual(approved["decisions"][-1]["kind"], "batch-approval")
        for entry in approved["children"]:
            child = design_harness.load_run(self.store, entry["run_id"])
            self.assertEqual(child["state"], "APPROVED")

    def test_batch_status_reports_verified_when_all_children_verified_or_archived(self):
        parent = self.start_parent()
        parent = design_harness.spawn_child_runs(
            self.store, parent["run_id"], ["P01", "P02"]
        )
        states = ["DELIVERY_VERIFIED", "ARCHIVED"]
        for entry, state in zip(parent["children"], states):
            child = design_harness.load_run(self.store, entry["run_id"])
            child["state"] = state
            design_harness.save_run(self.store, child)

        status = design_harness.batch_status(self.store, parent["run_id"])

        self.assertEqual(status["overall_state"], "DELIVERY_VERIFIED")
        self.assertTrue(status["all_delivery_verified"])


if __name__ == "__main__":
    unittest.main()
