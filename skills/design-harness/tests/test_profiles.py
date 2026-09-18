import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "design_harness.py"
spec = importlib.util.spec_from_file_location("design_harness_profiles", MODULE_PATH)
design_harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design_harness)


class DesignHarnessProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_catalog_contains_six_builtin_profiles(self):
        profiles = design_harness.list_profiles()
        ids = {item["id"] for item in profiles}

        self.assertEqual(
            ids,
            {
                "product-to-ui",
                "existing-product-next-page",
                "page-family-batch",
                "design-correction",
                "stitch-high-fidelity-delivery",
                "design-to-implementation",
            },
        )

    def test_load_profile_returns_versioned_stage_plan(self):
        profile = design_harness.load_profile("product-to-ui")

        self.assertEqual(profile["id"], "product-to-ui")
        self.assertEqual(profile["version"], 1)
        self.assertGreaterEqual(len(profile["stages"]), 6)
        self.assertEqual(profile["stages"][0]["evidence_stage"], "baseline")
        self.assertIn("handler", profile["stages"][0])

    def test_unknown_profile_is_rejected(self):
        with self.assertRaises(design_harness.ValidationError):
            design_harness.load_profile("does-not-exist")

    def test_start_run_binds_profile_and_stage_plan(self):
        run = design_harness.start_run(
            store=self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            authorities={},
            profile_id="product-to-ui",
        )

        self.assertEqual(run["profile"]["id"], "product-to-ui")
        self.assertEqual(run["profile"]["version"], 1)
        self.assertEqual(
            run["stage_plan"][0]["evidence_stage"],
            "baseline",
        )

    def test_existing_product_next_page_requires_locked_upstream_authorities(self):
        with self.assertRaises(design_harness.ValidationError):
            design_harness.start_run(
                store=self.store,
                product_id="demo",
                product_version="v1",
                surface="desktop-web",
                scope_type="page",
                scope_ids=["P02"],
                authorities={"baseline": "shell@v2"},
                profile_id="existing-product-next-page",
            )

        run = design_harness.start_run(
            store=self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P02"],
            authorities={
                "feature_contract": "feature@v3",
                "navigation_contract": "navigation@v5",
                "baseline": "shell@v2",
            },
            profile_id="existing-product-next-page",
        )
        self.assertEqual(run["profile"]["id"], "existing-product-next-page")

    def test_profile_can_skip_unneeded_generic_states(self):
        run = design_harness.start_run(
            store=self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P02"],
            authorities={
                "feature_contract": "feature@v3",
                "navigation_contract": "navigation@v5",
                "baseline": "shell@v2",
            },
            profile_id="existing-product-next-page",
        )

        run = design_harness.resume_run(
            self.store,
            run["run_id"],
            {
                "stage": "baseline",
                "status": "pass",
                "producer": "test",
                "observed_result": "baseline bound",
            },
        )
        self.assertEqual(run["state"], "BASELINE_BOUND")

        run = design_harness.resume_run(
            self.store,
            run["run_id"],
            {
                "stage": "task",
                "status": "pass",
                "producer": "product-design",
                "observed_result": "page task ready",
            },
        )
        self.assertEqual(run["state"], "TASK_READY")

    def test_status_exposes_profile_next_stage_and_handler(self):
        run = design_harness.start_run(
            store=self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            authorities={},
            profile_id="product-to-ui",
        )

        status = design_harness.status_run(self.store, run["run_id"])

        self.assertEqual(status["profile_next"]["evidence_stage"], "baseline")
        self.assertEqual(status["profile_next"]["handler"], "product-design")

    def test_design_correction_profile_requires_existing_run(self):
        profile = design_harness.load_profile("design-correction")
        self.assertEqual(profile["entry_mode"], "correction")

        with self.assertRaises(design_harness.ValidationError):
            design_harness.start_run(
                store=self.store,
                product_id="demo",
                product_version="v1",
                surface="desktop-web",
                scope_type="page",
                scope_ids=["P01"],
                authorities={},
                profile_id="design-correction",
            )

    def test_batch_profile_pins_shared_baseline_policy(self):
        profile = design_harness.load_profile("page-family-batch")

        self.assertEqual(profile["parallel_policy"], "shared-baseline")
        self.assertEqual(profile["child_scope"], "page")


if __name__ == "__main__":
    unittest.main()
