# Skill authoring policy

Primary sources:

- [Anthropic: 创建自定义 Skills](https://support.claude.com/zh-CN/articles/12512198-%E5%A6%82%E4%BD%95%E5%88%9B%E5%BB%BA%E8%87%AA%E5%AE%9A%E4%B9%89-skills)
- [Agent Skills overview](https://agentskills.io/what-are-skills)
- [Agent Skills format specification](https://agentskills.io/specification)

Each distributed skill has a root SKILL.md with YAML name and description plus task instructions. Follow the format specification for name/directory correspondence, field types and lengths. Describe both task purpose and activation conditions. For the specification entrypoint, keep description within 200 characters to also satisfy the linked Anthropic Chinese article; the format specification permits up to 1024.

Use progressive disclosure: concise entrypoint instructions, conditionally loaded references, executable scripts with documented dependencies, and static assets/templates. scripts/references/assets are recommended conventions; additional directories are permitted by the format, not automatically noncompliant. Preserve a cohesive workflow and working relative resource links.

Repository evaluation records and fixtures are not runtime requirements. Keep them outside distributed skill directories. The user's portability requirement additionally excludes project-specific names, summaries and case studies from the generic specification skill; this is a project requirement, not a claimed prohibition in the official format.

Validate format, references, script behavior and distribution separately. Test results do not constitute an official certification or measured model trigger rate. When standards differ, record the source and choose a compatible constraint rather than calling a recommendation a mandatory format rule.
