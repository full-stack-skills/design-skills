"""Synthetic relationship fixtures, never production approval evidence."""
import copy
import json
import shutil
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path
from validate_functional_design import validate
from methodology import render_maps


class MethodologyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        fixture = Path(__file__).resolve().parents[3] / 'evals/fixtures/ui-design-spec'
        self.root = Path(self.temp.name) / 'package'
        shutil.copytree(fixture / 'agent-browser/docs/functional-design', self.root)
        shutil.copyfile(fixture / 'agent-browser/docs/product-spec.md', self.root.parent / 'product-spec.md')
        self.data = json.loads((self.root / 'registry.json').read_text())
        self.surfaces = []
        self.actions = []
        for p in self.data['pages']:
            self.surfaces.extend(v['id'] if isinstance(v, dict) else f"{p['id']}-{i:02}"
                                 for i, v in enumerate(p['views'], 1))
            self.actions.extend(p['actions'])
            self.surfaces.extend(a['id'] for a in p['actions'])
            self.surfaces.extend(p.get(k, p['id'] + '-' + suffix) for k, suffix in
                                 [('state_id', 'S01'), ('error_id', 'E01'), ('result_id', 'R01')])
        self.surfaces.extend(g.get('surface_id', g['id'] + '-01') for g in self.data['globals'])
        pages = [p['id'] for p in self.data['pages']]
        self.tasks = {'schema_version': 1, 'features': ['F1'], 'surfaces': self.surfaces,
                      'tasks': [{'id': 'T1', 'source': 'task-source.md', 'marker': '## T1',
                                 'feature_ids': ['F1'], 'surface_ids': self.surfaces, 'depends_on': []}]}
        (self.root / 'task-source.md').write_text('## T1\nSynthetic coverage fixture only.\n', encoding='utf-8')
        self.method = {
            'schema_version': 1,
            'objects': [{'id': 'O1', 'name': 'Execution', 'owner': 'Runtime', 'source': 'README.md'}],
            'features': [{'id': 'F1', 'page_ids': pages, 'object_ids': ['O1'],
                          'upstream_ids': [], 'downstream_ids': [], 'source': 'FUNCTION-CATALOG.md'}],
            'menus': [{'id': 'M1', 'label': 'Workspace', 'parent_id': None, 'page_ids': pages,
                       'default_page_id': pages[0], 'feature_ids': ['F1'], 'object_ids': ['O1']}],
            'page_details': [{'page_id': p, 'menu_id': 'M1', 'actors': ['Operator'],
                              'permissions': ['Read execution'], 'object_ids': ['O1'],
                              'feature_ids': ['F1'], 'core_question': 'What happened?',
                              'layout_archetype': 'execution-detail', 'source': f'pages/{p}.md'} for p in pages],
            'surface_details': [{'surface_id': s, 'kind': 'state', 'parent_surface_id': None,
                                 'source': 'SCREEN-REGISTRY.md'} for s in self.surfaces],
            'transitions': [{'id': 'FLOW-' + a['id'], 'action_id': a['id'], 'kind': 'command',
                             'source': a['source'], 'success': a['target'], 'cancel': a['cancel'],
                             'failure': self.surfaces[0], 'precondition': a['precondition'],
                             'state_change': a['effect'], 'recovery': 'Retry after reconnect; retain input',
                             'permission': 'Operator', 'source_ref': 'USER-FLOWS.md'} for a in self.actions],
            'design_units': [{'id': 'DU1', 'task_id': 'T1', 'surface_ids': self.surfaces,
                              'mode': 'NEW_SCREEN', 'parent_unit_id': None, 'baseline_ref': None,
                              'frozen_regions': ['navigation'], 'allowed_regions': ['content'],
                              'acceptance': ['Review field order and failure recovery'],
                              'outputs': ['assets/unit.png'], 'source': 'task-source.md'}]}
        self.data['methodology'] = self.method

    def check(self):
        (self.root / 'registry.json').write_text(json.dumps(self.data), encoding='utf-8')
        (self.root / 'task-coverage.json').write_text(json.dumps(self.tasks), encoding='utf-8')
        return validate(self.root, require_task_coverage=True)

    def test_valid_extension(self):
        self.assertEqual(self.check(), [])

    def test_generated_projection_is_checked(self):
        (self.root / 'DESIGN-MAP.generated.md').write_text('stale', encoding='utf-8')
        self.assertIn('methodology: stale generated design map', self.check())
        (self.root / 'DESIGN-MAP.generated.md').write_text(render_maps(self.data, self.root, self.tasks), encoding='utf-8')
        self.assertEqual(self.check(), [])

    def test_render_is_order_independent_and_preserves_authority(self):
        before = copy.deepcopy(self.data)
        expected = render_maps(self.data)
        self.assertEqual(before, self.data)
        for field in ('menus', 'page_details', 'surface_details', 'transitions', 'design_units'):
            self.method[field].reverse()
        self.assertEqual(render_maps(self.data), expected)

    def test_strict_mode_requires_relationships(self):
        del self.data['methodology']
        self.check()
        self.assertIn('methodology: expected schema_version 1',
                      validate(self.root, require_methodology=True))

    def test_generate_cli_writes_only_projection_and_checks_staleness(self):
        self.check()
        script = Path(__file__).with_name('generate_design_maps.py')
        before = (self.root / 'registry.json').read_bytes()
        def run(*args):
            return subprocess.run([sys.executable, '-X', 'utf8', str(script), str(self.root), *args],
                                  capture_output=True, text=True)
        result = run('--write')
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual((self.root / 'registry.json').read_bytes(), before)
        self.assertEqual(run('--check').returncode, 0)
        authority = self.root / 'USER-FLOWS.md'
        authority.write_text(authority.read_text(encoding='utf-8') + '\nSource change\n', encoding='utf-8')
        self.assertNotEqual(run('--check').returncode, 0)
        self.assertEqual(run('--write').returncode, 0)
        self.method['menus'][0]['label'] = 'New label'
        self.check()
        self.assertNotEqual(run('--check').returncode, 0)
        self.assertEqual(run('--write').returncode, 0)
        self.assertEqual(run('--check').returncode, 0)

    def test_parent_dependency_and_baseline(self):
        first = self.method['design_units'][0]
        first['surface_ids'] = self.surfaces[:1]
        self.tasks['tasks'].append(dict(self.tasks['tasks'][0], id='T2', marker='## T2', depends_on=['T1']))
        (self.root / 'task-source.md').write_text('## T1\nParent\n## T2\nChild\n', encoding='utf-8')
        child = dict(first, id='DU2', task_id='T2', surface_ids=self.surfaces[1:],
                     mode='OVERLAY_PARENT', parent_unit_id='DU1', baseline_ref='asset:parent@v1',
                     outputs=['assets/child.png'])
        self.method['design_units'].append(child)
        self.assertEqual(self.check(), [])
        self.tasks['tasks'][1]['depends_on'] = []
        self.assertTrue(any('parent task dependency' in e for e in self.check()))

    def test_bad_relationships_are_rejected(self):
        mutations = [
            ('menu target', lambda m: m['menus'][0].update(default_page_id='MISSING')),
            ('menu cycle', lambda m: m['menus'][0].update(parent_id='M1')),
            ('missing page', lambda m: m['page_details'].pop()),
            ('unknown object', lambda m: m['features'][0].update(object_ids=['MISSING'])),
            ('failure target', lambda m: m['transitions'][0].update(failure='MISSING')),
            ('action drift', lambda m: m['transitions'][0].update(success=self.surfaces[-1])),
            ('missing recovery', lambda m: m['transitions'][0].update(recovery='')),
            ('missing action', lambda m: m['transitions'].pop()),
            ('missing surface', lambda m: m['surface_details'].pop()),
            ('frozen overlap', lambda m: m['design_units'][0].update(allowed_regions=['navigation'])),
            ('missing baseline', lambda m: m['design_units'][0].update(mode='EDIT_PARENT')),
            ('unknown task', lambda m: m['design_units'][0].update(task_id='MISSING')),
            ('missing acceptance', lambda m: m['design_units'][0].update(acceptance=[])),
            ('duplicate outputs', lambda m: m['design_units'].append(dict(m['design_units'][0], id='DU2'))),
            ('unsafe output', lambda m: m['design_units'][0].update(outputs=['../other.png'])),
            ('malformed section', lambda m: m.update(menus='bad')),
            ('reverse menu drift', lambda m: m['page_details'][0].update(menu_id=None, non_menu_reason='Detail only')),
            ('duplicate status', lambda m: m['design_units'][0].update(status='Approved')),
            ('unsafe empty filename', lambda m: m['design_units'][0].update(outputs=['.'])),
            ('invalid mode type', lambda m: m['design_units'][0].update(mode=[])),
            ('invalid kind type', lambda m: m['surface_details'][0].update(kind=[])),
            ('missing nullable parent', lambda m: m['menus'][0].pop('parent_id')),
            ('duplicate sibling menu', lambda m: m['menus'].append(dict(m['menus'][0], id='M2', page_ids=[], default_page_id=None))),
            ('windows stream output', lambda m: m['design_units'][0].update(outputs=['assets/unit.png:stream'])),
            ('windows trailing alias', lambda m: m['design_units'][0].update(outputs=['assets/unit.png.'])),
            ('malformed feature pages', lambda m: m['features'][0].update(page_ids=None)),
            ('malformed menu pages', lambda m: m['menus'][0].update(page_ids=None)),
            ('malformed initial baseline', lambda m: m['design_units'][0].update(baseline_ref={})),
        ]
        original = copy.deepcopy(self.method)
        for name, mutate in mutations:
            with self.subTest(name=name):
                self.data['methodology'] = copy.deepcopy(original)
                mutate(self.data['methodology'])
                self.assertTrue(any(e.startswith('methodology:') for e in self.check()), name)

    def test_malformed_task_surfaces_do_not_crash(self):
        self.tasks['tasks'][0]['surface_ids'] = None
        self.assertTrue(self.check())

    def test_cli_help_and_structured_generation_errors(self):
        script = Path(__file__).with_name('generate_design_maps.py')
        result = subprocess.run([sys.executable, '-X', 'utf8', str(script), '--help'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('Examples:', result.stdout)
        result = subprocess.run([sys.executable, '-X', 'utf8', str(script),
                                 str(self.root), '--check', '--format', 'json'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)['valid'])
        self.assertTrue(result.stderr.strip())


if __name__ == '__main__':
    unittest.main()
