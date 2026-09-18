<div align="center">

# design-skills

**设计与产品体验技能 — UI 工具、功能设计、导航设计、界面连续性**

[![GitHub](https://img.shields.io/badge/github-full--stack--skills%2Fdesign-skills-green.svg)](https://github.com/full-stack-skills/design-skills)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-兼容-purple.svg)](https://agentskills.io)

[English](./README.md) | 简体中文

[简介](#-简介) ·
[安装](#-安装) ·
[技能列表](#-技能列表) ·
[支持的智能体](#-支持的智能体) ·
[生态](#-生态)

</div>

---

## 📖 简介

**设计工具技能** 是一组 AI 编码智能体技能，属于 [Full Stack Skills](https://github.com/partme-ai/full-stack-skills) 生态，由 [PartMe.AI](https://github.com/partme-ai) 维护。

本包当前注册 **10 个技能**。每个技能是一个独立的 `SKILL.md` 文件，AI 智能体按需加载。

## 📦 安装

```bash
npx skills add full-stack-skills/design-skills
```

或按需安装特定技能：

```bash
npx skills add full-stack-skills/design-skills --skill <skill-name>
```

## 🎯 技能列表 (10)

| 技能 | 描述 |
|------|------|
| `adobe-xd` | Provides comprehensive guidance for Adobe XD including design creation, prototyping, components, and collaboration. U... |
| `algorithmic-art` | Creating algorithmic art using p5.js with seeded randomness and interactive parameter exploration. Use this when user... |
| `brand-guidelines` | Applies Anthropic's official brand colors and typography to any sort of artifact that may benefit from having Anthrop... |
| `canvas-design` | Create beautiful visual art in .png and .pdf documents using design philosophy. You should use this skill when the us... |
| `cross-platform-mvp-ui-alignment` | 对齐多平台 MVP 规格、产品状态、设计语言，并生成相互匹配的 Phone/Tablet UI 资产。 |
| `feature-design` | 将薄需求转化为可观察的功能行为契约，覆盖动作、状态、权限、证据与验收。 |
| `navigation-design` | 定义分层导航、路由、激活态、上下文传递、深链与返回契约，防止导航层级漂移。 |
| `ui-continuity` | 在已确认界面基线上继续设计，通过固定区、变更预算、局部反馈与差异检查保持连续性。 |
| `product-design` | 编排跨功能、导航、文档、连续设计、视觉执行、评审与验证的产品设计流程，避免重复实现专业技能。 |
| `design-guard` | 审查跨规格、导航、任务、提示词与设计资产的一致性，区分机械检查与判断检查，并在证据或权威未解决时阻止提升。 |

## 🤖 支持的智能体

适用于 [Claude Code](https://code.claude.com)、[Codex](https://developers.openai.com/codex)、[Cursor](https://cursor.com)、[OpenCode](https://opencode.ai)、[Gemini CLI](https://geminicli.com)、[GitHub Copilot](https://github.com/features/copilot)、[Windsurf](https://codeium.com/windsurf) 及 [70+ 其他平台](https://agentskills.io/clients)。

### Claude Code 安装

**方式一：npx skills CLI（推荐）**

```bash
npx skills add full-stack-skills/design-skills
```

**方式二：手动安装**

```bash
git clone https://github.com/full-stack-skills/design-skills.git
cp -r design-skills/skills/* .claude/skills/
```

更多详情请参阅 [Claude Code 技能指南](https://code.claude.com/docs/en/skills) 和 [Agent Skills 规范](https://agentskills.io/)。

## 🌐 生态

| 资源 | 链接 |
|------|------|
| **Full Stack Skills** | [github.com/partme-ai/full-stack-skills](https://github.com/partme-ai/full-stack-skills) |
| **全部技能组** | [github.com/full-stack-skills](https://github.com/full-stack-skills) |
| **Agent Skills 规范** | [agentskills.io](https://agentskills.io) |
| **Skills CLI** | [github.com/vercel-labs/skills](https://github.com/vercel-labs/skills) |

## 📄 许可证

Apache 2.0 — 详见 [LICENSE](LICENSE)。

第三方组件归属声明：详见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)。
