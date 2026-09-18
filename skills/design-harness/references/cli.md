# Design Harness CLI

The runtime is pure Python stdlib:

```bash
python skills/design-harness/scripts/design_harness.py --help
```

Store run ledgers inside the target project, for example:

```text
<project>/.design-harness/runs/<run-id>.json
```

Do not store secrets, cookies, tokens, or large binary/base64 artifacts in the ledger. Store stable references and evidence metadata.

## Discover and ensure runs

List compact run summaries:

```bash
python skills/design-harness/scripts/design_harness.py runs \
  --store <project>/.design-harness
```

Find a bounded scope:

```bash
python skills/design-harness/scripts/design_harness.py find-run \
  --store <project>/.design-harness \
  --product-id example \
  --product-version v1 \
  --surface desktop-web \
  --scope-type page \
  --scope-id P01 \
  --profile product-to-ui \
  --active-only
```

Atomically reuse-or-create:

```bash
python skills/design-harness/scripts/design_harness.py ensure-run \
  --store <project>/.design-harness \
  --product-id example \
  --product-version v1 \
  --surface desktop-web \
  --scope-type page \
  --scope-id P01 \
  --profile product-to-ui
```

See [run-discovery.md](run-discovery.md) for ambiguity and authority-drift behavior.

## Discover SOP profiles

```bash
python skills/design-harness/scripts/design_harness.py profiles
python skills/design-harness/scripts/design_harness.py profile --name product-to-ui
```

See [profiles.md](profiles.md) for selection rules.

## Start

```bash
python skills/design-harness/scripts/design_harness.py start \
  --store /path/to/project/.design-harness \
  --product-id example-product \
  --product-version v1 \
  --surface desktop-web \
  --scope-type page \
  --scope-id P01 \
  --profile product-to-ui \
  --authority feature_contract=feature@v1 \
  --authority navigation_contract=navigation@v3 \
  --authority baseline=shell@v2
```

The new run starts in `INIT`. When a profile is selected, the run ledger pins the profile ID/version and copies its ordered stage plan. Required authority bindings are validated before creation.

## Status

```bash
python skills/design-harness/scripts/design_harness.py status \
  --store /path/to/project/.design-harness \
  --run-id design_xxx
```

Use this before any “continue/resume” action.

## Resume with stage evidence

Inline JSON:

```bash
python skills/design-harness/scripts/design_harness.py resume \
  --store /path/to/project/.design-harness \
  --run-id design_xxx \
  --evidence-json '{"stage":"baseline","status":"pass","producer":"product-design","observed_result":"authority refs bound","artifact_ids":[],"input_versions":{},"limitations":[]}'
```

Or load JSON from a file with `@path`:

```bash
--evidence-json @/tmp/evidence.json
```

Generic stage sequence:

```text
baseline
behavior
navigation
task
continuity
candidate
guard
approval-ready
```

Approval and delivery verification use dedicated commands.

## Next action

```bash
python skills/design-harness/scripts/design_harness.py set-next-action \
  --store ... --run-id design_xxx \
  --action-json '{"kind":"skill","target":"navigation-design","required_inputs":["feature@v1"],"expected_evidence":"navigation"}'
```

A run should expose one logical next action.

## Record artifact

```bash
python skills/design-harness/scripts/design_harness.py record-artifact \
  --store ... --run-id design_xxx \
  --artifact-json '{"artifact_id":"P01-render-v1","type":"render","producer":"stitch","input_versions":{"baseline":"shell@v2"},"maturity":"candidate","status":"valid","location":"designs/P01.png","evidence_ids":[]}'
```

Artifact IDs are unique within a run.

## Reconcile unknown outcome

When a write/provider result is unknown, `resume` with `status=unknown` moves the run to `RECONCILING`.

Read-only probe still unresolved:

```bash
python skills/design-harness/scripts/design_harness.py reconcile \
  --store ... --run-id design_xxx \
  --unresolved --note "provider lookup still inconclusive"
```

Resolved successfully:

```bash
python skills/design-harness/scripts/design_harness.py reconcile \
  --store ... --run-id design_xxx \
  --resolved --outcome pass --note "screen exists with expected id"
```

After three unresolved probes the runtime enters `BLOCKED`.

## Scoped correction

```bash
python skills/design-harness/scripts/design_harness.py correct \
  --store ... --run-id design_xxx \
  --affected-state NAVIGATION_READY \
  --reason "Correct sidebar hierarchy only" \
  --artifact-id P01-render-v1
```

The runtime invalidates evidence at/after the affected stage and only the explicitly named artifact IDs. Then provide `correction` stage evidence through `resume`; the run returns to the predecessor of the affected stage so that the affected stage is re-established with fresh evidence.

## Approval

Only valid in `AWAITING_USER_APPROVAL`:

```bash
python skills/design-harness/scripts/design_harness.py approve \
  --store ... --run-id design_xxx \
  --scope page:P01 \
  --actor human
```

The scope must match the run scope unless an explicit expected scope is supplied.

## Delivery verification

Only valid after approval:

```bash
python skills/design-harness/scripts/design_harness.py verify \
  --store ... --run-id design_xxx \
  --evidence-json @/tmp/delivery-evidence.json
```

Delivery evidence must use `stage=delivery`.

## Archive

Only valid in `DELIVERY_VERIFIED`:

```bash
python skills/design-harness/scripts/design_harness.py archive \
  --store ... --run-id design_xxx
```

## Test command

From repository root:

```bash
python -m unittest discover -s skills/design-harness/tests -p 'test_*.py'
```

A passing test run verifies runtime mechanics only. It does not prove an individual product design is correct.


## Batch page-family commands

After a `page-family-batch` parent reaches `BASELINE_BOUND`, spawn page children:

```bash
python skills/design-harness/scripts/design_harness.py spawn-children \
  --store <project>/.design-harness \
  --run-id project-pages-v1 \
  --child-scope-id P01 \
  --child-scope-id P02
```

Inspect aggregate status:

```bash
python skills/design-harness/scripts/design_harness.py batch-status \
  --store <project>/.design-harness \
  --run-id project-pages-v1
```

Approve the whole ready batch:

```bash
python skills/design-harness/scripts/design_harness.py batch-approve \
  --store <project>/.design-harness \
  --run-id project-pages-v1 \
  --actor human
```

See [batch-runs.md](batch-runs.md) for parent/child ownership, failure isolation, and shared-baseline rules.


## Automatic next action and dispatch

Inspect the runtime-computed next action:

```bash
python skills/design-harness/scripts/design_harness.py next-action \
  --store <project>/.design-harness \
  --run-id design_xxx
```

When `kind=dispatch`, issue the specialist handoff:

```bash
python skills/design-harness/scripts/design_harness.py dispatch \
  --store <project>/.design-harness \
  --run-id design_xxx
```

Execute the returned `handler` with the packet's exact inputs. Then bind the result back:

```bash
python skills/design-harness/scripts/design_harness.py complete-dispatch \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --dispatch-id dispatch_xxx \
  --evidence-json @/tmp/evidence.json
```

Do not call `dispatch` when the computed action is a control, human, verification, or done action. See [dispatch-contract.md](dispatch-contract.md).


## Claim and release dispatches

For concurrent Agent/Runner execution:

```bash
python skills/design-harness/scripts/design_harness.py claim-dispatch \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --dispatch-id dispatch_xxx \
  --worker-id worker-a
```

Complete claimed work with the same worker:

```bash
python skills/design-harness/scripts/design_harness.py complete-dispatch \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --dispatch-id dispatch_xxx \
  --worker-id worker-a \
  --evidence-json @/tmp/evidence.json
```

Release unfinished work:

```bash
python skills/design-harness/scripts/design_harness.py release-dispatch \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --dispatch-id dispatch_xxx \
  --worker-id worker-a \
  --reason "worker unavailable"
```

A second worker cannot steal a claimed dispatch. It may claim the dispatch only after an explicit release.


## Heartbeat and expired reclaim

Claims default to a 900-second lease:

```bash
python skills/design-harness/scripts/design_harness.py claim-dispatch \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --dispatch-id dispatch_xxx \
  --worker-id worker-a \
  --lease-seconds 900
```

Renew a long-running claim:

```bash
python skills/design-harness/scripts/design_harness.py heartbeat-dispatch \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --dispatch-id dispatch_xxx \
  --worker-id worker-a \
  --lease-seconds 900
```

After expiry, `next-action` marks the active dispatch reclaimable. Another worker uses the normal `claim-dispatch` command with the same dispatch ID. The runtime records the expired takeover automatically.

Do not try to complete work with an expired lease.


## Run revision conflicts

The JSON returned by `start`, `status`, and mutation commands includes `revision`.

If a concurrent writer commits first, the runtime returns a `RunConflictError`. Treat it as an optimistic-concurrency signal:

1. run `status` again;
2. inspect the new revision/state/`computed_next_action`;
3. decide whether the intended operation is still applicable;
4. issue the operation again from fresh state.

Do not edit the JSON manually to lower the revision and do not force overwrite.

A `RunLockTimeoutError` means the short storage lock could not be acquired before its timeout. It does **not** prove the product/design operation failed. Retry after rereading status.

Run lock files are runtime internals. Only locks older than the configured stale threshold are automatically recovered.
