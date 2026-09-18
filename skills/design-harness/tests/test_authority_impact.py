import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "design_harness.py"
spec = importlib.util.spec_from_file_location("design_harness_impact", MODULE_PATH)
design_harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design_harness)


class DesignHarnessAuthorityImpactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def make_run(self, run_id, scope_id, baseline="shell@v2", profile="product-to-ui"):
        authorities = {"baseline": baseline}
        if profile == "existing-product-next-page":
            authorities.update(
                {
                    "feature_contract": "feature@v1",
                    "navigation_contract": "navigation@v1",
                }
            )
        return design_harness.start_run(
            store=self.store,
            run_id=run_id,
            product_id="demo",
            product_version="v1",
            surface="desktop-web",
            scope_type="page",
            scope_ids=[scope_id],
            authorities=authorities,
            profile_id=profile,
        )

    def test_authority_impact_finds_matching_active_runs(self):
        self.make_run("run_a", "P01", "shell@v2")
        self.make_run(
            "run_b",
            "P02",
            "shell@v2",
            profile="existing-product-next-page",
        )
        self.make_run("run_c", "P03", "shell@v9")

        result = design_harness.authority_impact_analysis(
            self.store,
            authority_key="baseline",
            authority_value="shell@v2",
        )

        self.assertTrue(result["complete"])
        self.assertEqual(
            {item["run_id"] for item in result["affected_runs"]},
            {"run_a", "run_b"},
        )
        self.assertEqual(result["diagnostics"], [])

    def test_authority_impact_collects_entity_dependencies(self):
        run = self.make_run("run_a", "P01", "shell@v2")
        run = design_harness.resume_run(
            self.store,
            run["run_id"],
            {
                "stage": "baseline",
                "status": "pass",
                "producer": "product-design",
                "observed_result": "baseline ready",
                "input_versions": {"baseline": "shell@v2"},
            },
        )
        evidence_id = run["evidence"][-1]["evidence_id"]
        run = design_harness.record_artifact(
            self.store,
            run["run_id"],
            {
                "artifact_id": "artifact-1",
                "type": "render",
                "producer": "renderer",
                "maturity": "candidate",
                "status": "valid",
                "location": "renders/p01.png",
                "input_versions": {"baseline": "shell@v2"},
                "evidence_ids": [evidence_id],
            },
        )
        dispatch = design_harness.issue_dispatch(
            self.store, run["run_id"]
        )

        result = design_harness.authority_impact_analysis(
            self.store,
            authority_key="baseline",
            authority_value="shell@v2",
        )
        impact = result["affected_runs"][0]

        self.assertIn("/authorities/baseline", impact["binding_paths"])
        self.assertEqual(
            impact["affected_entities"]["evidence"],
            [evidence_id],
        )
        self.assertEqual(
            impact["affected_entities"]["artifact"],
            ["artifact-1"],
        )
        self.assertEqual(
            impact["affected_entities"]["dispatch"],
            [dispatch["dispatch_id"]],
        )

    def test_terminal_runs_are_excluded_by_default(self):
        run = self.make_run("archived", "P01", "shell@v2")
        run["state"] = "ARCHIVED"
        run["archived_at"] = design_harness.utc_now()
        design_harness.save_run(self.store, run)
        self.make_run("active", "P02", "shell@v2")

        default = design_harness.authority_impact_analysis(
            self.store,
            authority_key="baseline",
            authority_value="shell@v2",
        )
        included = design_harness.authority_impact_analysis(
            self.store,
            authority_key="baseline",
            authority_value="shell@v2",
            include_terminal=True,
        )

        self.assertEqual(
            [item["run_id"] for item in default["affected_runs"]],
            ["active"],
        )
        self.assertEqual(
            {item["run_id"] for item in included["affected_runs"]},
            {"active", "archived"},
        )

    def test_corrupt_journal_marks_analysis_incomplete(self):
        self.make_run("good", "P01", "shell@v2")
        self.make_run("broken", "P02", "shell@v2")

        path = design_harness.run_journal_path(self.store, "broken")
        events = path.read_text(encoding="utf-8").splitlines()
        event = json.loads(events[0])
        event["snapshot"]["authorities"]["baseline"] = "tampered"
        path.write_text(
            json.dumps(event, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        result = design_harness.authority_impact_analysis(
            self.store,
            authority_key="baseline",
            authority_value="shell@v2",
        )

        self.assertFalse(result["complete"])
        self.assertEqual(
            [item["run_id"] for item in result["affected_runs"]],
            ["good"],
        )
        self.assertEqual(result["diagnostics"][0]["run_id"], "broken")
        self.assertEqual(
            result["diagnostics"][0]["error"],
            "JournalIntegrityError",
        )

    def test_plan_baseline_change_recommends_continuity_revalidation(self):
        run = self.make_run("run_a", "P01", "shell@v2")

        before_revision = design_harness.load_run(
            self.store, run["run_id"]
        )["revision"]
        plan = design_harness.plan_authority_change(
            self.store,
            authority_key="baseline",
            from_value="shell@v2",
            to_value="shell@v3",
        )
        after_revision = design_harness.load_run(
            self.store, run["run_id"]
        )["revision"]

        self.assertEqual(before_revision, after_revision)
        self.assertTrue(plan["complete"])
        self.assertFalse(plan["applied"])
        self.assertEqual(plan["authority_key"], "baseline")
        self.assertEqual(plan["from_value"], "shell@v2")
        self.assertEqual(plan["to_value"], "shell@v3")
        self.assertEqual(
            plan["run_impacts"][0]["recommended_affected_state"],
            "CONTINUITY_READY",
        )
        self.assertTrue(plan["plan_id"].startswith("impact_"))

    def test_batch_parent_baseline_change_recommends_rebinding_parent(self):
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

        plan = design_harness.plan_authority_change(
            self.store,
            authority_key="baseline",
            from_value="shell@v2",
            to_value="shell@v3",
        )
        impact = next(
            item for item in plan["run_impacts"]
            if item["run_id"] == parent["run_id"]
        )

        self.assertEqual(
            impact["recommended_affected_state"],
            "BASELINE_BOUND",
        )

    def test_navigation_change_recommends_navigation_revalidation(self):
        self.make_run(
            "run_nav",
            "P01",
            "shell@v2",
            profile="existing-product-next-page",
        )

        plan = design_harness.plan_authority_change(
            self.store,
            authority_key="navigation_contract",
            from_value="navigation@v1",
            to_value="navigation@v2",
        )

        self.assertEqual(
            plan["run_impacts"][0]["recommended_affected_state"],
            "NAVIGATION_READY",
        )

    def test_plan_id_is_deterministic_for_same_store_state(self):
        self.make_run("run_a", "P01", "shell@v2")

        first = design_harness.plan_authority_change(
            self.store,
            authority_key="baseline",
            from_value="shell@v2",
            to_value="shell@v3",
        )
        second = design_harness.plan_authority_change(
            self.store,
            authority_key="baseline",
            from_value="shell@v2",
            to_value="shell@v3",
        )

        self.assertEqual(first["plan_id"], second["plan_id"])

    def test_no_matching_authority_returns_empty_complete_plan(self):
        self.make_run("run_a", "P01", "shell@v2")

        plan = design_harness.plan_authority_change(
            self.store,
            authority_key="baseline",
            from_value="shell@missing",
            to_value="shell@new",
        )

        self.assertTrue(plan["complete"])
        self.assertEqual(plan["run_impacts"], [])
        self.assertEqual(plan["affected_run_count"], 0)


if __name__ == "__main__":
    unittest.main()
