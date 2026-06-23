# CLAUDE.md

## Project

`design-skills` — curated collection of 4 Agent Skills for AI coding agents (Claude Code, Codex, Cursor, etc.). Part of the [Full Stack Skills](https://github.com/partme-ai/full-stack-skills) ecosystem by PartMe.AI. Apache 2.0 licensed.

## Skills

| Skill | Directory | Purpose |
|-------|-----------|---------|
| `adobe-xd` | `skills/adobe-xd/` | Adobe XD UI/UX design, prototyping, components, collaboration |
| `algorithmic-art` | `skills/algorithmic-art/` | p5.js generative art with seeded randomness, flow fields, particles |
| `brand-guidelines` | `skills/brand-guidelines/` | Apply Anthropic brand colors/typography to artifacts |
| `canvas-design` | `skills/canvas-design/` | Visual poster/design creation as .png or .pdf |

## Directory Structure

```
skills/<skill-name>/
  SKILL.md          # YAML frontmatter + markdown body (loaded on-demand by agents)
  LICENSE.txt       # Per-skill license
  templates/        # Optional: code templates (algorithmic-art)
  canvas-fonts/     # Optional: bundled .ttf fonts (canvas-design)
.claude-plugin/
  plugin.json       # Plugin manifest listing all skills
```

## SKILL.md Authoring Conventions

- **Frontmatter** (YAML): `name`, `description`, `license` are required. `description` should include trigger conditions (when to invoke).
- **Body sections**: "When to use this skill", "How to use this skill", "Best Practices", "Keywords".
- **Language**: English primary; Chinese content is acceptable alongside English.
- **Assets**: Bundle fonts, templates, or other resources alongside the SKILL.md within the skill directory.
- **Philosophy-driven skills** (`algorithmic-art`, `canvas-design`): two-phase approach — first generate a creative philosophy/manifesto, then execute it in code/canvas.

## Key Files

| File | Purpose |
|------|---------|
| `README.md` / `README.zh-CN.md` | Bilingual project documentation |
| `.claude-plugin/plugin.json` | Plugin manifest — update when adding/removing skills |
| `LICENSE` | Apache 2.0 |

## Plugin Manifest

`plugin.json` maps skills to their directories via the `skills` array. When adding a new skill, register it there:

```json
{
  "name": "design-skills",
  "skills": [
    "./skills/<new-skill>"
  ]
}
```

## Install

```bash
npx skills add full-stack-skills/design-skills
```
