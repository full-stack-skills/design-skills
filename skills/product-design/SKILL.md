---
name: product-design
description: Use when product-design work spans multiple stages or existing design decisions must be continued across requirements, navigation, documentation, visual execution, review, and verification without restarting or duplicating specialist skills.
license: Apache-2.0
---

# Product Design

## Overview

Coordinate product-design work as a staged system. Preserve confirmed decisions, route each unresolved problem to the narrowest specialist skill, and pass explicit contracts downstream instead of re-solving the same problem at every stage.

## When to use this skill

Use when:
- the user asks to design a product, continue a design program, or move from feature definitions into pages;
- multiple design skills are relevant and sequence/ownership matters;
- a prior session already established IA, page baselines, or approved visual direction;
- “continue”, “next page”, or “finish the product design” must resume from existing work rather than restart.

Do not use this skill as a replacement for specialist design, documentation, rendering, implementation, or testing skills.

## How to use this skill

1. **Recover the current state.** Identify approved facts, current stage, completed artifacts, open decisions, and the next unfinished deliverable.
2. **Classify the missing work.**
   - behavior semantics → **REQUIRED SUB-SKILL:** `feature-design`
   - navigation/routes/context → **REQUIRED SUB-SKILL:** `navigation-design`
   - continuation from an approved UI baseline → **REQUIRED SUB-SKILL:** `ui-continuity`
   - documentation suites/PRD/UI docs → use the project’s documentation skill, such as `full-stack-doc`
   - PRD-to-design description translation → use `tui-prd-to-descriptions` when appropriate
   - visual execution → use the selected rendering skill (for example Stitch, Pencil, or `huashu-design`)
   - delivery verification → use the appropriate delivery/testing skills
3. **Protect authority boundaries.** A downstream renderer may propose visuals but may not silently rewrite upstream product contracts.
4. **Build the design task handoff.** Use [references/design-task-contract.md](references/design-task-contract.md) so every stage consumes the same page ID, source versions, constraints, scenario data, and acceptance criteria.
5. **Advance one gate at a time.** Candidate generation, preferred direction, product-contract approval, visual-master approval, implementation verification, and archival are distinct states.
6. **Resume instead of restart.** If the user says “continue”, execute the next approved task unless a missing decision materially blocks it.
7. **Run consistency review before promotion.** Use `design-guard` when several artifacts must agree.

Detailed routing is in [references/workflow.md](references/workflow.md).

## Best Practices

- **Orchestrate; do not duplicate.**
- **Preserve locked decisions until explicitly changed.**
- **Ask only for material blockers.**
- **Keep one canonical identity for page/feature/navigation objects across skills.**
- **Separate proposals from approved facts.**
- **Do not equate rendering success with design approval or implementation completion.**
- **Prefer narrow skills over one giant prompt.**

## Output contract

For the current iteration, return:
- current stage and authority sources;
- completed vs missing decisions;
- specialist skill(s) required next;
- design task contract or handoff;
- explicit human checkpoint when needed;
- next action and promotion gate.

## Keywords

product design workflow, design orchestration, continue design, next page, product design SOP, design handoff, design pipeline, 产品设计, 继续设计, 页面设计流程, 设计编排
