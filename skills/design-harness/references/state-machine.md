# Design Harness State Machine

The state names are generic. A project may omit non-applicable stages, but it must not silently skip required gates.

## Primary states

| State | Meaning | Required evidence to leave |
|---|---|---|
| `INIT` | Run created or recovered | scope + authority inventory |
| `BASELINE_BOUND` | Product/version/page identity and source contracts bound | versioned authority refs |
| `BEHAVIOR_READY` | Required feature behavior is resolved | feature contract or explicit non-blocking assumption |
| `NAVIGATION_READY` | Required navigation behavior is resolved | navigation contract |
| `TASK_READY` | Design task contract is complete | page/task contract |
| `CONTINUITY_READY` | Baseline/change budget is resolved when applicable | continuity contract |
| `CANDIDATE_READY` | A visual/editable candidate exists | provider/render receipt |
| `GUARD_REVIEWED` | Required structural/semantic/visual checks ran | design-guard report |
| `AWAITING_USER_APPROVAL` | Automatic gates passed; human decision required | candidate + review evidence presented |
| `APPROVED` | User approved the named scope | explicit approval receipt |
| `DELIVERY_VERIFIED` | Required delivery/runtime checks passed | test/delivery evidence |
| `ARCHIVED` | Final lineage and artifacts recorded | immutable/archive receipt |

## Control states

| State | Use when |
|---|---|
| `RECONCILING` | provider/write outcome is unknown or duplicate execution is possible |
| `BLOCKED` | authority conflict, unavailable required evidence, or blocking guard failure |
| `CORRECTION` | explicit scoped feedback requires partial regeneration |
| `CANCELLED` | user cancels the run |

## Typical transitions

```text
INIT
  -> BASELINE_BOUND
  -> BEHAVIOR_READY
  -> NAVIGATION_READY
  -> TASK_READY
  -> CONTINUITY_READY
  -> CANDIDATE_READY
  -> GUARD_REVIEWED
  -> AWAITING_USER_APPROVAL
  -> APPROVED
  -> DELIVERY_VERIFIED
  -> ARCHIVED
```

A stage may be marked `not-applicable` only with a recorded reason.

## Correction transition

```text
CANDIDATE_READY / GUARD_REVIEWED / APPROVED
  -> CORRECTION
  -> invalidate affected downstream evidence
  -> resume at earliest affected state
```

Example: a page-local visual spacing correction may resume at `CONTINUITY_READY`; a navigation rule change resumes no later than `NAVIGATION_READY` and invalidates later candidate/guard/approval evidence.

## Reconciliation transition

Unknown provider result:

```text
ANY_EXECUTION_STATE
  -> RECONCILING
  -> read-only inspection / receipt lookup
  -> resolved previous state or next state
  -> BLOCKED after bounded failed reconciliation
```

Never retry an unknown write merely because a timeout occurred.

## Approval scope

Approval must name what was approved:
- visual direction;
- one page candidate;
- shared shell/baseline;
- navigation contract;
- product behavior;
- final delivery.

Approval of one scope does not imply another.
