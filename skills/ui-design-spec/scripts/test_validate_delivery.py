"""Meaningful acceptance/rejection fixtures; no production or repository mutation."""
import json
from pathlib import Path
import tempfile
import unittest
from validate_delivery import AREAS, FIELDS, FILES, validate


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in FILES:
            (self.root / name).write_text('# Fixture\nInvoice export specification.\n')
        (self.root / '05-task-plan.md').write_text('## T1 Export invoice\nValidate scoped export and error recovery.\n')
        self.data = {'schema_version': 1, 'status': 'ready',
                     'scope': {k: 'Invoice export' for k in 'product users objects in_scope out_of_scope spec_source'.split()},
                     'task_source': '05-task-plan.md'}
        for group, fields in FIELDS.items():
            self.data[group] = [{k: 'Scoped invoice export' for k in fields.split()}]
        for group, ident in [('sources', 'SRC1'), ('features', 'F1'), ('surfaces', 'P1'), ('journeys', 'J1'), ('tasks', 'T1')]:
            self.data[group][0]['id'] = ident
        self.data['sources'][0]['evidence_kind'] = 'spec'
        self.data['features'][0]['source_ids'] = ['SRC1']
        self.data['surfaces'][0].update(kind='page', parent_id=None, feature_ids=['F1'])
        self.data['journeys'][0].update(feature_ids=['F1'], steps=[{
            'surface_id': 'P1', 'action': 'Export invoice', 'transition': 'Ready to exporting',
            'permission': 'Invoice owner', 'success': 'Download receipt', 'failure': 'Retain invoice and retry read'}],
            branches={k: 'Return to invoice with recorded export status' for k in 'failure denial cancel offline conflict interruption recovery'.split()})
        self.data['tasks'][0].update(feature_ids=['F1'], surface_ids=['P1'], depends_on=[], source_marker='## T1 Export invoice')
        self.data['issues'] = []
        self.data['reviews'] = [{'area': a, 'verdict': 'pass', 'evidence': '06-review-report.md | Fixture review observation'} for a in sorted(AREAS)]
    def check(self):
        (self.root / 'delivery.json').write_text(json.dumps(self.data))
        return validate(self.root, True)
    def test_valid_structure(self):
        self.assertEqual(self.check(), [])
    def test_required_document(self):
        (self.root / FILES[0]).unlink()
        self.assertTrue(any('missing' in e for e in self.check()))
    def test_missing_surface_information(self):
        del self.data['surfaces'][0]['layout']
        self.assertTrue(any('layout' in e for e in self.check()))
    def test_unknown_reference(self):
        self.data['journeys'][0]['steps'][0]['surface_id'] = 'P99'
        self.assertTrue(any('unknown step' in e for e in self.check()))
    def test_missing_task_coverage(self):
        self.data['tasks'][0]['surface_ids'] = []
        self.assertTrue(any('surfaces without tasks' in e for e in self.check()))
    def test_cycle(self):
        self.data['tasks'][0]['depends_on'] = ['T1']
        self.assertTrue(any('cycle' in e for e in self.check()))
    def test_canonical_marker(self):
        self.data['tasks'][0]['source_marker'] = 'Missing task'
        self.assertTrue(any('uniquely' in e for e in self.check()))
    def test_blocker(self):
        self.data['issues'] = [{'id':'I1', 'severity':'blocker', 'description':'Navigation conflict', 'impact':'Cannot freeze shell', 'resolution':'open'}]
        self.assertTrue(any('open blocker' in e for e in self.check()))
    def test_pending_review(self):
        self.data['reviews'][0]['verdict'] = 'pending'
        self.assertTrue(any('not passed' in e for e in self.check()))
    def test_duplicate_status(self):
        self.data['tasks'][0]['checked'] = True
        self.assertTrue(any('duplicate execution' in e for e in self.check()))
    def test_duplicate_id(self):
        self.data['tasks'][0]['id'] = 'F1'
        self.assertTrue(any('duplicate ID' in e for e in self.check()))
    def test_parent_cycle(self):
        self.data['surfaces'][0]['parent_id'] = 'P1'
        self.assertTrue(any('surface parents: cycle' in e for e in self.check()))
    def test_missing_exception_branch(self):
        del self.data['journeys'][0]['branches']['recovery']
        self.assertTrue(any('recovery' in e for e in self.check()))
    def test_draft_is_not_complete(self):
        self.data['status'] = 'draft'
        self.assertTrue(any('not ready' in e for e in self.check()))
    def test_review_evidence_missing(self):
        self.data['reviews'][0]['evidence'] = 'missing.md | Reviewed'
        self.assertTrue(any('evidence must resolve' in e for e in self.check()))
    def test_malformed_record(self):
        self.data['surfaces'] = ['not an object']
        self.assertTrue(self.check())


if __name__ == '__main__':
    unittest.main()
