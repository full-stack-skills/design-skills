# Design Harness Authority Impact Analysis

Authority Impact Analysis answers a cross-run question:

> Which active design runs and runtime entities still depend on this exact authority version?

It is deliberately **read-only**. Detecting dependency does not authorize mutation.

## Supported authority references

The analyzer inspects the latest **verified journal snapshot** for every materialized run and matches:

- direct run bindings under `authorities.<key>`;
- `shared_baseline` when `key=baseline`;
- Evidence `input_versions.<key>`;
- Artifact `input_versions.<key>`;
- Dispatch `inputs.authority_versions.<key>`.

The result therefore covers both the run-level contract and downstream execution records that explicitly consumed that contract version.

## Analyze one authority version

```bash
python skills/design-harness/scripts/design_harness.py authority-impact \
  --store <project>/.design-harness \
  --key baseline \
  --value shell@v2
```

By default terminal runs are excluded.

Use `--include-terminal` only when auditing historical/archived impact rather than planning active work.

## Result

Each affected run includes:

- run ID and revision;
- state/scope/profile;
- parent/shared-baseline metadata;
- `binding_paths`;
- affected Evidence IDs;
- affected Artifact IDs;
- affected Dispatch IDs.

Example:

```json
{
  "run_id": "page-P01",
  "revision": 18,
  "binding_paths": [
    "/authorities/baseline"
  ],
  "affected_entities": {
    "evidence": ["evidence_a"],
    "artifact": ["artifact_a"],
    "dispatch": ["dispatch_a"]
  }
}
```

## Integrity completeness

Every candidate run's journal is verified before it contributes to the report.

If any run cannot be verified, the analyzer records a diagnostic such as:

```text
run_id = page-P02
error = JournalIntegrityError
```

and returns:

```text
complete = false
```

An incomplete impact analysis must not be interpreted as “these are all affected runs”.

Do not silently fall back to a possibly stale/corrupt materialized snapshot.

## Plan an authority change

```bash
python skills/design-harness/scripts/design_harness.py plan-authority-change \
  --store <project>/.design-harness \
  --key baseline \
  --from shell@v2 \
  --to shell@v3
```

The planner wraps the read-only impact analysis and adds a recommended earliest revalidation state per affected run.

Current generic recommendations:

| Authority key | Recommended affected state |
|---|---|
| `feature_contract` | `BEHAVIOR_READY` |
| `navigation_contract` | `NAVIGATION_READY` |
| `design_task` | `TASK_READY` |
| `baseline` | `CONTINUITY_READY` |
| `approved_design` | `GUARD_REVIEWED` |

Special case:

`page-family-batch` parent + `baseline` change starts at `BASELINE_BOUND`, because the parent owns the family-level shared baseline itself.

Unknown authority keys conservatively recommend `TASK_READY`.

## Deterministic plan ID

The planner derives `plan_id` from:

- authority key;
- old/new values;
- include-terminal flag;
- affected run IDs/revisions;
- recommended affected states;
- binding paths;
- affected entity IDs;
- diagnostics/completeness.

The generation timestamp is **not** part of the plan hash.

Therefore repeating the planner against unchanged store state yields the same `plan_id`.

Any relevant run revision or dependency change produces a new plan ID.

## Read-only contract

A plan always returns:

```text
applied = false
```

It does not:

- change `authorities`;
- invalidate Evidence;
- invalidate Artifacts;
- create Corrections;
- rewrite child runs;
- rebind a shared baseline;
- advance/rewind any state.

Why: cross-run mutation needs an explicit change-set/transaction workflow. Impact detection alone is not sufficient authority.

## Recommended next action

For each run impact:

```text
required_action = explicit-correction-or-migration
```

Use the plan as input to a later explicit operation that can:

1. confirm the intended authority migration;
2. lock the expected run revisions;
3. update authority bindings;
4. invalidate only dependent downstream evidence/artifacts;
5. re-enter each run at its recommended affected state;
6. retain a complete journal/audit trail.

Until such an operation is explicitly approved and executed, the impact plan remains analysis only.

## Parent / child runs

Because child page runs inherit their own authority bindings, a shared-baseline search naturally finds:

- the page-family parent;
- every child still bound to the old baseline;
- each child's dependent Evidence/Artifact/Dispatch records.

This is preferable to assuming that changing the parent automatically mutates children.

Parent/child migration should be explicit and revision-checked.

## Typical question

> If `navigation@v5` changes, what needs review?

Run:

```text
authority-impact navigation_contract navigation@v5
```

Then:

```text
plan-authority-change navigation_contract navigation@v5 navigation@v6
```

The plan identifies affected runs and recommends `NAVIGATION_READY` as the earliest revalidation point, without silently changing any run.
