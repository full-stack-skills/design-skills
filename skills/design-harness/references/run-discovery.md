# Design Harness Run Discovery

Run discovery is the entry point for “continue”, “resume”, “next page”, and cross-session work when the caller does not already hold a trusted `run_id`.

## Principle

Do not guess the latest run from conversation memory or modification time.

Resolve a run by its bounded identity:

- product ID;
- product version;
- surface;
- scope type;
- exact scope ID set;
- SOP profile.

A matching active run is reused only when it is unique and any explicitly supplied authority bindings still agree.

## List runs

```bash
python skills/design-harness/scripts/design_harness.py runs \
  --store <project>/.design-harness
```

The command returns compact summaries only. It does not inline evidence/artifact ledgers.

## Find runs

```bash
python skills/design-harness/scripts/design_harness.py find-run \
  --store <project>/.design-harness \
  --product-id example \
  --product-version v1 \
  --surface desktop-web \
  --scope-type page \
  --scope-id P01 \
  --profile existing-product-next-page \
  --active-only
```

Scope IDs are compared as an exact set, independent of input order.

Terminal runs are:
- `ARCHIVED`;
- `CANCELLED`.

They are excluded by `--active-only`.

## Ensure a run

Prefer `ensure-run` before creating a new multi-step design run:

```bash
python skills/design-harness/scripts/design_harness.py ensure-run \
  --store <project>/.design-harness \
  --product-id example \
  --product-version v1 \
  --surface desktop-web \
  --scope-type page \
  --scope-id P01 \
  --profile existing-product-next-page \
  --authority feature_contract=feature@v3 \
  --authority navigation_contract=navigation@v5 \
  --authority baseline=shell@v2
```

The result is:

```json
{
  "created": false,
  "run": {
    "run_id": "design_xxx",
    "revision": 12
  }
}
```

or a newly created run with `created=true`.

## Registry atomicity

`ensure-run` performs discovery and creation under a short-lived Registry Lock:

```text
<store>/runs/.registry.lock
```

This prevents two sessions from both observing “no run exists” and creating duplicate active runs for the same bounded scope.

The per-run revision/CAS lock still protects each run's own mutations.

## Ambiguous active runs

If more than one active run already matches the same bounded identity, the runtime raises `RunAmbiguityError`.

It must **not** choose:
- the newest run;
- the highest revision;
- the run with the most artifacts;
- whichever one was mentioned most recently.

Resolve the duplicate-run situation explicitly.

## Authority drift

When `ensure-run` finds one unique active run, authority bindings explicitly supplied by the caller are checked against the run.

Example conflict:

```text
existing: feature_contract=feature@v1
requested: feature_contract=feature@v2
```

The runtime raises `RunAuthorityConflictError`.

It does not:
- silently update the active run;
- silently reuse stale authority;
- silently create another run.

Choose an explicit operation instead: correction/invalidation, authority migration, archive/cancel old work, or intentionally create a differently scoped/profiled run.

Authorities omitted by the caller are treated as “not asserted”; they do not conflict with existing bindings.

## Corrupt ledger diagnostics

Run scanning skips unreadable/corrupt `*.json` ledgers and reports diagnostics containing file name, error class, and message.

A corrupt unrelated ledger must not make all valid runs undiscoverable, but it must not be silently ignored either.

## Resume sequence

For a generic “continue” request:

```text
ensure-run
 -> returned unique active run
 -> status
 -> computed_next_action
 -> dispatch/control/human/verification
```

Do not start a new run until discovery proves that no matching active run exists.
