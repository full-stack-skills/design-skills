import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "design_harness.py"
spec = importlib.util.spec_from_file_location("design_harness_discovery", MODULE_PATH)
design_harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design_harness)


class DesignHarnessRunDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def create_run(self, run_id, scope_id="P01", profile="product-to-ui"):
        return design_harness.start_run(
            store=self.store,
            run_id=run_id,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=[scope_id],
            authorities={},
            profile_id=profile,
        )

    def test_list_runs_returns_compact_summaries(self):
        self.create_run("run_a", "P01")
        self.create_run("run_b", "P02")

        rows = design_harness.list_runs(self.store)

        self.assertEqual({row["run_id"] for row in rows}, {"run_a", "run_b"})
        for row in rows:
            self.assertIn("revision", row)
            self.assertIn("state", row)
            self.assertIn("scope", row)
            self.assertIn("profile_id", row)
            self.assertNotIn("evidence", row)

    def test_find_runs_matches_exact_scope_independent_of_scope_id_order(self):
        design_harness.start_run(
            store=self.store,
            run_id="family_a",
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page-family",
            scope_ids=["P02", "P01"],
            authorities={
                "feature_contract": "f@1",
                "navigation_contract": "n@1",
                "baseline": "b@1",
            },
            profile_id="page-family-batch",
        )

        rows = design_harness.find_runs(
            self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page-family",
            scope_ids=["P01", "P02"],
            profile_id="page-family-batch",
        )

        self.assertEqual([row["run_id"] for row in rows], ["family_a"])

    def test_find_active_run_ignores_archived_by_default(self):
        old = self.create_run("old_run", "P01")
        old["state"] = "ARCHIVED"
        old["archived_at"] = design_harness.utc_now()
        design_harness.save_run(self.store, old)

        active = self.create_run("active_run", "P01")

        found = design_harness.find_active_run(
            self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            profile_id="product-to-ui",
        )

        self.assertEqual(found["run_id"], active["run_id"])

    def test_find_active_run_returns_none_when_only_terminal_runs_exist(self):
        run = self.create_run("archived_run", "P01")
        run["state"] = "ARCHIVED"
        run["archived_at"] = design_harness.utc_now()
        design_harness.save_run(self.store, run)

        found = design_harness.find_active_run(
            self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            profile_id="product-to-ui",
        )

        self.assertIsNone(found)

    def test_find_active_run_rejects_ambiguous_active_matches(self):
        self.create_run("run_one", "P01")
        self.create_run("run_two", "P01")

        with self.assertRaises(design_harness.RunAmbiguityError):
            design_harness.find_active_run(
                self.store,
                product_id="demo",
                product_version="v1",
                surface="desktop-web",
                scope_type="page",
                scope_ids=["P01"],
                profile_id="product-to-ui",
            )

    def test_ensure_run_reuses_unique_active_run(self):
        existing = self.create_run("existing_run", "P01")

        result = design_harness.ensure_run(
            store=self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            authorities={},
            profile_id="product-to-ui",
        )

        self.assertFalse(result["created"])
        self.assertEqual(result["run"]["run_id"], existing["run_id"])
        self.assertEqual(len(design_harness.list_runs(self.store)), 1)

    def test_ensure_run_creates_new_when_no_active_run_matches(self):
        result = design_harness.ensure_run(
            store=self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P99"],
            authorities={},
            profile_id="product-to-ui",
            run_id="new_run",
        )

        self.assertTrue(result["created"])
        self.assertEqual(result["run"]["run_id"], "new_run")

    def test_ensure_run_reuses_when_explicit_authorities_match(self):
        existing = design_harness.start_run(
            store=self.store,
            run_id="matching_run",
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            authorities={"baseline": "shell@v2"},
            profile_id="product-to-ui",
        )

        result = design_harness.ensure_run(
            store=self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            authorities={"baseline": "shell@v2"},
            profile_id="product-to-ui",
        )

        self.assertFalse(result["created"])
        self.assertEqual(result["run"]["run_id"], existing["run_id"])

    def test_ensure_run_rejects_authority_drift(self):
        design_harness.start_run(
            store=self.store,
            run_id="authority_run",
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            authorities={
                "feature_contract": "feature@v1",
                "baseline": "shell@v1",
            },
            profile_id="product-to-ui",
        )

        with self.assertRaises(design_harness.RunAuthorityConflictError) as ctx:
            design_harness.ensure_run(
                store=self.store,
                product_id="demo",
                product_version="v1",
                surface="desktop-web",
                scope_type="page",
                scope_ids=["P01"],
                authorities={
                    "feature_contract": "feature@v2",
                    "baseline": "shell@v1",
                },
                profile_id="product-to-ui",
            )

        self.assertIn("feature_contract", str(ctx.exception))

    def test_ensure_run_ignores_unspecified_authorities_when_resuming(self):
        existing = design_harness.start_run(
            store=self.store,
            run_id="authority_resume",
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            authorities={"baseline": "shell@v2"},
            profile_id="product-to-ui",
        )

        result = design_harness.ensure_run(
            store=self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            authorities={},
            profile_id="product-to-ui",
        )

        self.assertFalse(result["created"])
        self.assertEqual(result["run"]["run_id"], existing["run_id"])

    def test_ensure_run_does_not_reuse_different_profile(self):
        self.create_run("ui_run", "P01", "product-to-ui")

        result = design_harness.ensure_run(
            store=self.store,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=["P01"],
            authorities={
                "feature_contract": "f@1",
                "navigation_contract": "n@1",
                "baseline": "b@1",
            },
            profile_id="existing-product-next-page",
            run_id="next_page_run",
        )

        self.assertTrue(result["created"])
        self.assertEqual(result["run"]["run_id"], "next_page_run")

    def test_discovery_skips_corrupt_run_and_reports_diagnostic(self):
        self.create_run("good_run", "P01")
        corrupt = self.store / "runs" / "broken.json"
        corrupt.write_text("{not-json", encoding="utf-8")

        result = design_harness.scan_runs(self.store)

        self.assertEqual([r["run_id"] for r in result["runs"]], ["good_run"])
        self.assertEqual(len(result["diagnostics"]), 1)
        self.assertEqual(result["diagnostics"][0]["file"], "broken.json")


if __name__ == "__main__":
    unittest.main()
