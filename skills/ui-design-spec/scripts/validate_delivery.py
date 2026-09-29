#!/usr/bin/env python3
"""Legacy 00-06/delivery.json contract checks only. A pass is structural evidence, not product approval."""
import argparse
import json
from pathlib import Path

FILES = ['00-scope-and-sources.md', '01-feature-catalog.md',
         '02-navigation-and-layout.md', '03-journeys-and-states.md',
         '04-surface-registry.md', '05-task-plan.md', '06-review-report.md']
AREAS = {'source_authority', 'functional_closure', 'layout_and_navigation',
         'interaction_and_recovery', 'task_plan', 'cross_surface_consistency'}
FIELDS = {
    'sources': 'id location version evidence_kind conclusion',
    'features': 'id goal preconditions inputs outputs permission exceptions acceptance priority maturity',
    'surfaces': 'id kind entry preconditions context user_question layout required_information primary_action secondary_actions fields_and_validation permission success failure return_behavior accessibility data_contract visual_dependency acceptance',
    'journeys': 'id goal preconditions outcome',
    'tasks': 'id phase owner_role inputs deliverable acceptance verification source_marker',
    'issues': 'id severity description impact resolution',
    'reviews': 'area verdict evidence',
}


def validate(root, require_ready=False):
    root = Path(root)
    errors = []
    def problem(message):
        errors.append(message)
    def text(obj, key, where):
        value = obj.get(key)
        if not isinstance(value, str) or not value.strip() or value.strip().lower() in {'todo', 'tbd', '待补', '待填写', '...'}:
            problem(f'{where}.{key}: requires concrete nonempty text')
            return ''
        return value
    for name in FILES:
        path = root / name
        if not path.is_file() or not path.read_text(encoding='utf-8').strip():
            problem(f'missing or empty document: {name}')
    try:
        data = json.loads((root / 'delivery.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        return errors + [f'delivery.json: {exc}']
    if not isinstance(data, dict):
        return errors + ['delivery.json must be an object']
    if type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        problem('schema_version must be 1')
    if data.get('status') not in {'draft', 'blocked', 'ready'}:
        problem('invalid status')
    if require_ready and data.get('status') != 'ready':
        problem('delivery is not ready')
    scope = data.get('scope', {})
    if not isinstance(scope, dict):
        problem('scope must be an object')
        scope = {}
    for key in 'product users objects in_scope out_of_scope spec_source'.split():
        text(scope, key, 'scope')
    groups = {}
    seen = set()
    for group, fields in FIELDS.items():
        rows = data.get(group)
        if not isinstance(rows, list) or (not rows and group != 'issues'):
            problem(f'{group}: requires a list of records')
            rows = []
        groups[group] = []
        for pos, row in enumerate(rows):
            where = f'{group}[{pos}]'
            if not isinstance(row, dict):
                problem(f'{where}: requires an object')
                continue
            groups[group].append(row)
            for key in fields.split():
                text(row, key, where)
            if group != 'reviews':
                ident = row.get('id')
                if isinstance(ident, str):
                    if ident in seen:
                        problem(f'duplicate ID: {ident}')
                    seen.add(ident)
    ids = {g: {r['id'] for r in rows if isinstance(r.get('id'), str)}
           for g, rows in groups.items() if g != 'reviews'}
    def refs(row, key, target, where, allow_empty=False):
        values = row.get(key)
        if not isinstance(values, list) or (not values and not allow_empty):
            problem(f'{where}.{key}: requires reference list')
            return []
        valid = []
        for value in values:
            if not isinstance(value, str) or value not in ids[target]:
                problem(f'{where}.{key}: unknown reference {value!r}')
            elif value in valid:
                problem(f'{where}.{key}: duplicate reference {value}')
            else:
                valid.append(value)
        return valid
    for row in groups['sources']:
        if row.get('evidence_kind') not in {'user_decision', 'spec', 'code', 'runtime', 'design', 'history'}:
            problem(f"source {row.get('id')}: invalid evidence_kind")
    for row in groups['features']:
        refs(row, 'source_ids', 'sources', str(row.get('id')))
    parent_graph = {}
    feature_surfaces = set()
    for row in groups['surfaces']:
        ident = str(row.get('id'))
        feature_surfaces.update(refs(row, 'feature_ids', 'features', ident))
        kind = row.get('kind')
        if kind not in {'page', 'subview', 'action', 'state', 'error', 'result', 'global'}:
            problem(f'{ident}: invalid surface kind')
        parent = row.get('parent_id')
        if 'parent_id' not in row or (parent is not None and not isinstance(parent, str)):
            problem(f'{ident}: parent_id must be explicit null or ID')
        elif parent:
            if parent not in ids['surfaces']:
                problem(f'{ident}: unknown parent {parent}')
            else:
                parent_graph[ident] = [parent]
        elif kind not in {'page', 'global'}:
            problem(f'{ident}: child surface requires parent')
    journey_features = set()
    for row in groups['journeys']:
        ident = str(row.get('id'))
        journey_features.update(refs(row, 'feature_ids', 'features', ident))
        steps = row.get('steps')
        if not isinstance(steps, list) or not steps:
            problem(f'{ident}: requires journey steps')
            steps = []
        for step in steps:
            if not isinstance(step, dict):
                problem(f'{ident}: step must be an object')
                continue
            for field in 'surface_id action transition permission success failure'.split():
                text(step, field, ident)
            if not isinstance(step.get('surface_id'), str) or step['surface_id'] not in ids['surfaces']:
                problem(f'{ident}: unknown step surface')
        branches = row.get('branches')
        if not isinstance(branches, dict):
            problem(f'{ident}: requires branches object')
            branches = {}
        for branch in 'failure denial cancel offline conflict interruption recovery'.split():
            text(branches, branch, ident)
    task_source = text(data, 'task_source', 'delivery')
    source_text = ''
    if task_source:
        try:
            source_text = (root / task_source).read_text(encoding='utf-8')
        except OSError:
            problem('task_source does not resolve to a readable local file')
    task_features, task_surfaces, dependency_graph = set(), set(), {}
    for row in groups['tasks']:
        ident = str(row.get('id'))
        task_features.update(refs(row, 'feature_ids', 'features', ident))
        task_surfaces.update(refs(row, 'surface_ids', 'surfaces', ident))
        dependency_graph[ident] = refs(row, 'depends_on', 'tasks', ident, True)
        if any(k in row for k in ('status', 'checked')):
            problem(f'{ident}: duplicate execution status is forbidden')
        marker = row.get('source_marker')
        if isinstance(marker, str) and marker and source_text.count(marker) != 1:
            problem(f'{ident}: source_marker must uniquely locate canonical task')
    def cycles(graph, label):
        visiting, done = set(), set()
        def visit(node):
            if node in visiting:
                problem(f'{label}: cycle at {node}')
                return
            if node in done:
                return
            visiting.add(node)
            for nxt in graph.get(node, []):
                visit(nxt)
            visiting.remove(node)
            done.add(node)
        for node in graph:
            visit(node)
    cycles(parent_graph, 'surface parents')
    cycles(dependency_graph, 'task dependencies')
    for label, required, covered in [
        ('features without surfaces', ids['features'], feature_surfaces),
        ('features without journeys', ids['features'], journey_features),
        ('features without tasks', ids['features'], task_features),
        ('surfaces without tasks', ids['surfaces'], task_surfaces),
    ]:
        if required - covered:
            problem(f'{label}: {sorted(required - covered)}')
    for row in groups['issues']:
        if row.get('severity') not in {'blocker', 'warning'}:
            problem('invalid issue severity')
        if data.get('status') == 'ready' and row.get('severity') == 'blocker' and row.get('resolution') == 'open':
            problem(f"open blocker: {row.get('id')}")
    areas = []
    for row in groups['reviews']:
        area = row.get('area')
        if not isinstance(area, str):
            continue
        areas.append(area)
        if row.get('verdict') not in {'pass', 'fail', 'pending'}:
            problem(f'{area}: invalid review verdict')
        if data.get('status') == 'ready' and row.get('verdict') != 'pass':
            problem(f'{area}: review not passed')
        evidence = row.get('evidence', '')
        if isinstance(evidence, str):
            # "relative-path.md#section | specific observation"
            path = evidence.split('|', 1)[0].strip().split('#', 1)[0]
            if not path or not (root / path).is_file() or '|' not in evidence or not evidence.split('|', 1)[1].strip():
                problem(f'{area}: evidence must resolve to local file and include observation')
    if set(areas) != AREAS or len(areas) != len(AREAS):
        problem('reviews must contain each of the six required areas exactly once')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package')
    parser.add_argument('--require-ready', action='store_true')
    args = parser.parse_args()
    errors = validate(args.package, args.require_ready)
    print(json.dumps({'valid': not errors, 'errors': errors,
                      'boundary': 'Structural validation only; semantic review remains required.'}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
