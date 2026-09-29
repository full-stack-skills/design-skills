#!/usr/bin/env python3
"""只读校验派生任务索引；不替代原任务源或业务语义审阅。"""
import argparse
import json
from pathlib import Path


def validate(index):
    """检查声明范围覆盖、源定位与依赖图，不写入任何文件。"""
    index = Path(index)
    try:
        data = json.loads(index.read_text())
    except (OSError, ValueError) as exc:
        return [f'unreadable task index: {exc}']
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        return ['expected task index schema_version 1']
    errors = []

    def ids(value, label, required=False):
        if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
            errors.append(f'{label}: expected string ID list')
            return set()
        if required and not value:
            errors.append(f'{label}: empty scope')
        if len(set(value)) != len(value):
            errors.append(f'duplicate {label}')
        return set(value)

    features = ids(data.get('features'), 'features', True)
    surfaces = ids(data.get('surfaces'), 'surfaces', True)
    tasks = data.get('tasks')
    if not isinstance(tasks, list) or not tasks:
        return errors + ['tasks: expected nonempty list']
    graph, covered_features, covered_surfaces = {}, set(), set()
    for row in tasks:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'].strip():
            errors.append('malformed task')
            continue
        ident = row['id']
        if ident in graph:
            errors.append(f'duplicate task {ident}')
        if {'status', 'done', 'checked', 'completed'} & row.keys():
            errors.append(f'{ident}: duplicate execution status is forbidden')
        fs = ids(row.get('feature_ids'), ident + '.feature_ids')
        ss = ids(row.get('surface_ids'), ident + '.surface_ids')
        deps = ids(row.get('depends_on'), ident + '.depends_on')
        graph[ident] = deps
        for val in fs - features:
            errors.append(f'{ident}: unknown feature {val}')
        for val in ss - surfaces:
            errors.append(f'{ident}: unknown surface {val}')
        covered_features.update(fs)
        covered_surfaces.update(ss)
        source, marker = row.get('source'), row.get('marker')
        if not isinstance(source, str) or not source.strip() or Path(source).is_absolute():
            errors.append(f'{ident}: source must be a relative path')
            continue
        if not isinstance(marker, str) or not marker.strip():
            errors.append(f'{ident}: missing source marker')
            continue
        try:
            lines = (index.parent / source).read_text().splitlines()
            if lines.count(marker) != 1:
                errors.append(f'{ident}: source marker must match exactly one line')
        except (OSError, UnicodeError):
            errors.append(f'{ident}: unreadable task source')
    for label, missing in [('features', features - covered_features), ('surfaces', surfaces - covered_surfaces)]:
        if missing:
            errors.append(f'uncovered {label}: {", ".join(sorted(missing))}')
    for ident, deps in graph.items():
        for dep in deps - graph.keys():
            errors.append(f'{ident}: unknown dependency {dep}')
    # Kahn 消除入度为零的节点，避免大计划递归溢出。
    remaining = {k: set(v) & graph.keys() for k, v in graph.items()}
    while remaining:
        ready = {k for k, v in remaining.items() if not v}
        if not ready:
            errors.append('dependency cycle: ' + ', '.join(sorted(remaining)))
            break
        remaining = {k: v - ready for k, v in remaining.items() if k not in ready}
    return sorted(set(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('index', type=Path)
    args = parser.parse_args()
    errors = validate(args.index)
    print(json.dumps({'valid': not errors, 'errors': errors,
                      'boundary': 'Declared scope only; verify scope completeness and source fidelity separately.'}, ensure_ascii=False, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
