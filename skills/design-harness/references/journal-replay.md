# Design Harness Journal, Replay, and Recovery

The Design Harness persists each run in two complementary forms:

```text
<store>/runs/<run-id>.json
<store>/runs/<run-id>.events.jsonl
```

- `<run-id>.json` is the **materialized current snapshot**.
- `<run-id>.events.jsonl` is the **append-only commit journal**.

The runtime materializes the snapshot on every successful revision, which is stricter than periodic checkpointing. The journal exists for auditability, integrity checks, replay, and recovery.

## Journal event

Every successful CAS commit appends one JSONL event containing:

- journal schema version;
- event ID/type;
- run ID;
- committed revision;
- previous revision;
- recorded timestamp;
- previous event hash;
- snapshot hash;
- full committed snapshot;
- cause derived from the latest run history event;
- event hash.

The first native journal event for a new run is:

```text
event_type = run.created
revision = 1
previous_revision = 0
previous_event_hash = null
```

Later commits use `run.updated`.

For runs created before journal support, the first later write creates a `run.journal-bootstrap` event from the existing materialized revision before appending the new revision.

## Hash chain

Each event stores:

```text
previous_event_hash
snapshot_hash
event_hash
```

`snapshot_hash` hashes the canonical JSON representation of the committed run snapshot.

`event_hash` hashes the canonical event payload excluding `event_hash` itself.

Verification checks:

- journal JSON syntax;
- run ID consistency;
- positive revisions;
- contiguous revisions;
- previous-revision linkage;
- previous-event-hash linkage;
- snapshot revision;
- snapshot hash;
- event hash.

This detects accidental corruption and ordinary tampering with an existing chain.

**Important:** this is integrity detection, not cryptographic authenticity. An attacker who can rewrite the entire journal and recompute every hash can forge a new chain. Signed/WORM external audit storage is a separate higher-assurance layer.

## Verify

```bash
python skills/design-harness/scripts/design_harness.py verify-journal \
  --store <project>/.design-harness \
  --run-id design_xxx
```

Example successful result:

```json
{
  "valid": true,
  "event_count": 18,
  "latest_revision": 18,
  "errors": []
}
```

A journal with any integrity error must not be replayed by default.

## Journal summary

```bash
python skills/design-harness/scripts/design_harness.py journal \
  --store <project>/.design-harness \
  --run-id design_xxx
```

The summary reports:
- journal path;
- validity;
- event count;
- latest revision;
- latest event hash;
- errors.

## Replay

```bash
python skills/design-harness/scripts/design_harness.py replay-run \
  --store <project>/.design-harness \
  --run-id design_xxx
```

Replay verifies the complete chain and returns the last committed snapshot.

The current V1 journal intentionally stores the full committed snapshot in every event. This makes replay deterministic and recovery simple while the workflow schema is still evolving. A future compact event/delta format may be added only with migration and replay-equivalence tests.

## Recover materialized snapshot

If `<run-id>.json` is deleted or corrupted:

```bash
python skills/design-harness/scripts/design_harness.py recover-run \
  --store <project>/.design-harness \
  --run-id design_xxx
```

Recovery:

1. verifies the journal;
2. replays the latest committed snapshot;
3. acquires the normal per-run write lock;
4. refuses recovery if the materialized snapshot has a **newer revision** than the journal;
5. atomically rewrites the materialized snapshot;
6. preserves the replayed revision exactly;
7. does **not** append another journal event.

Recovery is repair of the materialized view, not a new business/workflow mutation.

## Commit ordering

During a normal save, under the per-run write lock:

```text
CAS revision check
 -> verify journal revision agrees with snapshot revision
 -> build next committed snapshot
 -> append + fsync journal event
 -> atomic replace materialized snapshot
```

Journal-first commit ordering means that if the process crashes after the journal append but before snapshot replacement, the committed revision is still recoverable.

A future write that finds journal revision ahead of the materialized snapshot raises `JournalRecoveryError` and requires recovery before continuing. It must not append a duplicate revision.

## CAS failures do not journal

A stale writer fails its revision compare before creating the next event.

Therefore:

```text
RunConflictError
=> no new journal revision
=> no overwritten snapshot
```

The caller reloads the run and recomputes its operation.

## Audit questions

The journal can answer:

- which revision introduced this state?
- what was the complete run snapshot at revision N?
- what transition/history cause was associated with the commit?
- did a stale writer overwrite newer state? (it should not)
- is the current snapshot reproducible from the journal?
- can a lost/corrupt snapshot be restored?

Detailed “who executed the skill?” provenance remains in the snapshot's dispatch, worker, decision, evidence, invalidation, and history ledgers and is therefore included in each committed journal snapshot.

## Operational guidance

- Keep the journal in the same local durability boundary as the run snapshot unless an external audit store is configured.
- Never manually truncate the journal to solve a revision mismatch.
- Never edit a past journal event in place.
- Back up snapshot and journal together.
- For regulated/strong-audit environments, mirror journal events to an external append-only or signed store.
