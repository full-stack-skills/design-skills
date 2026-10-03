"""Keep the distributed specification skill independent of product case studies."""
import re
import unittest
from pathlib import Path


class StandardSkillTests(unittest.TestCase):
    def test_official_document_contract(self):
        path = Path(__file__).resolve().parents[1] / 'SKILL.md'
        text = path.read_text(encoding='utf-8')
        self.assertLess(len(text.splitlines()), 500)
        frontmatter = text.split('---', 2)[1]
        name = re.search(r'^name: (.+)$', frontmatter, re.M).group(1)
        self.assertEqual(name, path.parent.name)
        self.assertRegex(name, r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
        self.assertLessEqual(len(name), 64)
        description = re.search(r'^description: (.+)$', frontmatter, re.M).group(1)
        self.assertLessEqual(len(description), 1024)
        self.assertLessEqual(len(description), 200, 'Compatibility with the user-specified Anthropic help article')
        self.assertTrue(description.startswith('Use when'))
        for section in ('## 不适用与边界', '## Gotchas', '## Examples',
                        '## How to use · Workflow', '## Validation checklist', '## References'):
            self.assertIn(section, text)
        interface = path.parent / 'agents/openai.yaml'
        self.assertTrue(interface.is_file())
        self.assertIn('$ui-design-spec', interface.read_text(encoding='utf-8'))

    def test_runtime_documents_are_product_independent(self):
        root = Path(__file__).resolve().parents[1]
        names = re.compile(r'evently|wekefu|wakefu|年会|agent browser', re.I)
        files = [root / 'SKILL.md', *root.joinpath('references').glob('*.md'),
                 *root.joinpath('assets').glob('*.md')]
        for path in files:
            with self.subTest(path=path.name):
                self.assertIsNone(names.search(path.read_text(encoding='utf-8')))
        self.assertFalse((root / 'examples').exists(), 'Historical fixtures belong outside distributed skills')
        self.assertTrue((root / 'references/design-workflow.md').is_file())


if __name__ == '__main__':
    unittest.main()
