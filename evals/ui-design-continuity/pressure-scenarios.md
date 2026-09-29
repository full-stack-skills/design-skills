# UI Continuity — Pressure Scenarios

These scenarios cover continuing from an approved product UI baseline.

## RED-01 — Rebuilding the shell while designing the next page

**Prompt**

> Use this approved project overview as the baseline. Design the project plan page. Keep the shell and only replace the workspace content.

**Observed baseline failure**

The agent redraws or restructures the sidebar, changes tab hierarchy, or invents new project-navigation items while producing the new page.

**Expected behavior with the skill**

Partition the baseline into immutable shell, contract-variable regions, and page-local content. Change only the allowed regions.

## RED-02 — Over-interpreting positive feedback

**Prompt**

> This version is better. Continue with the next page.

**Observed baseline failure**

The agent treats every visible label, number, menu item, and interaction in the candidate image as approved product truth.

**Expected behavior with the skill**

Record what was actually approved: visual direction, layout, or a specific interaction. Do not promote incidental or conflicting business semantics without evidence.

## RED-03 — Local feedback causes global redesign

**Prompt**

> Do not put internal page tabs into the sidebar.

**Observed baseline failure**

The agent rewrites unrelated navigation, removes approved fixed submenu items, and changes the shell.

**Expected behavior with the skill**

Create a scoped feedback patch: what changes, what remains invariant, affected artifacts, and regression checks.

## RED-04 — Screenshot conflicts with the authoritative specification

**Prompt**

> The screenshot shows an extra menu item, but the approved registry does not.

**Observed baseline failure**

The agent follows the screenshot because it is the latest visual artifact.

**Expected behavior with the skill**

Use the approved registry for product structure and the screenshot for visual language. If two approved sources conflict, surface the conflict rather than choosing silently.

## GREEN acceptance

A response passes when it:
- names the authoritative baseline and its maturity;
- declares immutable, contract-variable, and page-local regions;
- states an explicit change budget;
- applies feedback only to its intended scope;
- produces a baseline-vs-candidate diff and regression checklist;
- never equates “rendered”, “preferred”, and “approved product contract”.
