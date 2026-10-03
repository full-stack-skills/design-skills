"""Product-independent design relationship contract; references existing authorities."""
from pathlib import PurePosixPath, PureWindowsPath
import hashlib
import json


def validate_contract(data, tasks, page_ids, surface_ids, actions):
    errors = []
    def error(message):
        errors.append('methodology: ' + message)
    contract = data.get('methodology')
    if not isinstance(contract, dict) or contract.get('schema_version') != 1:
        return ['methodology: expected schema_version 1']

    def text(row, field):
        value = row.get(field)
        if not isinstance(value, str) or not value.strip():
            error(f"{row.get('id', row.get('page_id', row.get('surface_id')))} missing {field}")
        return value

    def strings(row, field, required=False):
        value = row.get(field)
        if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
            error(f'invalid {field}')
            return set()
        if len(value) != len(set(value)) or (required and not value):
            error(f'duplicate or empty {field}')
        return set(value)

    def records(field, key='id'):
        rows = contract.get(field)
        if not isinstance(rows, list) or not rows:
            error(f'{field} must be nonempty records')
            return {}
        result = {}
        for row in rows:
            if not isinstance(row, dict):
                error(f'malformed {field} record')
                continue
            ident = text(row, key)
            if not isinstance(ident, str) or not ident.strip():
                continue
            if ident in result:
                error(f'duplicate {field} {ident}')
            result[ident] = row
        return result

    def refs(row, field, known, required=False):
        values = strings(row, field, required)
        for missing in values - set(known):
            error(f"{row.get('id', row.get('page_id'))} unknown {field} {missing}")
        return values

    def cycles(rows, field):
        remaining = {k: {r[field]} if isinstance(r.get(field), str) and r[field] in rows else set()
                     for k, r in rows.items()}
        while remaining:
            ready = {k for k, v in remaining.items() if not v}
            if not ready:
                error(f'{field} cycle: {", ".join(sorted(remaining))}')
                break
            remaining = {k: v - ready for k, v in remaining.items() if k not in ready}

    def explicit(row, fields):
        for field in fields:
            if field not in row:
                error(f"{row.get('id', row.get('page_id', row.get('surface_id')))} missing explicit {field}")

    objects, features, menus = records('objects'), records('features'), records('menus')
    pages = records('page_details', 'page_id')
    surfaces = records('surface_details', 'surface_id')
    transitions, units = records('transitions'), records('design_units')
    task_list = tasks.get('tasks') if isinstance(tasks, dict) else None
    task_rows = {r['id']: r for r in task_list
                 if isinstance(r, dict) and isinstance(r.get('id'), str)} if isinstance(task_list, list) else {}
    if not task_rows:
        error('task-coverage.json required')
    if isinstance(tasks, dict) and set(features) != strings(tasks, 'features', True):
        error('features do not match task coverage')
    for label, actual, expected in [('page_details', pages, page_ids), ('surface_details', surfaces, surface_ids)]:
        if set(actual) != set(expected):
            error(f'{label} do not match registry')
    for obj in objects.values():
        for field in ('name', 'owner', 'source'):
            text(obj, field)
    for feature in features.values():
        refs(feature, 'page_ids', page_ids, True)
        refs(feature, 'object_ids', objects, True)
        refs(feature, 'upstream_ids', features)
        refs(feature, 'downstream_ids', features)
        text(feature, 'source')
    labels = set()
    for ident, menu in menus.items():
        explicit(menu, ('parent_id', 'default_page_id'))
        text(menu, 'label')
        sibling_key = (str(menu.get('parent_id')), str(menu.get('label')))
        if sibling_key in labels:
            error(f'{ident} duplicate sibling menu label')
        labels.add(sibling_key)
        targets = refs(menu, 'page_ids', page_ids)
        refs(menu, 'feature_ids', features)
        refs(menu, 'object_ids', objects)
        parent = menu.get('parent_id')
        if parent is not None and (not isinstance(parent, str) or parent not in menus):
            error(f'{ident} unknown menu parent')
        default = menu.get('default_page_id')
        if targets and (not isinstance(default, str) or default not in targets):
            error(f'{ident} default page outside menu targets')
        if not targets and default is not None:
            error(f'{ident} group menu cannot have default page')
        for target in targets & pages.keys():
            if pages[target].get('menu_id') != ident:
                error(f'{ident} reverse menu/page mapping drift')
    cycles(menus, 'parent_id')
    for ident, page in pages.items():
        explicit(page, ('menu_id',))
        for field in ('core_question', 'layout_archetype', 'source'):
            text(page, field)
        for field in ('actors', 'permissions'):
            strings(page, field, True)
        fs = refs(page, 'feature_ids', features, True)
        refs(page, 'object_ids', objects, True)
        for feature in fs & features.keys():
            if ident not in strings(features[feature], 'page_ids'):
                error(f'{ident} feature/page mapping drift')
        menu_id = page.get('menu_id')
        if menu_id is None:
            text(page, 'non_menu_reason')
        elif not isinstance(menu_id, str) or menu_id not in menus or ident not in strings(menus[menu_id], 'page_ids'):
            error(f'{ident} menu/page mapping drift')
    kinds = {'screen', 'tab', 'detail', 'create', 'edit', 'drawer', 'dialog', 'confirmation',
             'result', 'error', 'empty', 'loading', 'readonly', 'conflict', 'state', 'action', 'global'}
    for ident, surface in surfaces.items():
        explicit(surface, ('parent_surface_id',))
        if not isinstance(surface.get('kind'), str) or surface['kind'] not in kinds:
            error(f'{ident} invalid surface kind')
        parent = surface.get('parent_surface_id')
        if parent is not None and (not isinstance(parent, str) or parent not in surfaces):
            error(f'{ident} unknown surface parent')
        if surface.get('kind') in ('drawer', 'dialog', 'confirmation', 'tab', 'detail', 'create', 'edit') and parent is None:
            error(f'{ident} missing source/parent surface')
        text(surface, 'source')
    cycles(surfaces, 'parent_surface_id')
    action_rows = {a['id']: a for a in actions if isinstance(a.get('id'), str)}
    covered_actions = set()
    for ident, transition in transitions.items():
        aid = transition.get('action_id')
        if not isinstance(aid, str) or aid not in action_rows:
            error(f'{ident} unknown action')
            continue
        covered_actions.add(aid)
        if transition.get('kind') not in ('navigation', 'command', 'local'):
            error(f'{ident} invalid transition kind')
        for field in ('precondition', 'state_change', 'recovery', 'permission', 'source_ref'):
            text(transition, field)
        for field in ('source', 'success', 'failure', 'cancel'):
            target = transition.get(field)
            if field == 'cancel' and target == 'return_surface':
                continue
            if not isinstance(target, str) or target not in surface_ids:
                error(f'{ident} unknown {field} target')
        for field, original in [('source', 'source'), ('success', 'target'), ('cancel', 'cancel')]:
            if transition.get(field) != action_rows[aid].get(original):
                error(f'{ident} action {field} drift')
    if covered_actions != set(action_rows):
        error('transitions do not cover registry actions')
    outputs, covered_surfaces = set(), set()
    for ident, unit in units.items():
        explicit(unit, ('parent_unit_id', 'baseline_ref'))
        if {'status', 'done', 'checked', 'completed', 'approved'} & unit.keys():
            error(f'{ident} duplicate execution status forbidden')
        task = unit.get('task_id')
        ss = refs(unit, 'surface_ids', surface_ids, True)
        covered_surfaces.update(ss)
        if not isinstance(task, str) or task not in task_rows:
            error(f'{ident} unknown task')
        elif not ss <= strings(task_rows[task], 'surface_ids'):
            error(f'{ident} task/surface mapping drift')
        if unit.get('mode') not in ('NEW_SCREEN', 'EDIT_PARENT', 'OVERLAY_PARENT', 'ACTION_HIGHLIGHT'):
            error(f'{ident} invalid design mode')
        parent = unit.get('parent_unit_id')
        if unit.get('baseline_ref') is not None:
            text(unit, 'baseline_ref')
        if parent is not None and (not isinstance(parent, str) or parent not in units):
            error(f'{ident} unknown parent unit')
        if unit.get('mode') != 'NEW_SCREEN':
            text(unit, 'baseline_ref')
            if parent is None:
                error(f'{ident} inherited design requires parent unit')
            elif isinstance(parent, str) and parent in units and isinstance(task, str) and task in task_rows:
                parent_task = units[parent].get('task_id')
                if parent_task != task and parent_task not in strings(task_rows[task], 'depends_on'):
                    error(f'{ident} missing parent task dependency')
        frozen = strings(unit, 'frozen_regions')
        allowed = strings(unit, 'allowed_regions', True)
        if frozen & allowed:
            error(f'{ident} frozen/allowed overlap')
        strings(unit, 'acceptance', True)
        text(unit, 'source')
        for output in strings(unit, 'outputs', True):
            normalized = output.replace('\\', '/')
            path = PurePosixPath(normalized)
            invalid_part = any(p.endswith(('.', ' ')) or any(c in p for c in ':*?"<>|')
                               or p.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL',
                                   *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}
                               for p in path.parts)
            if invalid_part or not path.name or path.is_absolute() or PureWindowsPath(output).drive or '..' in path.parts:
                error(f'{ident} unsafe output path')
            key = str(path).casefold()
            if key in outputs:
                error(f'{ident} duplicate output path {output}')
            outputs.add(key)
    cycles(units, 'parent_unit_id')
    if covered_surfaces != set(surface_ids):
        error('design units do not cover registry surfaces')
    return sorted(set(errors))


def render_maps(data, root=None, tasks=None):
    """Derived reference tables only; never task statuses or authority text."""
    contract = data['methodology']
    def cell(value):
        if isinstance(value, list):
            value = ', '.join(value)
        return str(value if value is not None else '—').replace('|', '\\|').replace('\n', ' ')
    canonical = dict(data, methodology={field: sorted(value, key=lambda r: r.get('id', r.get('page_id', r.get('surface_id', ''))))
                                      if isinstance(value, list) and all(isinstance(r, dict) for r in value)
                                      else value for field, value in contract.items()})
    lines = ['# Design relationship maps (generated)', '',
             'Source: registry.json methodology. Read-only projection; approval and runtime evidence remain separate.',
             'Registry SHA256: ' + hashlib.sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True,
                                                           separators=(',', ':')).encode('utf-8')).hexdigest(), '']
    if root is not None:
        references = set()
        for field, rows in contract.items():
            if isinstance(rows, list):
                for row in rows:
                    keys = ('source_ref',) if field == 'transitions' else ('source',)
                    references.update(row[key].split('#', 1)[0] for key in keys
                                      if isinstance(row, dict) and isinstance(row.get(key), str))
        if tasks is not None:
            references.update(row['source'] for row in tasks.get('tasks', []) if isinstance(row, dict))
            lines.extend(['Task index SHA256: ' + hashlib.sha256(json.dumps(tasks, sort_keys=True,
                           ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest(), ''])
        lines.extend(['## Source fingerprints', '', '| Source | SHA256 |', '| --- | --- |'])
        for reference in sorted(references):
            try:
                digest = hashlib.sha256((root / reference).read_bytes()).hexdigest()
            except OSError as exc:
                raise ValueError(f'methodology: unreadable source reference {reference}') from exc
            lines.append('| ' + cell(reference) + ' | ' + digest + ' |')
        lines.append('')
    sections = [('Business objects', 'objects', ['id', 'name', 'owner', 'source']),
                ('Features and dependencies', 'features', ['id', 'page_ids', 'object_ids', 'upstream_ids', 'downstream_ids', 'source']),
                ('Menus', 'menus', ['id', 'label', 'parent_id', 'default_page_id', 'page_ids', 'feature_ids', 'object_ids']),
                ('Page specifications', 'page_details', ['page_id', 'menu_id', 'actors', 'permissions', 'feature_ids', 'object_ids', 'core_question', 'layout_archetype', 'source']),
                ('Interaction surfaces', 'surface_details', ['surface_id', 'kind', 'parent_surface_id', 'source']),
                ('Transitions', 'transitions', ['id', 'action_id', 'kind', 'source', 'precondition', 'permission', 'state_change', 'success', 'failure', 'cancel', 'recovery', 'source_ref']),
                ('Design units', 'design_units', ['id', 'task_id', 'surface_ids', 'mode', 'parent_unit_id', 'baseline_ref', 'frozen_regions', 'allowed_regions', 'acceptance', 'outputs', 'source'])]
    for title, field, columns in sections:
        lines.extend(['## ' + title, '', '| ' + ' | '.join(columns) + ' |',
                      '| ' + ' | '.join('---' for _ in columns) + ' |'])
        for row in sorted(contract[field], key=lambda r: r[columns[0]]):
            lines.append('| ' + ' | '.join(cell(row.get(c)) for c in columns) + ' |')
        lines.append('')
    return '\n'.join(lines)
