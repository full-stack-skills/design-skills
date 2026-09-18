# Design Harness Run Contract

A design run is the persistent execution record for one bounded product-design goal.

## Run identity

- `run_id`
- `product_id`
- `product_version`
- `surface`
- `scope_type`: product / domain / page-family / page / correction
- `scope_ids`
- `created_at`
- `updated_at`
- `state`

## Authority bindings

Record exact versions/IDs for:
- feature contract;
- navigation contract;
- design task contract;
- design system / shell baseline;
- scenario fixture;
- user decisions.

Do not use “latest” as a durable authority pointer.

## Artifact ledger

Each artifact records:

| Field | Meaning |
|---|---|
| `artifact_id` | stable run-local/global ID |
| `type` | spec / prompt / editable-source / render / screenshot / report / test-evidence / archive |
| `producer` | skill/tool/provider |
| `input_versions` | exact upstream contracts |
| `maturity` | candidate / preferred / approved-master / verified-delivery / archived |
| `status` | valid / invalidated / superseded / unknown |
| `location` | repository/file/provider reference |
| `evidence_ids` | receipts that support claims |

## Decision ledger

Record:
- decision ID;
- exact scope;
- chosen option;
- user/source authority;
- timestamp;
- affected artifacts;
- whether it invalidates previous evidence.

## Invalidation graph

When an upstream contract changes:
1. identify dependent artifacts by `input_versions`;
2. mark only those artifacts invalidated;
3. retain unaffected evidence;
4. return the run to the earliest affected state.

Never delete historical evidence to make the run look clean.

## Next action

Store exactly one logical `next_action`:
- specialist skill/tool;
- required input refs;
- expected evidence type;
- stop condition.

“Continue” executes this action after confirming no newer decision invalidated it.

## Parallel pages

For a page family:
- bind one shared shell/design-system baseline version;
- create child page tasks/runs referencing that version;
- do not allow child runs to silently fork the baseline;
- promote a baseline change explicitly, then invalidate/review affected children.
