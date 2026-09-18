# Design Harness Evidence Contract

Evidence proves a specific transition; it does not prove the whole run.

## Evidence fields

- `evidence_id`
- `run_id`
- `stage`
- `producer`
- `artifact_ids`
- `input_versions`
- `observed_result`
- `status`: pass / fail / unknown / needs-decision
- `timestamp`
- `provenance`
- `limitations`

## Evidence classes

### Contract evidence
Confirmed feature/navigation/task/continuity versions.

### Provider evidence
Tool/provider request and resulting artifact identity. Provider “success” only proves that the provider reported success unless the artifact is independently retrieved/validated.

### Guard evidence
`design-guard` findings with checks actually executed.

### Human decision evidence
Explicit user approval/rejection/correction for a named scope.

### Delivery evidence
Browser/runtime/test evidence required after implementation or provider round-trip.

## Promotion rule

A transition may consume only evidence whose:
- `run_id` matches;
- upstream input versions are still valid;
- status satisfies the gate;
- artifact has not been invalidated.

## Unknown outcomes

Timeout, interrupted connection, or missing acknowledgement is `unknown`, not `fail` and not `pass`.

Enter `RECONCILING` and inspect the provider/read model before deciding whether to retry.

## Evidence honesty

Never infer:
- user approval from positive sentiment;
- semantic correctness from a screenshot existing;
- runtime behavior from static HTML;
- final delivery from a provider success string;
- current validity from an old receipt after upstream changes.
