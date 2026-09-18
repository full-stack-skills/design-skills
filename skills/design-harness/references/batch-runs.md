# Parent / Child Batch Runs

Use batch runs when several pages share one approved shell/design baseline but still need independent page-level execution, review, correction, and approval.

## Model

```text
parent: page-family-batch
├── child: page/P01 -> existing-product-next-page
├── child: page/P02 -> existing-product-next-page
├── child: page/P03 -> existing-product-next-page
└── child: page/P04 -> existing-product-next-page
```

The parent owns:
- shared baseline identity;
- child inventory;
- aggregate status;
- batch approval decision.

Each child owns:
- page task;
- continuity contract;
- candidate artifacts;
- guard evidence;
- page approval;
- delivery verification.

The parent must not duplicate those page-level stages.

## Start the parent

```bash
python skills/design-harness/scripts/design_harness.py start \
  --store <project>/.design-harness \
  --run-id project-pages-v1 \
  --product-id example \
  --product-version v1 \
  --surface desktop-web \
  --scope-type page-family \
  --scope-id project-pages \
  --profile page-family-batch \
  --authority feature_contract=feature@v3 \
  --authority navigation_contract=navigation@v5 \
  --authority baseline=shell@v2
```

Bind the shared baseline:

```bash
python skills/design-harness/scripts/design_harness.py resume \
  --store <project>/.design-harness \
  --run-id project-pages-v1 \
  --evidence-json '{"stage":"baseline","status":"pass","producer":"product-design","observed_result":"shared baseline bound"}'
```

## Spawn children

```bash
python skills/design-harness/scripts/design_harness.py spawn-children \
  --store <project>/.design-harness \
  --run-id project-pages-v1 \
  --child-scope-id P01 \
  --child-scope-id P02 \
  --child-scope-id P03
```

Each child:
- inherits product/version/surface;
- inherits the parent's authorities;
- pins the exact same `baseline`;
- records `parent_run_id`;
- uses `existing-product-next-page`;
- starts already at `BASELINE_BOUND`, because the parent supplied the verified shared-baseline evidence.

Duplicate child scope IDs are rejected.

A child cannot override the shared baseline with a different value.

## Child execution

After spawning, continue each child through its normal profile:

```text
BASELINE_BOUND
 -> TASK_READY
 -> CONTINUITY_READY
 -> CANDIDATE_READY
 -> GUARD_REVIEWED
 -> AWAITING_USER_APPROVAL
```

One child may enter `CORRECTION`, `RECONCILING`, or `BLOCKED` without deleting sibling progress.

## Aggregate status

```bash
python skills/design-harness/scripts/design_harness.py batch-status \
  --store <project>/.design-harness \
  --run-id project-pages-v1
```

The response includes:
- per-state counts;
- child run IDs and current states;
- shared baseline;
- `overall_state`;
- `ready_for_batch_approval`;
- `all_delivery_verified`.

Aggregate states are derived from children:

| Condition | Overall state |
|---|---|
| any child `BLOCKED` | `BLOCKED` |
| else any child `RECONCILING` | `RECONCILING` |
| all children `ARCHIVED` | `ARCHIVED` |
| all children `DELIVERY_VERIFIED` or `ARCHIVED` | `DELIVERY_VERIFIED` |
| all children `APPROVED` or beyond | `APPROVED` |
| all children awaiting/already approved and at least one awaits | `READY_FOR_APPROVAL` |
| no children | `EMPTY` |
| otherwise | `RUNNING` |

## Batch approval

Batch approval is allowed only when every child is either:
- `AWAITING_USER_APPROVAL`, or
- already `APPROVED`.

```bash
python skills/design-harness/scripts/design_harness.py batch-approve \
  --store <project>/.design-harness \
  --run-id project-pages-v1 \
  --actor human
```

The runtime approves every waiting child using that child's exact scope, then writes one `batch-approval` decision into the parent.

A blocked, incomplete, or reconciling child prevents batch approval.

## Shared baseline changes

Do not silently edit a child to use a different shell baseline.

If the shared baseline changes:
1. change the parent authority explicitly;
2. identify affected child runs;
3. invalidate dependent child evidence;
4. re-run continuity/guard stages as needed;
5. only then promote the new baseline.

A baseline change is a family-level decision, not a page-local correction.

## Parallel execution

`page-family-batch` declares:

```text
parallel_policy = shared-baseline
child_scope = page
child_profile = existing-product-next-page
```

This means page-level work may be parallelized only after the parent baseline is bound. Parallel execution never authorizes children to fork shell/navigation contracts independently.
