import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "design_harness.py"
spec = importlib.util.spec_from_file_location("design_harness_lease", MODULE_PATH)
design_harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design_harness)


class DesignHarnessDispatchLeaseTests(unittest.TestCase):
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

    def set_expired(self, dispatch_id):
        run = design_harness.load_run(self.store, self.run["run_id"])
        item = next(
            d for d in run["dispatches"] if d["dispatch_id"] == dispatch_id
        )
        item["lease_expires_at"] = "2000-01-01T00:00:00+00:00"
        design_harness.save_run(self.store, run)

    def evidence(self):
        return {
            "stage": "baseline",
            "status": "pass",
            "producer": "product-design",
            "observed_result": "baseline bound",
        }

    def test_claim_creates_worker_lease(self):
        claimed = design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            self.dispatch["dispatch_id"],
            worker_id="worker-a",
            lease_seconds=600,
        )

        self.assertEqual(claimed["status"], "claimed")
        self.assertEqual(claimed["lease_seconds"], 600)
        self.assertIsNotNone(claimed["lease_expires_at"])
        self.assertFalse(design_harness.dispatch_lease_expired(claimed))

    def test_heartbeat_extends_lease_only_for_owner(self):
        claimed = design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            self.dispatch["dispatch_id"],
            worker_id="worker-a",
            lease_seconds=60,
        )
        original_expiry = claimed["lease_expires_at"]

        with self.assertRaises(design_harness.TransitionError):
            design_harness.heartbeat_dispatch(
                self.store,
                self.run["run_id"],
                claimed["dispatch_id"],
                worker_id="worker-b",
                lease_seconds=120,
            )

        renewed = design_harness.heartbeat_dispatch(
            self.store,
            self.run["run_id"],
            claimed["dispatch_id"],
            worker_id="worker-a",
            lease_seconds=120,
        )

        self.assertEqual(renewed["worker_id"], "worker-a")
        self.assertEqual(renewed["lease_seconds"], 120)
        self.assertGreater(renewed["lease_expires_at"], original_expiry)
        self.assertEqual(len(renewed["heartbeats"]), 1)

    def test_unexpired_claim_cannot_be_stolen(self):
        design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            self.dispatch["dispatch_id"],
            worker_id="worker-a",
            lease_seconds=600,
        )

        with self.assertRaises(design_harness.TransitionError):
            design_harness.claim_dispatch(
                self.store,
                self.run["run_id"],
                self.dispatch["dispatch_id"],
                worker_id="worker-b",
                lease_seconds=600,
            )

    def test_expired_claim_can_be_reclaimed_by_another_worker(self):
        claimed = design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            self.dispatch["dispatch_id"],
            worker_id="worker-a",
            lease_seconds=60,
        )
        self.set_expired(claimed["dispatch_id"])

        reclaimed = design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            claimed["dispatch_id"],
            worker_id="worker-b",
            lease_seconds=300,
        )

        self.assertEqual(reclaimed["worker_id"], "worker-b")
        self.assertEqual(reclaimed["status"], "claimed")
        self.assertEqual(reclaimed["releases"][-1]["worker_id"], "worker-a")
        self.assertEqual(
            reclaimed["releases"][-1]["reason"],
            "lease-expired-reclaim",
        )
        self.assertEqual(
            reclaimed["releases"][-1]["reclaimed_by"],
            "worker-b",
        )

    def test_expired_owner_cannot_complete_without_reclaiming(self):
        claimed = design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            self.dispatch["dispatch_id"],
            worker_id="worker-a",
            lease_seconds=60,
        )
        self.set_expired(claimed["dispatch_id"])

        with self.assertRaises(design_harness.TransitionError):
            design_harness.complete_dispatch(
                self.store,
                self.run["run_id"],
                claimed["dispatch_id"],
                self.evidence(),
                worker_id="worker-a",
            )

    def test_next_action_exposes_expired_lease_as_reclaimable(self):
        claimed = design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            self.dispatch["dispatch_id"],
            worker_id="worker-a",
            lease_seconds=60,
        )
        self.set_expired(claimed["dispatch_id"])

        action = design_harness.get_next_action(
            self.store, self.run["run_id"]
        )

        self.assertEqual(action["kind"], "control")
        self.assertEqual(action["operation"], "claim-dispatch")
        self.assertTrue(action["lease_expired"])
        self.assertEqual(action["previous_worker_id"], "worker-a")
        self.assertEqual(action["dispatch_id"], claimed["dispatch_id"])

    def test_release_clears_worker_lease(self):
        claimed = design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            self.dispatch["dispatch_id"],
            worker_id="worker-a",
            lease_seconds=60,
        )

        released = design_harness.release_dispatch(
            self.store,
            self.run["run_id"],
            claimed["dispatch_id"],
            worker_id="worker-a",
            reason="handoff",
        )

        self.assertIsNone(released["lease_expires_at"])
        self.assertIsNone(released["lease_seconds"])


if __name__ == "__main__":
    unittest.main()
