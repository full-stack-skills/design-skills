"""验证待分发 Git 文件与 manifest 一致；从暂存区导出的干净副本再次运行测试。"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0'))
    manifest = json.loads((ROOT / '.claude-plugin/plugin.json').read_text())
    expected = {(Path(p) / 'SKILL.md').as_posix() for p in manifest['skills']}
    actual = {p for p in tracked if p.endswith('/SKILL.md')}
    errors = []
    for p in sorted(actual - expected):
        errors.append('unregistered distributed skill: ' + p)
    for p in sorted(expected - actual):
        errors.append('missing distributed skill: ' + p)
    resources = list((ROOT / 'skills/ui-design-harness/profiles').glob('*.json'))
    resources += [ROOT / 'skills/ui-design-visual' / p for p in
                  ['package.json', 'package-lock.json', 'test-prompts.json', 'assets/personal-asset-index.example.json']]
    for p in resources:
        relative = p.relative_to(ROOT).as_posix()
        if relative not in tracked or not p.is_file():
            errors.append('missing distributed resource: ' + relative)
    catalog = ROOT / 'skills/ui-design-harness/profiles/catalog.json'
    if not catalog.is_file():
        errors.append('missing profile catalog')
    else:
        for entry in json.loads(catalog.read_text())['profiles']:
            p = catalog.parent / entry['file']
            if not p.is_file() or p.relative_to(ROOT).as_posix() not in tracked:
                errors.append('missing catalog profile: ' + entry['file'])
    print(json.dumps({'valid': not errors, 'skills': len(actual), 'errors': errors}, ensure_ascii=False, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
