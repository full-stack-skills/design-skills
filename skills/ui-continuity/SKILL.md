---
name: ui-continuity
description: Use when continuing, extending, or correcting a UI from an approved screen, shell, design system, or page family and only part of the interface is allowed to change.
license: Apache-2.0
---

# UI Continuity

## Overview

Continue a product UI by inheriting approved decisions and declaring a change budget. A new page is not permission to redesign the surrounding product, and local feedback is not permission to rewrite unrelated contracts.

## When to use this skill

Use when:
- the user says “continue”, “next page”, “based on this”, “keep the shell”, or “only replace the content area”;
- a page family already has an approved baseline;
- a generated candidate must preserve navigation, project/context headers, design tokens, or component language;
- feedback should patch one problem without causing global drift.

Do not use when there is no approved baseline and the task is open-ended visual exploration; use an appropriate design exploration skill instead.

## How to use this skill

1. **Identify the baseline and maturity.** Distinguish candidate, preferred direction, approved visual master, approved product contract, and implementation screenshot.
2. **Resolve authority.** Product structure comes from approved specs/registries; visual language comes from the approved visual baseline. If two approved sources conflict, stop and surface the conflict.
3. **Partition the UI.**
   - `immutable`: regions that must remain structurally consistent;
   - `contract-variable`: defined changes such as active tab, breadcrumb position, or live values;
   - `page-local`: the target page content that may be redesigned.
4. **Declare a change budget.** State exactly what this iteration may change and what it must preserve.
5. **Apply the target spec.** Use the current feature/navigation contracts; do not copy accidental business semantics from the reference image.
6. **Compare baseline and candidate.** Produce a structural/visual diff before promoting the result.
7. **Scope feedback.** Convert user feedback into a patch: change, preserve, affected artifacts, and regression checks.
8. **Promote deliberately.** “Looks better” can approve a direction without approving every visible business rule.

Use [references/continuity-contract.md](references/continuity-contract.md) and [references/feedback-protocol.md](references/feedback-protocol.md).

## Best Practices

- **Inherit before inventing.**
- **Freeze structure, not live data.** Dynamic values may change while shell identity remains stable.
- **Preserve confirmed advantages during correction.**
- **Do not let a screenshot override an approved registry.**
- **Do not treat render success as product approval.**
- **Keep feedback local unless the user explicitly broadens scope.**

Actual prototype generation may be handed to `huashu-design`, Stitch, Pencil, or another rendering skill after the continuity brief is established.

## Output contract

Return:
- baseline and authority sources;
- immutable / contract-variable / page-local map;
- change budget;
- candidate diff;
- scoped feedback patch when applicable;
- regression checklist;
- unresolved conflicts.

Read [references/anti-patterns.md](references/anti-patterns.md) before finalizing.

## Keywords

UI continuity, shell preservation, design baseline, next page, approved master, scoped feedback, change budget, visual regression, 页面连续性, 固定 Shell, 基线, 局部修改
