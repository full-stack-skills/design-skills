---
name: ui-design-continuity
description: Define pre-render constraints for first-page design, inheritance from an approved UI baseline, or scoped correction. Record baseline maturity and allowed changes; compare actual candidates after rendering through ui-design-review.
license: Apache-2.0
---

# UI Design Continuity

## Overview

Continue a product UI by inheriting approved decisions and declaring a change budget. A new page is not permission to redesign the surrounding product, and local feedback is not permission to rewrite unrelated contracts.

## When to use this skill

Use when:
- the user says “continue”, “next page”, “based on this”, “keep the shell”, or “only replace the content area”;
- a page family already has an approved baseline;
- a generated candidate must preserve navigation, project/context headers, design tokens, or component language;
- feedback should patch one problem without causing global drift.

For first-page design, use initial mode to define constraints without inventing a visual baseline. Visual exploration itself belongs to ui-design-visual.

## How to use this skill

1. **Choose the pre-render mode.** `initial`: no approved visual baseline; record `baseline_id: null`, confirmed product/navigation constraints, theme reference, allowed visual exploration and unresolved decisions. `inherit`: bind the exact approved baseline version. `correction`: bind the current candidate and scoped feedback, preserving its actual maturity. Initial mode does not approve any visual output.
2. **Identify the baseline and maturity.** Distinguish candidate, preferred direction, approved visual master, approved product contract, and implementation screenshot.
3. **Resolve authority.** Product structure comes from approved specs/registries; visual language comes from the approved visual baseline. If two approved sources conflict, stop and surface the conflict.
4. **Partition the UI.**
   - `immutable`: regions that must remain structurally consistent;
   - `contract-variable`: defined changes such as active tab, breadcrumb position, or live values;
   - `page-local`: the target page content that may be redesigned.
5. **Declare a change budget.** State exactly what this iteration may change and what it must preserve.
6. **Apply the target spec.** Use the current feature/navigation contracts; do not copy accidental business semantics from the reference image.
7. **Prepare post-render checks.** Before rendering, return the expected comparisons, not a fabricated candidate diff. After rendering, ui-design-review compares the candidate against these constraints; initial mode checks product/theme constraints without claiming inheritance from an absent visual master.
8. **Scope feedback.** Convert user feedback into a patch: change, preserve, affected artifacts, and regression checks.
9. **Promote deliberately.** “Looks better” can approve a direction without approving every visible business rule.

Use [references/continuity-contract.md](references/continuity-contract.md) and [references/feedback-protocol.md](references/feedback-protocol.md).

## Best Practices

- **Inherit before inventing.**
- **Freeze structure, not live data.** Dynamic values may change while shell identity remains stable.
- **Preserve confirmed advantages during correction.**
- **Do not let a screenshot override an approved registry.**
- **Do not treat render success as product approval.**
- **Keep feedback local unless the user explicitly broadens scope.**

When dispatched, return only the continuity/correction preflight artifact and evidence for the same run/dispatch. A completed initial preflight can return `pass`; it proves constraints are ready, not visual approval. Unresolved blocking decisions return `needs-decision`. Do not start a renderer or another run inside the dispatch.

For standalone requests, actual prototype generation may be handed to `ui-design-visual`, Stitch, Pencil, or another rendering skill after the continuity brief is established.

## Output contract

Return:
- baseline and authority sources;
- immutable / contract-variable / page-local map;
- change budget;
- post-render comparison criteria; actual candidate diff only when a candidate exists;
- scoped feedback patch when applicable;
- regression checklist;
- unresolved conflicts.

Read [references/anti-patterns.md](references/anti-patterns.md) before finalizing.

## Keywords

UI continuity, shell preservation, design baseline, next page, approved master, scoped feedback, change budget, visual regression, 页面连续性, 固定 Shell, 基线, 局部修改
