# Design Guard Report Contract

## Header

- target product/version
- review scope
- authority sources and versions
- artifacts inspected
- checks actually executed
- checks not available

## Findings

| ID | Category | Status | Evidence | Expected | Actual | Affected artifacts | Next action |
|---|---|---|---|---|---|---|---|

Statuses:
- `PASS`: check executed and expected condition observed;
- `FAIL`: check executed and mismatch observed;
- `NOT VERIFIED`: evidence/tool/check was unavailable or not run;
- `NEEDS DECISION`: authoritative sources conflict or policy is unspecified.

## Severity

Optional:
- `blocking`: promotion would encode contradictory or unsafe product behavior;
- `important`: meaningful drift that should be corrected before handoff;
- `minor`: local polish/documentation mismatch without contract impact.

Severity never replaces status.

## Conflict record

For `NEEDS DECISION`:
- source A + version;
- source B + version;
- conflict field;
- why neither may be silently overwritten;
- downstream artifacts affected.

## Completion rule

“Guard passed” is allowed only when all required checks for the requested promotion gate are PASS. Otherwise report the exact remaining FAIL / NOT VERIFIED / NEEDS DECISION items.

## Harness result aggregation

Keep each finding and its evidence. For required checks: unresolved authority conflicts aggregate to `needs-decision`; otherwise observed failures aggregate to `fail`; unavailable checks aggregate to `unknown`; only all required checks PASS aggregate to `pass`. Include report artifact and source versions in the current guard dispatch. Recommendations alone do not become user approval. The caller routes corrections and resubmits affected checks; review does not start its own workflow.
