# Design Harness Dispatch Contract

A dispatch is the executable handoff between the Harness runtime and one specialist skill/tool. It binds one run state, one handler, one exact input snapshot, and one expected evidence contract.

## Standard loop

```text
next-action
  -> dispatch
  -> execute handler
  -> complete-dispatch
  -> state transition
  -> next-action
```

Do not call the specialist first and reconstruct evidence afterward.

## Inspect next action

```bash
python skills/design-harness/scripts/design_harness.py next-action \
  --store <project>/.design-harness \
  --run-id design_xxx
```

Possible action kinds:

- `dispatch`: execute a specialist skill/tool;
- `control`: Harness operation such as reconcile, spawn-children, batch-status, archive;
- `human`: explicit approval/decision gate;
- `verification`: delivery/runtime verification;
- `done`: no further automatic transition.

## Issue a dispatch

```bash
python skills/design-harness/scripts/design_harness.py dispatch \
  --store <project>/.design-harness \
  --run-id design_xxx
```

Issuing is idempotent while a dispatch is outstanding. Repeating the command returns the same active `dispatch_id`; it does not create a second execution lease.

A dispatch packet contains:

```json
{
  "contract_version": 1,
  "dispatch_id": "dispatch_xxx",
  "run_id": "design_xxx",
  "profile": {
    "id": "product-to-ui",
    "version": 1
  },
  "state_at_issue": "BASELINE_BOUND",
  "stage_cursor": 1,
  "handler": "feature-design",
  "evidence_stage": "behavior",
  "target_state": "BEHAVIOR_READY",
  "scope": "page:P01",
  "inputs": {
    "product_id": "example",
    "product_version": "v1",
    "surface": "desktop-web",
    "scope_type": "page",
    "scope_ids": ["P01"],
    "scope": "page:P01",
    "authorities": {},
    "authority_versions": {},
    "valid_artifact_ids": [],
    "valid_evidence_ids": [],
    "parent_run_id": null,
    "shared_baseline": null
  },
  "expected_evidence": {
    "stage": "behavior",
    "allowed_statuses": [
      "fail",
      "needs-decision",
      "pass",
      "unknown"
    ]
  },
  "stop_conditions": [
    "blocking-finding",
    "needs-decision",
    "unknown-provider-outcome",
    "human-approval-required"
  ],
  "status": "issued",
  "worker_id": null,
  "claimed_at": null,
  "releases": []
}
```

The packet is a contract, not a suggestion. The handler must not silently switch product scope, source versions, or expected evidence stage.

## Execute the handler

Use the `handler` literally when it names a registered specialist skill, for example:

- `feature-design`
- `navigation-design`
- `ui-continuity`
- `design-guard`
- `product-design`
- `stitch-delivery-harness`

A generic handler such as `renderer` means the current design task must select the configured renderer without changing upstream product contracts.

The specialist should consume:
- exact scope;
- authority versions;
- valid upstream evidence;
- valid artifacts;
- parent/shared-baseline context when present.

## Complete the dispatch

Create evidence for the execution:

```json
{
  "stage": "behavior",
  "status": "pass",
  "producer": "feature-design",
  "observed_result": "feature contract v3 confirmed",
  "artifact_ids": ["feature-contract-v3"],
  "input_versions": {
    "requirements": "req@v5"
  },
  "limitations": []
}
```

Return it through:

```bash
python skills/design-harness/scripts/design_harness.py complete-dispatch \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --dispatch-id dispatch_xxx \
  --evidence-json @/tmp/evidence.json
```

The runtime binds the evidence to that dispatch.

## Validation rules

`complete-dispatch` rejects:
- a stale/wrong dispatch ID;
- a dispatch that is no longer `issued`;
- evidence for the wrong stage;
- unsupported evidence status.

While a dispatch is active, direct `resume` cannot bypass it unless the evidence carries that exact dispatch ID.

## Dispatch completion statuses

| Evidence status | Dispatch status | Run effect |
|---|---|---|
| `pass` | `completed` | advance to target state |
| `unknown` | `unknown` | enter `RECONCILING` |
| `fail` | `blocked` | enter `BLOCKED` |
| `needs-decision` | `blocked` | enter `BLOCKED` |

The dispatch ledger retains historical receipts even after the active dispatch is cleared.

## Control and human actions

Not every next action becomes a dispatch.

Examples:
- `RECONCILING` → `control/reconcile`
- batch parent after baseline → `control/spawn-children`
- batch in progress → `control/batch-status`
- `AWAITING_USER_APPROVAL` → `human/approve`
- `APPROVED` → `verification/verify`
- `DELIVERY_VERIFIED` → `control/archive`

Calling `dispatch` for these states fails intentionally.

## Evidence provenance

The dispatch record stores the resulting `evidence_id`. This creates the trace:

```text
run
 -> dispatch
 -> handler/input snapshot
 -> evidence
 -> state transition
 -> next dispatch
```

This trace is the minimum provenance needed to resume a design SOP without relying on conversation memory.

## Safety and authority

- Do not include credentials, cookies, tokens, or binary/base64 assets in dispatch inputs.
- Stable repository/provider references are preferred over copied large payloads.
- A dispatch never grants a specialist authority to rewrite upstream contracts.
- A changed authority invalidates dependent downstream evidence according to the run invalidation rules.


## Worker claim protocol

For a single in-process Agent, a dispatch may be completed while still `issued`. For multiple Agents/Runners, claim the dispatch before execution.

Claim:

```bash
python skills/design-harness/scripts/design_harness.py claim-dispatch \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --dispatch-id dispatch_xxx \
  --worker-id worker-a
```

Claim behavior:
- `issued -> claimed`;
- stores `worker_id` and `claimed_at`;
- repeating the claim from the same worker is idempotent;
- another worker is rejected.

A claimed dispatch must be completed by the same worker:

```bash
python skills/design-harness/scripts/design_harness.py complete-dispatch \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --dispatch-id dispatch_xxx \
  --worker-id worker-a \
  --evidence-json @/tmp/evidence.json
```

To hand work back before completion:

```bash
python skills/design-harness/scripts/design_harness.py release-dispatch \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --dispatch-id dispatch_xxx \
  --worker-id worker-a \
  --reason "worker shutting down"
```

Release behavior:
- verifies ownership;
- appends a release receipt with worker/reason/time;
- clears `worker_id` / `claimed_at`;
- returns the dispatch to `issued`;
- keeps the same `dispatch_id` so provenance is not fragmented.

After release, another worker may claim the same dispatch.

## In-flight next action

While an active dispatch is `issued` or `claimed`, `next-action` returns `kind=inflight` instead of constructing another stage dispatch. It includes:
- active `dispatch_id`;
- dispatch status;
- worker ID when claimed;
- handler;
- evidence stage;
- target state.

This prevents resume/re-entry flows from mistaking already-dispatched work for new work.


## Worker lease and heartbeat

A worker claim is a **lease**, not permanent ownership.

Default claim:

```bash
python skills/design-harness/scripts/design_harness.py claim-dispatch \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --dispatch-id dispatch_xxx \
  --worker-id worker-a
```

The default lease is 900 seconds. Override it when necessary:

```bash
--lease-seconds 300
```

A claimed dispatch records:
- `lease_seconds`;
- `lease_expires_at`;
- `heartbeats[]`.

For long-running work, the owner renews its lease:

```bash
python skills/design-harness/scripts/design_harness.py heartbeat-dispatch \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --dispatch-id dispatch_xxx \
  --worker-id worker-a \
  --lease-seconds 900
```

Heartbeat rules:
- only the current worker may heartbeat;
- an expired lease cannot be revived by heartbeat;
- each heartbeat records previous/new expiry;
- heartbeat changes ownership time only, never the dispatch identity or input contract.

### Expired reclaim

If the worker disappears and the lease expires, `next-action` returns a control action with:

```text
kind = control
operation = claim-dispatch
lease_expired = true
previous_worker_id = <old worker>
```

Another worker may then call `claim-dispatch` on the **same dispatch ID**.

Reclaim:
- records a release receipt with reason `lease-expired-reclaim`;
- records `reclaimed_by`;
- assigns a fresh lease to the new worker;
- preserves all original dispatch provenance.

An expired owner cannot call `complete-dispatch`. It must first reclaim the dispatch if nobody else owns it.

This avoids two unsafe outcomes: permanent orphaned work and silent duplicate execution.
