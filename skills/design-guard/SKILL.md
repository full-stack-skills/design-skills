---
name: design-guard
description: Use when product specs, navigation registries, page tasks, prompts, mockups, manifests, or verification evidence may have drifted and a cross-artifact consistency decision is required before promotion or delivery.
license: Apache-2.0
---

# Design Guard

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

1. **Identify authority.** Record artifact type, version, maturity, and the source that is authoritative for each concern.
2. **Run mechanical checks first.** Prefer deterministic comparison for IDs, labels, order, routes, manifest membership, references, schema, and file existence. If no checker exists, report that gap instead of pretending the check ran.
3. **Run semantic checks.** Compare behavior, states, permissions, navigation scope, and acceptance meaning across artifacts.
4. **Run visual-continuity checks.** Verify only what available images/screens can establish: shell structure, hierarchy, active state, token family, and obvious content drift.
5. **Separate evidence gates.** File existence, schema validity, semantic consistency, visual approval, runtime behavior, and user approval are independent.
6. **Classify every finding.** Use `PASS`, `FAIL`, `NOT VERIFIED`, or `NEEDS DECISION`.
7. **Do not self-authorize fixes.** Conflicting approved sources become blocking findings with affected downstream artifacts.
8. **Publish an actionable report.** Use [references/report-contract.md](references/report-contract.md).

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
