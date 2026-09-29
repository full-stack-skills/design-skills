# Navigation Design — Pressure Scenarios

These scenarios are derived from real navigation-drift failures and use generic fixture labels.

## RED-01 — Correcting dynamic sidebar injection without deleting fixed navigation

**Fixture**

- Global domain: Projects
- Fixed domain submenu: Overview / Plan / Milestones / Team / Risks
- Workspace tabs: Overview / Plan / Milestones / Requirements
- Page-local views under Plan: Summary / WBS / Gantt / Resources

**Prompt**

> When I click a workspace tab, internal pages must not be added to the sidebar.

**Observed baseline failure**

The agent over-corrects by removing the already-approved fixed domain submenu entirely.

**Expected behavior with the skill**

Keep the fixed submenu inventory. Forbid dynamic injection from workspace tabs or page-local views. Treat “what exists in the sidebar” separately from “which item is active”.

## RED-02 — Deduplicating by label

**Prompt**

> “Plan” appears in both the fixed domain submenu and workspace tabs. Remove the duplicate.

**Observed baseline failure**

The agent deletes one entry solely because the labels match.

**Expected behavior with the skill**

Do not deduplicate by display text. Compare scope, navigation level, route, context, and responsibility. Same-label entries may be valid when they represent different navigation layers.

## RED-03 — Page-local views replacing workspace tabs

**Prompt**

> The Plan page has Summary / WBS / Gantt / Resources. Make Gantt active.

**Observed baseline failure**

The page-local views replace the workspace tab row.

**Expected behavior with the skill**

Keep the workspace tab inventory and activate Plan at the workspace level. Activate Gantt only inside the Plan page-local view group.

## RED-04 — Inferring activation behavior that was never approved

**Prompt**

> Clicking the Requirements workspace tab should update the page.

**Observed baseline failure**

The agent also changes the sidebar domain and submenu without any approved activation contract.

**Expected behavior with the skill**

Change only behavior defined by the navigation contract. If sidebar activation synchronization is unspecified and materially affects structure or orientation, mark it `needs-decision` instead of inventing a rule.

## GREEN acceptance

A response passes when it outputs:
- navigation inventory by level/scope;
- route and activation rules;
- context propagation and return/deep-link rules;
- explicit invariants that prevent hierarchy drift;
- unresolved activation semantics as decisions, not guesses.
