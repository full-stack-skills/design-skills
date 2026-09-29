"""任务覆盖索引失败注入；仅操作临时目录。"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from validate_task_coverage import validate


class TaskCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'plan.md').write_text('## T1\nBuild page\n## T2\nRecover failure\n')
        self.data = {'schema_version': 1, 'features': ['F1'], 'surfaces': ['P1', 'P1-E1'],
                     'tasks': [dict(id='T1', source='plan.md', marker='## T1', feature_ids=['F1'],
                                    surface_ids=['P1'], depends_on=[]),
                               dict(id='T2', source='plan.md', marker='## T2', feature_ids=['F1'],
                                    surface_ids=['P1-E1'], depends_on=['T1'])]}

    def check(self):
        p = self.root / 'task-coverage.json'
        p.write_text(json.dumps(self.data))
        before = p.read_bytes()
        result = validate(p)
        self.assertEqual(p.read_bytes(), before)
        return result

    def test_valid(self):
        self.assertEqual(self.check(), [])

    def test_missing_coverage(self):
        self.data['tasks'][1]['surface_ids'] = []
        self.assertTrue(any('uncovered surfaces' in e for e in self.check()))

    def test_unknown_references(self):
        self.data['tasks'][1]['depends_on'] = ['T9']
        self.data['tasks'][1]['feature_ids'] = ['F9']
        errors = self.check()
        self.assertTrue(any('unknown dependency' in e for e in errors))
        self.assertTrue(any('unknown feature' in e for e in errors))

    def test_cycle(self):
        self.data['tasks'][0]['depends_on'] = ['T2']
        self.assertTrue(any('cycle' in e for e in self.check()))

    def test_duplicate_task(self):
        self.data['tasks'].append(copy.deepcopy(self.data['tasks'][0]))
        self.assertTrue(any('duplicate task' in e for e in self.check()))

    def test_missing_source_marker(self):
        self.data['tasks'][0]['marker'] = '## nonexistent'
        self.assertTrue(any('source marker' in e for e in self.check()))

    def test_reject_duplicate_execution_status(self):
        self.data['tasks'][0]['status'] = 'done'
        self.assertTrue(any('execution status' in e for e in self.check()))

    def test_malformed(self):
        self.data['tasks'] = [None, {'id': []}]
        self.assertTrue(self.check())

    def test_duplicate_scope(self):
        self.data['features'].append('F1')
        self.assertTrue(any('duplicate features' in e for e in self.check()))
