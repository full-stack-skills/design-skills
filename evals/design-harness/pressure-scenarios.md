# Design Harness — Pressure Scenarios

These scenarios capture orchestration failures that happen when a design SOP has multiple skills, tools, checkpoints, and artifacts but no persistent run contract.

## RED-01 — Re-running from the beginning

**Prompt**

> Continue the existing design run. Feature and navigation contracts are approved, the UI baseline is selected, and the next step is rendering the next page.

**Observed baseline failure**

The agent restarts discovery, rewrites already-approved artifacts, or creates a duplicate design run because there is no persistent run state.

**Expected behavior with the skill**

Resume the existing run from its latest verified state. Preserve approved artifacts and execute only the next allowed transition.

## RED-02 — Tool success bypasses gates

**Prompt**

> Stitch returned success and the image looks fine. Mark the page complete and continue to implementation.

**Observed baseline failure**

The agent treats provider success and a visual impression as sufficient evidence for completion.

**Expected behavior with the skill**

Record provider output as evidence for the relevant stage only. Require semantic/continuity review, user approval where configured, and any required delivery verification before promotion.

## RED-03 — Multiple skills disagree on authority

**Prompt**

> Navigation says one tab order, the latest render shows another, and the continuity brief copied the render. Continue.

**Observed baseline failure**

The agent chooses the newest artifact or whichever is easiest, silently propagating drift.

**Expected behavior with the skill**

Pause the run in a blocked/needs-decision state, identify the authoritative source and affected artifacts, and do not advance until the conflict is resolved.

## RED-04 — Local feedback mutates completed stages

**Prompt**

> Keep everything else. Fix only the sidebar issue and regenerate the page.

**Observed baseline failure**

The agent reopens feature design, rewrites navigation, or changes unrelated shell decisions.

**Expected behavior with the skill**

Create a scoped correction branch within the current run, invalidate only affected downstream evidence, regenerate only the necessary artifacts, then re-run dependent gates.

## RED-05 — “Continue” without evidence provenance

**Prompt**

> Continue from yesterday.

**Observed baseline failure**

The agent cannot tell which outputs were actually approved versus merely generated, and guesses the next step.

**Expected behavior with the skill**

Read the run ledger: artifact IDs, maturity, approvals, evidence, invalidations, and next allowed action. If provenance is incomplete, stop at reconciliation rather than guessing.

## RED-06 — Parallel page work causes shared-baseline drift

**Prompt**

> Generate three pages in parallel using the same shell.

**Observed baseline failure**

Each page independently reconstructs the shell and produces slightly different menus, tabs, or tokens.

**Expected behavior with the skill**

Freeze a shared baseline version, give every page task the same immutable contract, and prevent promotion if a page deviates from the shared baseline.

## GREEN acceptance

A response passes when it:
- models a persistent design run rather than a one-shot prompt;
- has explicit states and allowed transitions;
- records artifacts, evidence, approvals, and invalidations;
- distinguishes generation success from promotion;
- can resume, reconcile, block, correct, and continue deterministically;
- delegates specialist decisions to existing skills instead of duplicating them.


## RED-07 — Profile stage is known but execution bypasses dispatch receipt

**Prompt**

> The run says the next handler is navigation-design. Call it, then continue.

**Observed baseline failure**

The agent directly invokes the specialist skill and later submits an unbound success summary. The run has no stable dispatch ID, no exact input snapshot, no expected evidence contract, and no way to prove which execution produced the evidence.

**Expected behavior with the skill**

Use `next-action` to inspect the computed action, `dispatch` to issue one idempotent dispatch packet, execute the named handler with that packet's exact inputs, and return through `complete-dispatch` with evidence bound to the active dispatch ID. A mismatched/stale dispatch or wrong evidence stage must be rejected.
