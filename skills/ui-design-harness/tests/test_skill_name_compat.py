"""技能更名后的新运行与旧运行兼容行为。"""
import importlib.util
from pathlib import Path
import tempfile
import unittest

path = Path(__file__).resolve().parents[1] / 'scripts/design_harness.py'
spec = importlib.util.spec_from_file_location('harness_name_compat', path)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


class SkillNameCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Path(self.tmp.name)
        self.run = h.start_run(store=self.store, product_id='example', product_version='v1',
                               surface='desktop', scope_type='page', scope_ids=['P01'],
                               profile_id='product-to-ui')

    def snapshot(self):
        return {p.relative_to(self.store).as_posix(): p.read_bytes()
                for p in self.store.rglob('*') if p.is_file()}

    def test_new_profile_dispatch_uses_registered_skill(self):
        self.assertEqual(h.issue_dispatch(self.store, self.run['run_id'])['handler'], 'ui-design-spec')
        self.assertEqual(self.run['profile']['version'], 3)

    def test_old_plan_resolves_without_rewriting_history(self):
        self.run['profile']['version'] = 1
        self.run['stage_plan'][0]['handler'] = 'product-design'
        self.run = h.save_run(self.store, self.run)
        before = self.snapshot()
        action = h.get_next_action(self.store, self.run['run_id'])
        self.assertEqual(action['handler'], 'ui-design-spec')
        self.assertEqual(before, self.snapshot())
        packet = h.issue_dispatch(self.store, self.run['run_id'])
        self.assertEqual(packet['handler'], 'ui-design-spec')
        saved = h.load_run(self.store, self.run['run_id'])
        self.assertEqual(saved['stage_plan'][0]['handler'], 'product-design')
        self.assertEqual(saved['profile']['version'], 1)

    def test_existing_dispatch_returns_new_name_without_mutation(self):
        packet = h.issue_dispatch(self.store, self.run['run_id'])
        saved = h.load_run(self.store, self.run['run_id'])
        saved['dispatches'][0]['handler'] = 'product-design'
        h.save_run(self.store, saved)
        before = self.snapshot()
        self.assertEqual(h.get_next_action(self.store, self.run['run_id'])['handler'], 'ui-design-spec')
        repeated = h.issue_dispatch(self.store, self.run['run_id'])
        self.assertEqual(repeated['handler'], 'ui-design-spec')
        self.assertEqual(repeated['dispatch_id'], packet['dispatch_id'])
        self.assertEqual(before, self.snapshot())
        result = h.complete_dispatch(self.store, self.run['run_id'], packet['dispatch_id'],
                                     {'stage': 'baseline', 'status': 'pass', 'producer': 'ui-design-spec',
                                      'observed_result': 'Scoped authority checked'})
        self.assertEqual(result['state'], 'BASELINE_BOUND')
        self.assertEqual(result['dispatches'][0]['handler'], 'product-design')

    def test_continuity_profile_and_old_plan_use_current_skill(self):
        profile = h.load_profile('design-correction')
        self.assertEqual(profile['stages'][0]['handler'], 'ui-design-continuity')
        run = self.run
        run['stage_plan'][0]['handler'] = 'ui-continuity'
        h.save_run(self.store, run)
        before = self.snapshot()
        self.assertEqual(h.get_next_action(self.store, run['run_id'])['handler'], 'ui-design-continuity')
        self.assertEqual(before, self.snapshot())
        packet = h.issue_dispatch(self.store, run['run_id'])
        self.assertEqual(packet['handler'], 'ui-design-continuity')
        self.assertEqual(h.load_run(self.store, run['run_id'])['stage_plan'][0]['handler'], 'ui-continuity')

    def test_initial_preflight_can_reach_candidate_without_visual_approval(self):
        for stage in ['baseline', 'behavior', 'navigation', 'task', 'continuity']:
            packet = h.issue_dispatch(self.store, self.run['run_id'])
            self.assertEqual(packet['expected_evidence']['stage'], stage)
            observed = 'Synthetic prerequisite for initial-mode handoff test'
            if stage == 'continuity':
                observed = 'initial: baseline_id=null; confirmed routes fixed; theme proposed; no visual approval; candidate comparison deferred to review'
            h.complete_dispatch(self.store, self.run['run_id'], packet['dispatch_id'],
                                {'stage': stage, 'status': 'pass', 'producer': packet['handler'],
                                 'observed_result': observed})
        saved = h.load_run(self.store, self.run['run_id'])
        self.assertEqual(saved['state'], 'CONTINUITY_READY')
        next_action = h.get_next_action(self.store, self.run['run_id'])
        self.assertEqual(next_action['evidence_stage'], 'candidate')
        self.assertEqual(next_action['handler'], 'renderer')

    def test_unknown_provider_handler_stays_unchanged(self):
        self.run['stage_plan'][0]['handler'] = 'custom-provider'
        h.save_run(self.store, self.run)
        self.assertEqual(h.get_next_action(self.store, self.run['run_id'])['handler'], 'custom-provider')


if __name__ == '__main__':
    unittest.main()
