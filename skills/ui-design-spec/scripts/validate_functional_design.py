#!/usr/bin/env python3
"""只读校验完整功能设计的文件与引用；不证明语义质量、批准或运行成功。"""
import argparse
import json
import re
from pathlib import Path
from validate_task_coverage import validate as validate_tasks

DOCUMENTS = ('README.md', 'FUNCTION-CATALOG.md', 'NAVIGATION.md',
             'UI-STRUCTURE.md', 'USER-FLOWS.md', 'SCREEN-REGISTRY.md',
             'GLOBAL-SURFACES.md', 'MASTER-PLAN.md', 'DESIGN-EXECUTION.md', 'STATUS.md')
PAGE_FIELDS = ('id', 'name', 'scope', 'nav', 'phase', 'purpose', 'entry',
               'layout', 'fields', 'validation', 'state', 'error', 'result', 'requirements')


def validate(package, document_map=None, require_task_coverage=False):
    """返回结构问题，不修改文档或提升状态；允许现有文件名通过映射保留。"""
    root = Path(package)
    mapping = document_map or {}
    if not isinstance(mapping, dict) or any(
            not isinstance(k, str) or not isinstance(v, str) or not v.strip()
            for k, v in mapping.items()):
        return ['document_map must map logical names to nonempty relative paths']
    allowed = set(DOCUMENTS) | {'pages', 'registry.json'}
    if set(mapping) - allowed:
        return ['unknown document_map keys']
    errors = []

    def path(name):
        return root / mapping.get(name, name)

    def read(p):
        try:
            value = p.read_text(encoding='utf-8')
            if not value.strip():
                errors.append(f'empty document: {p.name}')
            return value
        except (OSError, UnicodeError):
            errors.append(f'missing or unreadable document: {p.name}')
            return ''

    documents = {name: read(path(name)) for name in DOCUMENTS}
    try:
        data = json.loads(read(path('registry.json')))
    except ValueError:
        return errors + ['registry.json must contain valid JSON']
    if not isinstance(data, dict):
        return errors + ['registry must be an object']

    def rows(value, label, required=False):
        if not isinstance(value, list) or (required and not value):
            errors.append(f'{label}: expected a list of records')
            return []
        result = []
        for item in value:
            if not isinstance(item, dict):
                errors.append(f'{label}: malformed record')
            else:
                result.append(item)
        return result

    def text(row, field, label):
        v = row.get(field)
        if not isinstance(v, str) or not v.strip():
            errors.append(f'{label}: missing {field}')
            return ''
        return v

    pages = rows(data.get('pages'), 'pages', True)
    globals_ = rows(data.get('globals'), 'globals')
    identities, surfaces, actions, doc_paths = set(), set(), [], []
    page_ids = set()

    def register(value, surface=False):
        if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', value):
            errors.append(f'invalid ID: {value!r}')
            return False
        if value in identities:
            errors.append(f'duplicate ID: {value}')
        identities.add(value)
        if surface:
            surfaces.add(value)
        return True

    for page in pages:
        ident = page.get('id')
        for field in PAGE_FIELDS:
            text(page, field, str(ident))
        if not register(ident):
            continue
        page_ids.add(ident)
        p = path('pages') / (ident + '.md')
        content = read(p)
        doc_paths.append((p, content))
        # 清单必须可导航到对应详规，而非只出现一个页面名字。
        relative = mapping.get('pages', 'pages').rstrip('/') + '/' + ident + '.md'
        if relative not in documents['FUNCTION-CATALOG.md']:
            errors.append(f'{ident}: missing catalog page link')
        views = page.get('views')
        if not isinstance(views, list) or not views:
            errors.append(f'{ident}: missing views')
            views = []
        for index, view in enumerate(views, 1):
            if isinstance(view, str) and view.strip():
                register(f'{ident}-{index:02}', True)
            elif isinstance(view, dict):
                text(view, 'name', ident)
                register(view.get('id'), True)
            else:
                errors.append(f'{ident}: malformed view')
        for action in rows(page.get('actions'), ident + '.actions', True):
            register(action.get('id'), True)
            actions.append(action)
            for field in ('name', 'precondition', 'effect', 'source', 'target', 'cancel'):
                text(action, field, str(action.get('id')))
        for key, default in (('state_id', 'S01'), ('error_id', 'E01'), ('result_id', 'R01')):
            register(page.get(key, f'{ident}-{default}'), True)
    for item in globals_:
        ident = item.get('id')
        if not register(ident):
            continue
        for field in ('name', 'entry', 'presentation', 'layout', 'effect', 'fields', 'failure', 'target'):
            text(item, field, ident)
        register(item.get('surface_id', ident + '-01'), True)
    for action in actions:
        for field in ('source', 'target', 'cancel'):
            value = action.get(field)
            if field == 'cancel' and value == 'return_surface':
                continue
            if not isinstance(value, str) or value not in surfaces:
                errors.append(f"{action.get('id')}: unknown {field} {value!r}")
    for item in globals_:
        target = item.get('target')
        if not isinstance(target, str) or target not in surfaces:
            errors.append(f"{item.get('id')}: unknown target {target!r}")
    for ident in surfaces:
        if not re.search(r'\|\s*' + re.escape(ident) + r'\s*\|', documents['SCREEN-REGISTRY.md']):
            errors.append(f'missing registry row: {ident}')
    if path('pages').is_dir():
        for p in path('pages').glob('*.md'):
            if p.stem not in page_ids:
                errors.append(f'unregistered page document: {p.name}')
    for name, content in documents.items():
        doc_paths.append((path(name), content))
    for p, content in doc_paths:
        fence = None
        prose = []
        for line in content.splitlines():
            match = re.match(r'^\s*(`{3,}|~{3,})', line)
            if match:
                token = match.group(1)
                if fence is None:
                    fence = token
                elif token[0] == fence[0] and len(token) >= len(fence):
                    fence = None
                continue
            if fence is None:
                prose.append(line)
        if fence:
            errors.append(f'unclosed code fence: {p.name}')
        for link in re.findall(r'\]\(([^)]+)\)', '\n'.join(prose)):
            if re.match(r'^[a-zA-Z][\w+.-]*:', link) or link.startswith('#'):
                continue
            target = link.split('#', 1)[0].strip('<>')
            if target and not (p.parent / target).is_file():
                errors.append(f'broken link {p.name}: {link}')
    task_index = root / 'task-coverage.json'
    if require_task_coverage or task_index.exists():
        errors.extend(validate_tasks(task_index))
        try:
            task_data = json.loads(task_index.read_text())
            declared = task_data.get('surfaces') if isinstance(task_data, dict) else None
            if isinstance(declared, list) and all(isinstance(v, str) for v in declared):
                if set(declared) != surfaces:
                    errors.append('task coverage surfaces do not match registry')
        except (OSError, ValueError):
            pass  # 读取问题已由任务校验器返回。
    return sorted(set(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--document-map', type=Path, help='JSON mapping of logical document names to existing paths')
    parser.add_argument('--require-task-coverage', action='store_true', help='Require derived task coverage index for new full-product packages')
    args = parser.parse_args()
    try:
        mapping = json.loads(args.document_map.read_text()) if args.document_map else None
        errors = validate(args.package, mapping, args.require_task_coverage)
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    print(json.dumps({'valid': not errors, 'errors': errors,
                      'boundary': 'Structure and supplied task index only; scope completeness, semantic review, approvals and runtime evidence remain separate.'}, ensure_ascii=False, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
