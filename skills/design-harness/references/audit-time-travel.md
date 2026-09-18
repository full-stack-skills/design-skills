# Design Harness Historical Audit and Time Travel

The journal is not only for recovery. It is also the authoritative history source for explaining how a design run changed over time.

Historical audit always verifies the journal before reading historical state.

## Snapshot at a revision

Read the exact committed run snapshot for one revision:

```bash
python skills/design-harness/scripts/design_harness.py snapshot-at \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --revision 12
```

This returns the full snapshot committed at revision 12.

It does not reconstruct from the current snapshot and does not mutate the run.

If the revision does not exist, the runtime raises `JournalRevisionNotFoundError`.

## Compare revisions

```bash
python skills/design-harness/scripts/design_harness.py diff-revisions \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --from-revision 12 \
  --to-revision 18 \
  --ignore-volatile
```

The response contains structured changes:

```json
{
  "path": "/authorities/baseline",
  "kind": "changed",
  "before": "shell@v2",
  "after": "shell@v3"
}
```

Change kinds:
- `added`
- `removed`
- `changed`

Object changes are recursively reported using JSON Pointer paths.

Lists are treated as one value in V1. This deliberately avoids pretending that list-item identity is known when it may not be.

`--ignore-volatile` currently suppresses:
- `/revision`
- `/updated_at`

This makes semantic diffs easier to read.

## Timeline

```bash
python skills/design-harness/scripts/design_harness.py timeline \
  --store <project>/.design-harness \
  --run-id design_xxx
```

Optional bounds:

```bash
--from-revision 10 --to-revision 25
```

Each row includes:
- revision;
- previous revision;
- event type;
- recorded timestamp;
- event/snapshot hashes;
- cause;
- run state;
- profile ID/version;
- artifact/evidence/dispatch/decision/invalidation counts.

Typical audit question:

> When did this run become APPROVED?

Inspect the timeline or trace `/state`.

## Trace a field/path

Use JSON Pointer syntax:

```bash
python skills/design-harness/scripts/design_harness.py trace-path \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --path /state
```

Other examples:

```text
/authorities/baseline
/correction/reason
/decisions/0/kind
/profile/version
```

The trace returns only revisions where the path's existence or value changed.

That means unchanged revisions do not create audit noise.

A path that did not exist initially is still represented with:

```json
{
  "exists": false,
  "value": null
}
```

This makes “missing → present” transitions explicit.

## Audit questions this supports

### When did approval happen?

```text
trace-path /state
```

Find the row where `value=APPROVED`. The same row includes revision, timestamp, event hash, and cause.

### Which revision changed the baseline?

```text
trace-path /authorities/baseline
```

Then compare the surrounding revisions with `diff-revisions`.

### What changed during a correction?

Use the revision where `/state` enters `CORRECTION`, then compare it with the revision after correction completes.

The diff can reveal:
- invalidated evidence;
- invalidated artifacts;
- correction scope;
- state/cursor changes.

### When did evidence become invalid?

Trace the relevant evidence item's `validity` path if its array index is stable in that historical run, or compare revisions around the correction using `diff-revisions`.

For higher-level evidence identity queries, use stable evidence IDs from the ledger rather than relying on array position.

## Integrity requirement

All historical read operations first verify the journal.

If the chain is invalid:
- `snapshot-at` fails;
- `diff-revisions` fails;
- `timeline` fails;
- `trace-path` fails.

Historical audit must never silently read a tampered chain.

## Read-only rule

Time-travel operations are read-only.

They:
- do not increment run revision;
- do not append journal events;
- do not alter the materialized snapshot;
- do not promote or rollback workflow state.

If a historical finding should cause a correction, start an explicit correction/invalidation flow in the current run.

## Rollback is not time travel

Reading revision 12 does **not** authorize replacing the current run with revision 12.

A business rollback must be represented as a new explicit workflow transition/decision so that history remains append-only.

Never "restore an old revision" by copying its snapshot over the current run JSON.
