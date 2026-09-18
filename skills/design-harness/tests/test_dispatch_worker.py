import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "design_harness.py"
spec = importlib.util.spec_from_file_location("design_harness_worker", MODULE_PATH)
design_harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design_harness)


class DesignHarnessDispatchWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Path(self.tmp.name)
        self.run = design_harness.start_run(
            store=self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            authorities={},
            profile_id="product-to-ui",
        )
        self.dispatch = design_harness.issue_dispatch(
            self.store, self.run["run_id"]
        )

    def tearDown(self):
        self.tmp.cleanup()

    def evidence(self):
        return {
            "stage": "baseline",
            "status": "pass",
            "producer": "product-design",
            "observed_result": "baseline bound",
        }

    def test_worker_claim_is_persisted_and_idempotent_for_same_worker(self):
        claimed = design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            self.dispatch["dispatch_id"],
            worker_id="worker-a",
        )
        repeated = design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            self.dispatch["dispatch_id"],
            worker_id="worker-a",
        )

        self.assertEqual(claimed["status"], "claimed")
        self.assertEqual(claimed["worker_id"], "worker-a")
        self.assertIsNotNone(claimed["claimed_at"])
        self.assertEqual(repeated["dispatch_id"], claimed["dispatch_id"])
        self.assertEqual(repeated["claimed_at"], claimed["claimed_at"])

    def test_second_worker_cannot_claim_active_dispatch(self):
        design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            self.dispatch["dispatch_id"],
            worker_id="worker-a",
        )

        with self.assertRaises(design_harness.TransitionError):
            design_harness.claim_dispatch(
                self.store,
                self.run["run_id"],
                self.dispatch["dispatch_id"],
                worker_id="worker-b",
            )

    def test_claimed_dispatch_requires_matching_worker_to_complete(self):
        design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            self.dispatch["dispatch_id"],
            worker_id="worker-a",
        )

        with self.assertRaises(design_harness.TransitionError):
            design_harness.complete_dispatch(
                self.store,
                self.run["run_id"],
                self.dispatch["dispatch_id"],
                self.evidence(),
            )

        with self.assertRaises(design_harness.TransitionError):
            design_harness.complete_dispatch(
                self.store,
                self.run["run_id"],
                self.dispatch["dispatch_id"],
                self.evidence(),
                worker_id="worker-b",
            )

        advanced = design_harness.complete_dispatch(
            self.store,
            self.run["run_id"],
            self.dispatch["dispatch_id"],
            self.evidence(),
            worker_id="worker-a",
        )
        self.assertEqual(advanced["state"], "BASELINE_BOUND")

    def test_worker_can_release_then_another_worker_can_claim(self):
        claimed = design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            self.dispatch["dispatch_id"],
            worker_id="worker-a",
        )

        released = design_harness.release_dispatch(
            self.store,
            self.run["run_id"],
            claimed["dispatch_id"],
            worker_id="worker-a",
            reason="worker shutting down",
        )
        self.assertEqual(released["status"], "issued")
        self.assertIsNone(released["worker_id"])
        self.assertIsNone(released["claimed_at"])
        self.assertEqual(len(released["releases"]), 1)

        claimed_b = design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            released["dispatch_id"],
            worker_id="worker-b",
        )
        self.assertEqual(claimed_b["worker_id"], "worker-b")

    def test_release_rejects_wrong_worker(self):
        claimed = design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            self.dispatch["dispatch_id"],
            worker_id="worker-a",
        )

        with self.assertRaises(design_harness.TransitionError):
            design_harness.release_dispatch(
                self.store,
                self.run["run_id"],
                claimed["dispatch_id"],
                worker_id="worker-b",
                reason="steal",
            )

    def test_next_action_reports_claimed_worker(self):
        claimed = design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            self.dispatch["dispatch_id"],
            worker_id="worker-a",
        )

        action = design_harness.get_next_action(
            self.store, self.run["run_id"]
        )

        self.assertEqual(action["kind"], "inflight")
        self.assertEqual(action["dispatch_id"], claimed["dispatch_id"])
        self.assertEqual(action["worker_id"], "worker-a")
        self.assertEqual(action["dispatch_status"], "claimed")


if __name__ == "__main__":
    unittest.main()
