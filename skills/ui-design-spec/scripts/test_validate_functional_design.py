"""完整范例与失败注入；不修改原项目或快照。"""
import json
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest

from validate_functional_design import validate


class FunctionalDesignTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        example = Path(__file__).resolve().parents[3] / 'evals/fixtures/ui-design-spec/agent-browser'
        self.root = Path(self.temp.name) / 'example'
        shutil.copytree(example, self.root)
        self.package = self.root / 'docs/functional-design'
        self.data = json.loads((self.package / 'registry.json').read_text())

    def check(self):
        (self.package / 'registry.json').write_text(json.dumps(self.data))
        return validate(self.package)

    def test_intact_draft(self):
        self.assertEqual(self.check(), [])
        self.assertEqual(self.data['status'], 'Draft')

    def test_complete_task_index_matches_full_example(self):
        surfaces = []
        for page in self.data['pages']:
            ident = page['id']
            for n, view in enumerate(page['views'], 1):
                surfaces.append(view['id'] if isinstance(view, dict) else f'{ident}-{n:02}')
            surfaces.extend(a['id'] for a in page['actions'])
            for key, suffix in [('state_id', 'S01'), ('error_id', 'E01'), ('result_id', 'R01')]:
                surfaces.append(page.get(key, f'{ident}-{suffix}'))
        surfaces.extend(g.get('surface_id', g['id'] + '-01') for g in self.data['globals'])
        (self.package / 'audit-task.md').write_text('## T1\nSynthetic mapping fixture, not a production plan\n')
        data = {'schema_version': 1, 'features': ['F1'], 'surfaces': surfaces,
                'tasks': [{'id': 'T1', 'source': 'audit-task.md', 'marker': '## T1',
                           'feature_ids': ['F1'], 'surface_ids': surfaces, 'depends_on': []}]}
        (self.package / 'task-coverage.json').write_text(json.dumps(data))
        self.assertEqual(validate(self.package, require_task_coverage=True), [])

    def test_new_package_requires_task_index(self):
        errors = validate(self.package, require_task_coverage=True)
        self.assertTrue(any('unreadable task index' in e for e in errors))

    def test_task_scope_must_match_registry(self):
        (self.package / 'task-source.md').write_text('## T1\nBuild page\n')
        data = {'schema_version': 1, 'features': ['F1'], 'surfaces': ['P01-01'],
                'tasks': [{'id': 'T1', 'source': 'task-source.md', 'marker': '## T1',
                           'feature_ids': ['F1'], 'surface_ids': ['P01-01'], 'depends_on': []}]}
        (self.package / 'task-coverage.json').write_text(json.dumps(data))
        errors = validate(self.package, require_task_coverage=True)
        self.assertIn('task coverage surfaces do not match registry', errors)

    def test_snapshot_provenance(self):
        manifest = json.loads((self.root / 'provenance.json').read_text())
        declared = {row['path'] for row in manifest['files']}
        actual = {p.relative_to(self.root).as_posix()
                  for p in (self.root / 'docs').rglob('*') if p.is_file()}
        self.assertEqual(declared, actual)
        for row in manifest['files']:
            self.assertEqual(hashlib.sha256((self.root / row['path']).read_bytes()).hexdigest(),
                             row['sha256'], row['path'])

    def test_missing_page(self):
        (self.package / 'pages/P01.md').unlink()
        self.assertTrue(any('P01.md' in e for e in self.check()))

    def test_bad_target(self):
        self.data['pages'][0]['actions'][0]['target'] = 'MISSING'
        self.assertTrue(any('unknown target' in e for e in self.check()))

    def test_duplicate_page(self):
        self.data['pages'].append(self.data['pages'][0])
        self.assertTrue(any('duplicate' in e for e in self.check()))

    def test_missing_plan(self):
        (self.package / 'MASTER-PLAN.md').unlink()
        self.assertTrue(any('MASTER-PLAN.md' in e for e in self.check()))

    def test_bad_return(self):
        self.data['pages'][0]['actions'][0]['cancel'] = ''
        self.assertTrue(any('cancel' in e for e in self.check()))

    def test_missing_surface_row(self):
        p = self.package / 'SCREEN-REGISTRY.md'
        p.write_text(p.read_text().replace('| P01-01 |', '| REMOVED |'))
        self.assertTrue(any('P01-01' in e for e in self.check()))

    def test_malformed_page(self):
        self.data['pages'][0] = 'bad record'
        self.assertTrue(self.check())

    def test_partial_catalog(self):
        p = self.package / 'FUNCTION-CATALOG.md'
        p.write_text(p.read_text().replace('pages/P01.md', 'pages/P02.md'))
        self.assertTrue(any('catalog' in e for e in self.check()))

    def test_explicit_view_id(self):
        # 允许项目稳定 ID，不能只支持序号生成。
        page = self.data['pages'][0]
        page['views'][0] = {'id': 'P01-01', 'name': '默认首页'}
        self.assertEqual(self.check(), [])

    def test_broken_local_link(self):
        p = self.package / 'README.md'
        p.write_text(p.read_text() + '\n[missing](no-such-file.md)\n')
        self.assertTrue(any('broken link' in e for e in self.check()))

    def test_existing_document_names(self):
        old = self.package / 'MASTER-PLAN.md'
        old.rename(self.package / 'plan.md')
        readme = self.package / 'README.md'
        readme.write_text(readme.read_text().replace('MASTER-PLAN.md', 'plan.md'))
        self.assertEqual(validate(self.package, {'MASTER-PLAN.md': 'plan.md'}), [])

    def test_invalid_mapping(self):
        self.assertTrue(validate(self.package, {'pages': 3}))


if __name__ == '__main__':
    unittest.main()
