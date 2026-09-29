---
name: ui-design-review
description: Use when product specs, navigation registries, page tasks, prompts, mockups, manifests, or verification evidence may have drifted and a cross-artifact consistency decision is required before promotion or delivery.
license: Apache-2.0
---

# UI Design Review

## Overview

Detect design drift without inventing product authority. Run mechanical checks first where possible, then perform judgment-based review only for relationships automation cannot decide.

## When to use this skill

Use when:
- several design artifacts should express the same menu, page, route, state, or approved baseline;
- generated assets may have drifted from registries/specs;
- a candidate is about to be promoted, archived, or handed to implementation;
- “all files exist” is being mistaken for semantic or visual completion;
- two authoritative-looking sources disagree.

Do not use this skill to choose product behavior, redesign the UI, or silently repair conflicting decisions.

## How to use this skill

**Review boundary:** consume the canonical specification/task versions and the candidate supplied by ui-design-spec or Harness. Author self-checks are input evidence, not this review's conclusion. Return findings and affected artifacts to the caller; do not regenerate the design package, dispatch rendering, restart the product entrypoint or approve the user's decision. A standalone review can run without Harness. A dispatched review returns only its named evidence stage.

1. **Identify authority.** Record artifact type, version, maturity, and the source that is authoritative for each concern.
2. **Run mechanical checks first.** Prefer deterministic comparison for IDs, labels, order, routes, manifest membership, references, schema, and file existence. If no checker exists, report that gap instead of pretending the check ran.
3. **Run semantic checks.** Compare behavior, states, permissions, navigation scope, and acceptance meaning across artifacts.
4. **Run visual-continuity checks after rendering.** Read the theme version and continuity mode/brief. For initial mode compare the candidate with product, navigation and theme constraints, without claiming an approved baseline exists. For inherit/correction compare actual candidate and bound baseline within the change budget. Verify only what available images/screens can establish: shell structure, hierarchy, active state, token family, and obvious content drift.
5. **Separate evidence gates.** File existence, schema validity, semantic consistency, visual approval, runtime behavior, and user approval are independent.
6. **Classify every finding.** Use `PASS`, `FAIL`, `NOT VERIFIED`, or `NEEDS DECISION`.
7. **Do not self-authorize fixes.** Conflicting approved sources become blocking findings with affected downstream artifacts.
8. **Return scoped correction.** Send findings to the caller with affected IDs and earliest invalidated stage: behavior to feature, routes to nav, theme decisions to theme, budget/baseline conflicts to continuity, rendering defects to visual. Harness manages invalidation and re-dispatch; rerun affected checks before promotion.
9. **Publish an actionable report.** Use [references/report-contract.md](references/report-contract.md).

Check categories are in [references/check-catalog.md](references/check-catalog.md).

## Best Practices

- **Authority beats recency.**
- **Automation beats prose for mechanical invariants.**
- **No evidence, no PASS.**
- **A render is not an approval.**
- **A guard detects and scopes; it does not make product decisions.**
- **Every failure names affected downstream artifacts.**
- **Re-run checks after any authoritative source changes.**

## Output contract

Return:
- scope and authority map;
- mechanical-check evidence;
- semantic/visual findings;
- status per finding;
- affected artifacts;
- blocking decisions;
- safe next action.

## Keywords

design guard, consistency review, design lint, navigation drift, spec drift, manifest check, visual baseline, design QA, 设计守卫, 一致性审查, 设计漂移, 菜单一致性
