# Design Harness Stable Entity Provenance

Historical JSON Pointer tracing is useful for arbitrary fields, but durable audit questions should use stable entity IDs rather than array positions.

The Harness supports five stable audit entity types:

| Entity type | Collection | Stable ID |
|---|---|---|
| `evidence` | `evidence[]` | `evidence_id` |
| `artifact` | `artifacts[]` | `artifact_id` |
| `dispatch` | `dispatches[]` | `dispatch_id` |
| `decision` | `decisions[]` | `decision_id` |
| `invalidation` | `invalidations[]` | `invalidation_id` |

Do not use an array index such as `/evidence/3/validity` as the primary audit identity when a stable ID exists.

## Entity index

Build a stable-ID index across the verified journal:

```bash
python skills/design-harness/scripts/design_harness.py entity-index \
  --store <project>/.design-harness \
  --run-id design_xxx
```

Each indexed entity includes:

- stable entity ID;
- first revision where it appeared;
- latest revision where it is present;
- last revision where its entity value changed;
- change count;
- latest entity value.

The index is computed from journal history and does not mutate the run.

## Entity history

```bash
python skills/design-harness/scripts/design_harness.py entity-history \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --type evidence \
  --id evidence_xxx
```

The history returns only entity lifecycle changes:

```text
created
changed
removed
```

Each change row includes:

- revision;
- run state;
- journal cause;
- timestamp;
- event hash;
- complete entity value at that revision;
- related invalidation IDs for evidence/artifacts.

This directly supports questions such as:

> Which correction invalidated this evidence?

Find the history row where `validity=invalidated`; the same row exposes the correction cause and related `invalidation_id`.

## Artifact history

Use the same command with `--type artifact`.

Typical lifecycle:

```text
candidate / valid
        ↓
invalidated
```

or, when future artifact promotion APIs mutate the record:

```text
candidate
→ preferred
→ approved-master
→ superseded
```

The audit identity remains `artifact_id`, even if its repository/provider location changes.

## Dispatch history

```bash
... entity-history --type dispatch --id dispatch_xxx
```

This can reconstruct changes such as:

```text
issued
→ claimed(worker-a)
→ issued(released)
→ claimed(worker-b)
→ completed(evidence_xxx)
```

Worker lease, heartbeat, release, reclaim, and resulting evidence metadata remain inside the dispatch entity snapshots.

## Decision and invalidation history

Decisions are queried by `decision_id`, not by `decisions[N]`.

Invalidations are queried by `invalidation_id` and contain the stable evidence/artifact IDs they invalidated.

This makes a correction auditable without depending on collection ordering.

## Provenance graph

Build a relationship graph around one entity:

```bash
python skills/design-harness/scripts/design_harness.py provenance \
  --store <project>/.design-harness \
  --run-id design_xxx \
  --type evidence \
  --id evidence_xxx \
  --max-depth 2
```

The V1 graph is derived from the **latest verified run snapshot**. Historical lifecycle metadata is then attached to each included node.

Current relationship types:

```text
dispatch   --produced-evidence----> evidence
evidence   --mentions-artifact----> artifact
artifact   --supported-by---------> evidence
invalidation --invalidated-evidence--> evidence
invalidation --invalidated-artifact--> artifact
```

Traversal treats edges as bidirectional for reachability, while preserving their semantic direction in output.

Therefore querying an evidence node can still discover the invalidation that points *into* it.

## Graph depth

`--max-depth 0` returns only the root entity.

Example with depth 2:

```text
dispatch_x
   │ produced-evidence
   ▼
evidence_y
   │ mentions-artifact
   ▼
artifact_z
```

Depth bounds prevent an audit query from expanding across an arbitrarily large provenance network.

## Current-snapshot graph vs historical entity history

These two APIs answer different questions.

`entity-history`:

> How did this one stable entity change across revisions?

`provenance`:

> What stable entities are related to this entity in the latest verified run state?

For “what was the graph at revision 12?”, first use `snapshot-at` / historical APIs. A revision-scoped provenance graph can be added later without changing the stable entity model.

## Integrity rule

All entity index/history/provenance operations verify the journal first.

A broken hash/revision chain causes the query to fail with `JournalIntegrityError`.

Do not fall back to the current materialized JSON for historical provenance when journal integrity fails.

## Provenance is evidence, not authority

A relationship proves that two runtime records reference one another. It does not grant one entity authority to rewrite another.

Examples:

- an invalidation referencing an artifact proves that the correction invalidated it;
- an evidence record mentioning an artifact does not make that artifact approved;
- a completed dispatch referencing evidence does not imply user approval.

Promotion/authority rules remain owned by the Harness state machine and product contracts.
