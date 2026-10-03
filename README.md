<div align="center">

# design-skills

**Design and product experience skills — UI tools, feature design, navigation, continuity**

[![GitHub](https://img.shields.io/badge/github-full--stack--skills%2Fdesign-skills-green.svg)](https://github.com/full-stack-skills/design-skills)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Compatible-purple.svg)](https://agentskills.io)

English | [简体中文](./README.zh-CN.md)

[Introduction](#-introduction) ·
[Install](#-install) ·
[Skills](#-skills) ·
[Supported Agents](#-supported-agents) ·
[Ecosystem](#-ecosystem)

</div>

---

## 📖 Introduction

**Design Tools Skills** is a curated collection of Agent Skills for AI coding agents, part of the [Full Stack Skills](https://github.com/partme-ai/full-stack-skills) ecosystem maintained by [PartMe.AI](https://github.com/partme-ai).

This package currently registers **16 skills**. Each skill is a self-contained `SKILL.md` file that AI agents load on-demand.

## 📦 Install

```bash
npx skills add full-stack-skills/design-skills
```

Or install specific skills:

```bash
npx skills add full-stack-skills/design-skills --skill <skill-name>
```

## 🎯 Skills (16)

| Skill | Description |
|-------|-------------|
| `adobe-xd` | Provides comprehensive guidance for Adobe XD including design creation, prototyping, components, and collaboration. U... |
| `algorithmic-art` | Creating algorithmic art using p5.js with seeded randomness and interactive parameter exploration. Use this when user... |
| `brand-guidelines` | Applies Anthropic's official brand colors and typography to any sort of artifact that may benefit from having Anthrop... |
| `canvas-design` | Create beautiful visual art in .png and .pdf documents using design philosophy. You should use this skill when the us... |
| `cross-platform-mvp-ui-alignment` | Align cross-platform MVP specifications, product states, design language, and matching Phone/Tablet UI asset sets. |
| `ui-design-feature` | Turn underspecified product features into observable behavior contracts covering actions, states, permissions, evidence, and acceptance. |
| `ui-design-nav` | Define scoped navigation, routes, activation, context propagation, deep links, and return contracts without hierarchy drift. |
| `ui-design-continuity` | Continue approved UI families with explicit immutable regions, change budgets, scoped feedback, and baseline-vs-candidate checks. |
| `ui-design-spec` | Unified entry: Product-independent method for menu maps, page specs, interaction surfaces, flows, independent design units, and generated consistency checks; execution hands off to Harness and specialists. |
| `ui-design-review` | Audit cross-artifact design consistency, distinguish mechanical and judgment checks, and block promotion when evidence or authority is unresolved. |
| `ui-design-harness` | Execute resumable, evidence-backed design SOPs across specialist skills, tools, approvals, corrections, reconciliation, and promotion gates. |
| `ui-design-theme` | Apply reusable artifact themes. |
| `remotion` | Create programmatic videos with Remotion. |
| `ui-design-visual` | Create high-fidelity HTML design prototypes. |
| [ui-design-preview](skills/ui-design-preview/SKILL.md) | Synchronized pages/themes and multi-device preview comparison, with a complete standalone application. |
| `better-icons` | Find and use icons. |

## 🤖 Supported Agents

Works with [Claude Code](https://code.claude.com), [Codex](https://developers.openai.com/codex), [Cursor](https://cursor.com), [OpenCode](https://opencode.ai), [Gemini CLI](https://geminicli.com), [GitHub Copilot](https://github.com/features/copilot), [Windsurf](https://codeium.com/windsurf), and [70+ others](https://agentskills.io/clients).

### Claude Code Installation

**Option 1: npx skills CLI (Recommended)**

```bash
npx skills add full-stack-skills/design-skills
```

**Option 2: Manual Installation**

```bash
git clone https://github.com/full-stack-skills/design-skills.git
cp -r design-skills/skills/* .claude/skills/
```

For more details, see the [Claude Code Skills Guide](https://code.claude.com/docs/en/skills) and [Agent Skills Spec](https://agentskills.io/).

## 🌐 Ecosystem

| Resource | Link |
|----------|------|
| **Full Stack Skills** | [github.com/partme-ai/full-stack-skills](https://github.com/partme-ai/full-stack-skills) |
| **All Skill Groups** | [github.com/full-stack-skills](https://github.com/full-stack-skills) |
| **Agent Skills Spec** | [agentskills.io](https://agentskills.io) |
| **Skills CLI** | [github.com/vercel-labs/skills](https://github.com/vercel-labs/skills) |

## 📄 License

Apache 2.0 — see [LICENSE](LICENSE).

Third-party attribution notices: see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
