import importlib.util
import json
import os
import tempfile
import time
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "design_harness.py"
spec = importlib.util.spec_from_file_location("design_harness_concurrency", MODULE_PATH)
design_harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design_harness)


class DesignHarnessRunConcurrencyTests(unittest.TestCase):
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

    def tearDown(self):
        self.tmp.cleanup()

    def test_new_run_starts_with_revision_one(self):
        self.assertEqual(self.run["revision"], 1)
        persisted = design_harness.load_run(self.store, self.run["run_id"])
        self.assertEqual(persisted["revision"], 1)

    def test_save_run_uses_compare_and_swap_revision(self):
        first = design_harness.load_run(self.store, self.run["run_id"])
        stale = design_harness.load_run(self.store, self.run["run_id"])

        first["next_action"] = {"writer": "first"}
        saved = design_harness.save_run(self.store, first)

        self.assertEqual(saved["revision"], 2)

        stale["next_action"] = {"writer": "stale"}
        with self.assertRaises(design_harness.RunConflictError):
            design_harness.save_run(self.store, stale)

        persisted = design_harness.load_run(self.store, self.run["run_id"])
        self.assertEqual(persisted["revision"], 2)
        self.assertEqual(persisted["next_action"], {"writer": "first"})

    def test_mutating_api_increments_revision(self):
        before = design_harness.load_run(self.store, self.run["run_id"])
        updated = design_harness.set_next_action(
            self.store,
            self.run["run_id"],
            {
                "kind": "skill",
                "target": "feature-design",
                "expected_evidence": "behavior",
            },
        )

        self.assertEqual(updated["revision"], before["revision"] + 1)

    def test_lock_timeout_does_not_overwrite_run(self):
        snapshot = design_harness.load_run(self.store, self.run["run_id"])
        snapshot["next_action"] = {"writer": "blocked"}

        lock_path = design_harness.run_lock_path(self.store, self.run["run_id"])
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text(
            json.dumps(
                {
                    "pid": os.getpid(),
                    "created_at": design_harness.utc_now(),
                }
            ),
            encoding="utf-8",
        )

        with self.assertRaises(design_harness.RunLockTimeoutError):
            design_harness.save_run(
                self.store,
                snapshot,
                lock_timeout_seconds=0.05,
                lock_stale_seconds=60,
            )

        persisted = design_harness.load_run(self.store, self.run["run_id"])
        self.assertIsNone(persisted["next_action"])

    def test_stale_lock_is_recovered(self):
        snapshot = design_harness.load_run(self.store, self.run["run_id"])
        snapshot["next_action"] = {"writer": "recovered"}

        lock_path = design_harness.run_lock_path(self.store, self.run["run_id"])
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text(
            json.dumps({"pid": 999999, "created_at": "2000-01-01T00:00:00+00:00"}),
            encoding="utf-8",
        )
        old = time.time() - 120
        os.utime(lock_path, (old, old))

        saved = design_harness.save_run(
            self.store,
            snapshot,
            lock_timeout_seconds=0.2,
            lock_stale_seconds=1,
        )

        self.assertEqual(saved["revision"], 2)
        self.assertFalse(lock_path.exists())

    def test_new_run_creation_is_create_only(self):
        with self.assertRaises(design_harness.RunConflictError):
            design_harness.start_run(
                store=self.store,
                product_id="demo",
                product_version="v1",
                surface="desktop-web",
                scope_type="page",
                scope_ids=["P02"],
                authorities={},
                profile_id="product-to-ui",
                run_id=self.run["run_id"],
            )

    def test_lock_is_released_after_validation_error(self):
        snapshot = design_harness.load_run(self.store, self.run["run_id"])
        snapshot["revision"] = -1

        with self.assertRaises(design_harness.RunConflictError):
            design_harness.save_run(self.store, snapshot)

        lock_path = design_harness.run_lock_path(self.store, self.run["run_id"])
        self.assertFalse(lock_path.exists())

    def test_status_exposes_revision(self):
        status = design_harness.status_run(self.store, self.run["run_id"])
        self.assertEqual(status["revision"], 1)


if __name__ == "__main__":
    unittest.main()
