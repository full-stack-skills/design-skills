---
name: design-harness
description: Use when a multi-step product-design SOP must be executed or resumed across specialist skills, tools, approvals, corrections, and verification with persistent run state and evidence-backed stage gates.
license: Apache-2.0
---

# Design Harness

## Overview

Execute product-design SOPs as resumable, evidence-backed runs. `product-design` decides **what design work is needed**; `design-harness` controls **how that work advances, pauses, resumes, reconciles, and gets promoted** without losing authority or repeating completed stages.

## When to use this skill

Use when:
- a design request spans multiple specialist skills or tools;
- the user says “continue”, “resume”, “next page”, or asks to finish an existing design program;
- page generation, review, approval, and verification must be gated;
- corrections should invalidate only affected downstream artifacts;
- several pages must share one frozen shell/design baseline;
- tool outcomes may be unknown, asynchronous, or insufficient to prove completion.

Do not use for a one-shot visual idea where no persistent workflow, approval, or evidence trail is required.

## Relationship to other skills

- **REQUIRED ROUTER:** use `product-design` to determine the required design stages and specialist skills.
- `feature-design` owns product behavior contracts.
- `navigation-design` owns navigation/route contracts.
- `ui-continuity` owns baseline inheritance and scoped feedback.
- `design-guard` owns cross-artifact consistency review.
- Stitch/Pencil/`huashu-design` and other renderers own visual execution.
- Provider-specific harnesses such as `stitch-delivery-harness` may run as nested execution steps; their provider receipts become evidence in the parent design run.

The harness never redefines those skills' domain rules.

## Core rule

**Only execute the next transition allowed by the run state.**

Run writes use revision-based compare-and-swap under a short-lived file lock. A stale snapshot must fail with a conflict instead of overwriting newer run state.

A successful tool call is evidence for one step, not permission to skip later gates.

## Dispatch execution loop

When the next action is a specialist skill/tool, do not invoke it directly from conversational memory.

1. Run `next-action` to inspect the computed transition.
2. Run `dispatch` to issue an idempotent dispatch packet with exact scope, authority versions, valid upstream evidence/artifacts, handler, expected evidence stage, and stop conditions.
3. In multi-worker environments, claim the dispatch with `claim-dispatch --worker-id ...` before executing it. Claims use a bounded lease (default 900 seconds); a second worker cannot claim an unexpired lease.
4. For long-running work, renew ownership with `heartbeat-dispatch` before the lease expires. If the worker disappears, another worker may reclaim the same dispatch after expiry; the reclaim is recorded in the release ledger.
5. Execute exactly the named handler against that packet.
6. Return the result through `complete-dispatch --dispatch-id ... --worker-id ... --evidence-json ...` when claimed. An expired worker lease cannot complete the dispatch.
7. Only then inspect the next action.

A wrong/stale dispatch ID or wrong evidence stage is rejected. While an active dispatch exists, direct `resume` cannot bypass it. Claimed work can only be completed by the owning worker; use `release-dispatch` with a reason before reassignment.

See [references/dispatch-contract.md](references/dispatch-contract.md).

## Runtime entry

Choose a built-in SOP profile before starting a multi-step run when the task class matches one. The catalog includes `product-to-ui`, `existing-product-next-page`, `page-family-batch`, `design-correction`, `stitch-high-fidelity-delivery`, and `design-to-implementation`. See [references/profiles.md](references/profiles.md).

Use the bundled pure-stdlib runtime for multi-step execution:

```bash
python skills/design-harness/scripts/design_harness.py status --store <project>/.design-harness --run-id <run-id>
```

Before a new run, search the target project's run ledger for the same bounded scope. Existing runs are resumed rather than duplicated. Start new runs with `--profile <id>` when a profile applies. Full commands and payloads are in [references/cli.md](references/cli.md).

## Run lifecycle

1. **Start or resume.** Use the runtime `status`/ledger before creating a new run for the requested scope.
2. **Reconcile authority.** Bind the run to versioned feature, navigation, baseline, and task contracts.
3. **Plan the next transition.** Use `product-design` routing and the state machine in [references/state-machine.md](references/state-machine.md).
4. **Execute one specialist step.** Record its input contract and returned artifact/evidence.
5. **Validate the gate.** Use deterministic checks where possible and `design-guard` for cross-artifact review.
6. **Pause for required human decisions.** Never infer approval from “looks good”, tool success, or an old message.
7. **Promote or correct.** Approval advances maturity; scoped feedback creates a correction path and invalidates only dependent downstream evidence.
8. **Archive only verified final state.** Preserve lineage from source contracts through final assets and receipts.

Use [references/run-contract.md](references/run-contract.md) for persistent state, [references/evidence-contract.md](references/evidence-contract.md) for receipts, [references/dispatch-contract.md](references/dispatch-contract.md) for specialist handoffs, [references/profiles.md](references/profiles.md) for SOP selection, [references/batch-runs.md](references/batch-runs.md) for parent/child page-family orchestration, and [references/cli.md](references/cli.md) for executable commands.

## Hard gates

- No visual execution before required behavior/navigation decisions are either confirmed or explicitly marked as non-blocking assumptions.
- No specialist execution may bypass an outstanding dispatch receipt; dispatch-bound evidence must return through `complete-dispatch`.
- Expired claims are reclaimable, but an expired owner may not submit evidence until it reclaims the dispatch.
- A `RunConflictError` means another writer committed first. Reload the run, inspect `next-action`, and retry the business operation from fresh state; never force-write the stale snapshot.
- Run lock timeout is not evidence that the business operation failed. Do not delete an unexpired lock or overwrite the ledger.
- No candidate promotion while `design-guard` has blocking `FAIL` or `NEEDS DECISION` findings.
- No user-approval state without explicit approval for the named scope.
- No implementation/delivery verification claim from design-render evidence alone.
- Unknown write/tool outcome enters `RECONCILING`; do not blindly retry.
- A change to an authoritative upstream contract invalidates all dependent downstream evidence.
- Parallel page work must pin the same shared baseline version when continuity is required.
- `page-family-batch` parents own only the shared baseline and aggregate decisions; page-level task/continuity/render/guard stages belong to child runs.

## Correction behavior

For feedback such as “only fix the sidebar”:
1. record a scoped feedback patch through `ui-continuity`;
2. compute affected artifacts;
3. preserve unaffected approved stages;
4. invalidate dependent candidates/guard receipts only;
5. regenerate the minimum scope;
6. re-run affected gates;
7. return to the prior promotion path.

Do not restart the whole design program.

## Stop conditions

Stop and report current run state when:
- an authority conflict requires a product decision;
- explicit user approval is required;
- provider outcome is unknown and reconciliation is incomplete;
- required evidence/tooling is unavailable;
- a blocking guard finding remains;
- the requested action would skip a stage gate.

Return: `run_id`, current state, completed gates, blocked/invalidated gates, next allowed action, and evidence required. When the runtime is available, derive these fields from the persisted ledger rather than reconstructing them from conversation memory.

## Output contract

For every harness turn, report:
- run identity and scope;
- current state;
- authoritative contract versions;
- newly consumed evidence;
- transition executed or refused;
- invalidated downstream artifacts, if any;
- next allowed action;
- whether human input is required.

## Keywords

design harness, design SOP, resumable design workflow, design run, stage gate, evidence, approval, reconcile, correction, design orchestration, 设计编排, 设计流水线, 设计状态机, 设计闭环
