# Design Harness SOP Profiles

Profiles define **which design stages are required for a task class**. They do not redefine the domain rules of the specialist skills that execute those stages.

List the installed profiles:

```bash
python skills/design-harness/scripts/design_harness.py profiles
```

Inspect one profile:

```bash
python skills/design-harness/scripts/design_harness.py profile --name existing-product-next-page
```

Start a run with a profile:

```bash
python skills/design-harness/scripts/design_harness.py start \
  --store <project>/.design-harness \
  --product-id example \
  --product-version v1 \
  --surface desktop-web \
  --scope-type page \
  --scope-id P02 \
  --profile existing-product-next-page \
  --authority feature_contract=feature@v3 \
  --authority navigation_contract=navigation@v5 \
  --authority baseline=shell@v2
```

## Built-in catalog

| Profile | Use when | Key behavior |
|---|---|---|
| `product-to-ui` | A product/feature must move from product intent to an approved UI candidate | Runs behavior → navigation → page task → continuity → render → guard → approval |
| `existing-product-next-page` | IA/feature/navigation/shell are already locked and the next page must continue the family | Requires locked upstream authorities and skips reopening behavior/navigation stages |
| `page-family-batch` | Several pages share the same approved shell/design language | Pins a shared baseline and declares `shared-baseline` parallel policy for page children |
| `design-correction` | Existing run receives scoped feedback | Correction-only entry; use the runtime `correct` path rather than starting a new run |
| `stitch-high-fidelity-delivery` | A contract-bound page is delivered through Stitch | Routes candidate production to `stitch-delivery-harness`, then guard + approval |
| `design-to-implementation` | Approved design must become a guarded implementation handoff and then be runtime-verified | Requires approved design authority and keeps delivery verification as the final gate |

## Profile schema

Each profile JSON includes:

- `id`
- `version`
- `title`
- `description`
- `entry_mode`: `start` or `correction`
- `required_authorities`
- `parallel_policy`
- `child_scope`
- `final_gate`
- ordered `stages`

Each stage includes:

- `evidence_stage`
- `target_state`
- `handler`
- `required`

The runtime stores the chosen profile ID/version and a copy of the stage plan in the run ledger. This makes a historical run reproducible even when the built-in profile later evolves.

## Authority requirements

Profiles may require authority bindings before the run can start. Example:

`existing-product-next-page` requires:

- `feature_contract`
- `navigation_contract`
- `baseline`

If any is missing, start fails. The harness must not reopen or invent those decisions merely to proceed.

## Stage skipping

A profile may omit generic states that are not needed for its task class.

Example:

`existing-product-next-page` may progress:

```text
INIT
 -> BASELINE_BOUND
 -> TASK_READY
 -> CONTINUITY_READY
 -> CANDIDATE_READY
 -> GUARD_REVIEWED
 -> AWAITING_USER_APPROVAL
```

This is an explicit profile plan, not an accidental gate bypass.

## Profile evolution

- Change a profile's `version` when stage semantics or required authorities change.
- Existing runs retain the copied `stage_plan` and bound profile version.
- Never rewrite historical run ledgers to match a new profile.
- Use a new profile when the task class has meaningfully different stage ownership, rather than accumulating exceptions.

## Custom profiles

A project-specific profile may be added only when:
1. existing profiles cannot express the required stage sequence without distorting their meaning;
2. specialist skill ownership remains unchanged;
3. required authorities and final gate are explicit;
4. tests cover the new stage plan.

Product-specific menu names, routes, and design tokens belong in project contracts, not in the reusable profile.
