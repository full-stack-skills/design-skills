#!/usr/bin/env python3
"""Generate/check one derived map; preserve all authority documents and statuses."""
import argparse
import json
import sys
from pathlib import Path
from methodology import render_maps
from validate_functional_design import validate


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Examples:\n  python generate_design_maps.py docs/functional-design --check --format json\n'
               '  python generate_design_maps.py docs/functional-design --write\n'
               'Exit codes: 0 = success; 1 = invalid input or stale/missing output; 2 = invalid CLI usage.')
    parser.add_argument('package', type=Path)
    parser.add_argument('--document-map', type=Path)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--write', action='store_true', help='Create/replace only the derived map after input validation')
    modes.add_argument('--check', action='store_true', help='Read-only validation and freshness check')
    parser.add_argument('--format', choices=('text', 'json'), default='text', help='Output format (default: text)')
    args = parser.parse_args()
    def report(valid, errors):
        if args.format == 'json':
            print(json.dumps({'valid': valid, 'mode': 'write' if args.write else 'check',
                              'output': str(args.package / 'DESIGN-MAP.generated.md'),
                              'errors': errors}, ensure_ascii=False, indent=2))
        if errors:
            print('Design map check failed: ' + '; '.join(errors) +
                  '. Correct source contracts, then regenerate with --write and rerun --check.', file=sys.stderr)
        elif args.format == 'text':
            print('Design map matches validated contract; semantic and visual review remain required.')
    try:
        mapping = json.loads(args.document_map.read_text(encoding='utf-8')) if args.document_map else None
        errors = validate(args.package, mapping, require_task_coverage=True, require_methodology=True)
        # Writing replaces only stale derived output, never invalid input contracts.
        if args.write:
            errors = [e for e in errors if e != 'methodology: stale generated design map']
        if errors:
            report(False, errors)
            return 1
        data = json.loads((args.package / (mapping or {}).get('registry.json', 'registry.json')).read_text(encoding='utf-8'))
        task_data = json.loads((args.package / 'task-coverage.json').read_text(encoding='utf-8'))
        expected = render_maps(data, args.package, task_data)
        output = args.package / 'DESIGN-MAP.generated.md'
        if args.write:
            if output.is_symlink():
                raise ValueError('refusing to overwrite symlink output')
            output.write_text(expected, encoding='utf-8', newline='\n')
        elif not output.is_file() or output.read_text(encoding='utf-8') != expected:
            report(False, ['Missing or stale DESIGN-MAP.generated.md'])
            return 1
        report(True, [])
        return 0
    except (OSError, ValueError) as exc:
        report(False, [str(exc)])
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
