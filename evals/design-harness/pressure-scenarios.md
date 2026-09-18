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


## RED-08 — Two workers execute the same dispatch

**Prompt**

> Two Agent runners are both available. Let whichever responds fastest handle the current design stage.

**Observed baseline failure**

Both runners receive the same outstanding dispatch and execute it independently. The run may receive duplicate artifacts, provider writes, or conflicting evidence because there is no ownership record.

**Expected behavior with the skill**

A worker explicitly claims the active dispatch. Claiming is idempotent for the same worker and rejected for a different worker. A claimed dispatch can only be completed by its owning worker. The owner may explicitly release it with a reason so another worker can claim it.


## RED-09 — Claimed worker disappears and blocks the run forever

**Prompt**

> Worker A claimed the current design stage and then crashed. Worker B is healthy and available. Continue the design run.

**Observed baseline failure**

The dispatch remains permanently claimed by Worker A. The run cannot progress unless a human manually edits the ledger or discards the dispatch, losing provenance.

**Expected behavior with the skill**

Claims use a bounded lease. The owner sends heartbeats to extend it. Before expiry, another worker cannot steal the dispatch. After expiry, `next-action` exposes the dispatch as reclaimable, a new worker may claim the same dispatch ID, and the ledger records an automatic `lease-expired-reclaim` release receipt. The expired owner cannot complete the dispatch unless it reclaims it.


## RED-10 — Two processes overwrite the same run snapshot

**Prompt**

> Two healthy workers read the same run revision. Worker A records a dispatch claim while Worker B records a different update milliseconds later.

**Observed baseline failure**

Both writers load the same JSON file and use last-write-wins replacement. The later writer silently erases the earlier worker's valid state, evidence, claim, or decision even though dispatch-level semantics were correct.

**Expected behavior with the skill**

Every persisted run has a monotonically increasing `revision`. Writes acquire a short-lived run lock and perform compare-and-swap against the on-disk revision. Exactly one stale-snapshot writer can commit; another receives an explicit `RunConflictError`, reloads the run, and recomputes its action. Atomic replacement prevents partial JSON writes. A stale orphan lock may be recovered only after its bounded lock TTL.


## RED-11 — Lost run ID creates duplicate active design runs

**Prompt**

> Continue yesterday's P01 design. I do not remember the run ID, but the same product/version/surface/page/profile is known.

**Observed baseline failure**

The agent treats missing `run_id` as permission to start another run. Two active runs then diverge on approvals, artifacts, evidence, or baseline.

**Expected behavior with the skill**

Resolve the bounded run identity through the registry. `ensure-run` reuses one unique active match or creates one only when none exists. Multiple active matches raise `RunAmbiguityError`. If explicitly provided authority bindings differ from the existing run, raise `RunAuthorityConflictError` instead of silently reusing or forking.


## RED-12 — Snapshot is lost and the run cannot be reconstructed

**Prompt**

> The materialized run JSON was deleted after a machine crash. Continue the design run without inventing a new run or losing approval/evidence history.

**Observed baseline failure**

The runtime has only the latest snapshot file as durable state. Losing or corrupting it forces manual reconstruction from conversation/files, or creation of a fresh run that breaks provenance.

**Expected behavior with the skill**

Every committed revision is appended to a hash-chained journal. The runtime verifies the chain, replays the latest committed snapshot, and restores the materialized JSON at the exact existing revision without generating a new workflow event. Tampered/invalid journals block replay. A journal/snapshot revision mismatch is reconciled explicitly rather than silently overwritten.


## RED-13 — Audit question is answered from current state only

**Prompt**

> Tell me exactly when this design run became APPROVED, which revision changed the baseline, and what changed during the later correction.

**Observed baseline failure**

The agent inspects only the current materialized snapshot or summarizes conversation memory. It cannot prove which revision introduced the state, which fields changed, or whether an answer came from intact historical evidence.

**Expected behavior with the skill**

Historical inspection verifies the journal, reads exact revision snapshots, generates structured revision diffs, and traces JSON Pointer paths only when their values change. Audit commands are read-only and never restore an old revision over the current run. The answer cites revision numbers, causes, and event hashes from the verified journal history.


## RED-14 — Entity audit depends on array position

**Prompt**

> Which correction invalidated evidence `evidence_abc`? Who executed the dispatch that produced it? Which artifact did that evidence refer to?

**Observed baseline failure**

The agent traces paths such as `/evidence/3/validity` and assumes collection ordering is a durable identity. Insertions/reordering make the audit brittle, and cross-entity provenance must be reconstructed manually from current JSON.

**Expected behavior with the skill**

Audit uses stable IDs for evidence, artifacts, dispatches, decisions, and invalidations. `entity-history` shows only lifecycle changes for the named entity and exposes related invalidation IDs. `provenance` builds explicit relationship edges such as dispatch→evidence, evidence→artifact, and invalidation→evidence/artifact from a verified journal snapshot. Array positions are never the primary entity identity.
