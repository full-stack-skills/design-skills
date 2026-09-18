import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "design_harness.py"
spec = importlib.util.spec_from_file_location("design_harness_provenance", MODULE_PATH)
design_harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design_harness)


class DesignHarnessEntityProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Path(self.tmp.name)
        self.run = design_harness.start_run(
            store=self.store,
            run_id="provenance_run",
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

    def baseline_evidence(self):
        run = design_harness.resume_run(
            self.store,
            self.run["run_id"],
            {
                "stage": "baseline",
                "status": "pass",
                "producer": "product-design",
                "observed_result": "baseline ready",
            },
        )
        return run, run["evidence"][-1]["evidence_id"]

    def test_entity_index_tracks_stable_ids_and_revision_span(self):
        run, evidence_id = self.baseline_evidence()
        design_harness.record_artifact(
            self.store,
            run["run_id"],
            {
                "artifact_id": "artifact-1",
                "type": "render",
                "producer": "renderer",
                "maturity": "candidate",
                "status": "valid",
                "location": "renders/p01.png",
                "evidence_ids": [evidence_id],
            },
        )

        index = design_harness.entity_audit_index(
            self.store, run["run_id"]
        )

        evidence = next(
            item for item in index["evidence"]
            if item["entity_id"] == evidence_id
        )
        artifact = next(
            item for item in index["artifact"]
            if item["entity_id"] == "artifact-1"
        )

        self.assertEqual(evidence["first_revision"], 2)
        self.assertGreaterEqual(evidence["last_revision"], 2)
        self.assertEqual(evidence["latest"]["validity"], "valid")
        self.assertEqual(artifact["latest"]["status"], "valid")
        self.assertEqual(artifact["latest"]["maturity"], "candidate")

    def test_evidence_history_explains_invalidation_revision(self):
        run, evidence_id = self.baseline_evidence()

        corrected = design_harness.correct_run(
            self.store,
            run["run_id"],
            affected_state="BASELINE_BOUND",
            reason="baseline contract changed",
        )
        invalidation_id = corrected["invalidations"][-1]["invalidation_id"]

        history = design_harness.entity_history(
            self.store,
            run["run_id"],
            "evidence",
            evidence_id,
        )

        self.assertEqual(history["entity_type"], "evidence")
        self.assertEqual(history["entity_id"], evidence_id)
        self.assertEqual(history["changes"][0]["kind"], "created")
        invalidated = [
            row for row in history["changes"]
            if row["entity"].get("validity") == "invalidated"
        ]
        self.assertEqual(len(invalidated), 1)
        self.assertEqual(
            invalidated[0]["cause"],
            "correction_started",
        )
        self.assertIn(
            invalidation_id,
            invalidated[0]["related_invalidation_ids"],
        )

    def test_artifact_history_tracks_valid_to_invalidated(self):
        run, evidence_id = self.baseline_evidence()
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
                "evidence_ids": [evidence_id],
            },
        )
        design_harness.correct_run(
            self.store,
            run["run_id"],
            affected_state="CONTINUITY_READY",
            reason="regenerate candidate",
            affected_artifact_ids=["artifact-1"],
        )

        history = design_harness.entity_history(
            self.store,
            run["run_id"],
            "artifact",
            "artifact-1",
        )

        self.assertEqual(
            [row["entity"]["status"] for row in history["changes"]],
            ["valid", "invalidated"],
        )

    def test_dispatch_history_tracks_worker_handoffs_and_completion(self):
        dispatch = design_harness.issue_dispatch(
            self.store, self.run["run_id"]
        )
        design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            dispatch["dispatch_id"],
            worker_id="worker-a",
            lease_seconds=60,
        )
        design_harness.release_dispatch(
            self.store,
            self.run["run_id"],
            dispatch["dispatch_id"],
            worker_id="worker-a",
            reason="handoff",
        )
        design_harness.claim_dispatch(
            self.store,
            self.run["run_id"],
            dispatch["dispatch_id"],
            worker_id="worker-b",
            lease_seconds=60,
        )
        design_harness.complete_dispatch(
            self.store,
            self.run["run_id"],
            dispatch["dispatch_id"],
            {
                "stage": "baseline",
                "status": "pass",
                "producer": "product-design",
                "observed_result": "baseline ready",
            },
            worker_id="worker-b",
        )

        history = design_harness.entity_history(
            self.store,
            self.run["run_id"],
            "dispatch",
            dispatch["dispatch_id"],
        )

        statuses = [row["entity"]["status"] for row in history["changes"]]
        self.assertEqual(
            statuses,
            ["issued", "claimed", "issued", "claimed", "completed"],
        )
        self.assertEqual(
            history["changes"][-1]["entity"]["evidence_id"],
            design_harness.load_run(
                self.store, self.run["run_id"]
            )["evidence"][-1]["evidence_id"],
        )

    def test_decision_history_uses_stable_decision_id(self):
        run = design_harness.load_run(self.store, self.run["run_id"])
        run["state"] = "AWAITING_USER_APPROVAL"
        design_harness.save_run(self.store, run)
        approved = design_harness.approve_run(
            self.store,
            run["run_id"],
            scope="page:P01",
            actor="human",
        )
        decision_id = approved["decisions"][-1]["decision_id"]

        history = design_harness.entity_history(
            self.store,
            run["run_id"],
            "decision",
            decision_id,
        )

        self.assertEqual(len(history["changes"]), 1)
        self.assertEqual(history["changes"][0]["kind"], "created")
        self.assertEqual(history["latest"]["kind"], "approval")
        self.assertEqual(history["latest"]["actor"], "human")

    def test_unknown_entity_type_and_id_are_rejected(self):
        with self.assertRaises(design_harness.ValidationError):
            design_harness.entity_history(
                self.store,
                self.run["run_id"],
                "made-up",
                "x",
            )

        with self.assertRaises(design_harness.EntityNotFoundError):
            design_harness.entity_history(
                self.store,
                self.run["run_id"],
                "evidence",
                "missing",
            )

    def test_provenance_graph_links_dispatch_evidence_and_artifact(self):
        run = design_harness.record_artifact(
            self.store,
            self.run["run_id"],
            {
                "artifact_id": "artifact-1",
                "type": "render",
                "producer": "renderer",
                "maturity": "candidate",
                "status": "valid",
                "location": "renders/p01.png",
                "evidence_ids": [],
            },
        )
        dispatch = design_harness.issue_dispatch(
            self.store, run["run_id"]
        )
        completed = design_harness.complete_dispatch(
            self.store,
            run["run_id"],
            dispatch["dispatch_id"],
            {
                "stage": "baseline",
                "status": "pass",
                "producer": "product-design",
                "observed_result": "baseline ready",
                "artifact_ids": ["artifact-1"],
            },
        )
        evidence_id = completed["evidence"][-1]["evidence_id"]

        graph = design_harness.entity_provenance_graph(
            self.store,
            run["run_id"],
            "dispatch",
            dispatch["dispatch_id"],
            max_depth=2,
        )

        node_keys = {
            (node["entity_type"], node["entity_id"])
            for node in graph["nodes"]
        }
        edge_keys = {
            (
                edge["source_type"],
                edge["source_id"],
                edge["relation"],
                edge["target_type"],
                edge["target_id"],
            )
            for edge in graph["edges"]
        }

        self.assertIn(("dispatch", dispatch["dispatch_id"]), node_keys)
        self.assertIn(("evidence", evidence_id), node_keys)
        self.assertIn(("artifact", "artifact-1"), node_keys)
        self.assertIn(
            (
                "dispatch",
                dispatch["dispatch_id"],
                "produced-evidence",
                "evidence",
                evidence_id,
            ),
            edge_keys,
        )
        self.assertIn(
            (
                "evidence",
                evidence_id,
                "mentions-artifact",
                "artifact",
                "artifact-1",
            ),
            edge_keys,
        )

    def test_provenance_graph_links_invalidation_to_invalidated_entities(self):
        run, evidence_id = self.baseline_evidence()
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
                "evidence_ids": [evidence_id],
            },
        )
        corrected = design_harness.correct_run(
            self.store,
            run["run_id"],
            affected_state="BASELINE_BOUND",
            reason="invalidate old baseline",
            affected_artifact_ids=["artifact-1"],
        )
        invalidation_id = corrected["invalidations"][-1]["invalidation_id"]

        graph = design_harness.entity_provenance_graph(
            self.store,
            run["run_id"],
            "evidence",
            evidence_id,
            max_depth=1,
        )

        node_keys = {
            (node["entity_type"], node["entity_id"])
            for node in graph["nodes"]
        }
        edge_keys = {
            (
                edge["source_type"],
                edge["source_id"],
                edge["relation"],
                edge["target_type"],
                edge["target_id"],
            )
            for edge in graph["edges"]
        }

        self.assertIn(("invalidation", invalidation_id), node_keys)
        self.assertIn(
            (
                "invalidation",
                invalidation_id,
                "invalidated-evidence",
                "evidence",
                evidence_id,
            ),
            edge_keys,
        )

    def test_entity_history_requires_valid_journal(self):
        run, evidence_id = self.baseline_evidence()
        path = design_harness.run_journal_path(
            self.store, run["run_id"]
        )
        lines = path.read_text(encoding="utf-8").splitlines()
        lines[-1] = lines[-1].replace('"validity":"valid"', '"validity":"tampered"')
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        with self.assertRaises(design_harness.JournalIntegrityError):
            design_harness.entity_history(
                self.store,
                run["run_id"],
                "evidence",
                evidence_id,
            )


if __name__ == "__main__":
    unittest.main()
