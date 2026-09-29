# Feature Contract Reference

Use this compact contract for one feature or one coherent capability.

## Identity

- `feature_id`
- `name`
- `goal`
- `scope_in`
- `scope_out`
- `authority_sources`
- `status`: confirmed / proposed / needs-decision

## Actors and objects

| Actor | Goal | Allowed responsibility |
|---|---|---|

| Object | Scope key | Version/lifecycle owner | Related objects |
|---|---|---|---|

## Action contract

| Action ID | Actor | Preconditions | Input | Visible result | Side effects | Evidence | Failure/recovery |
|---|---|---|---|---|---|---|---|

Do not collapse “button label” and “action”. A single action may have several entry points; a button without a behavior contract is not finished.

## State model

Record only states that change what the user can see or do.

| State | Entered when | Visible behavior | Allowed actions | Exit |
|---|---|---|---|---|

Typical categories: empty, loading/running, normal, waiting-human, blocked, conflict, failed, cancelled, recovered.

## Permission matrix

| Capability | Viewer | Editor | Owner | Approver/Admin | Automation/Agent |
|---|---:|---:|---:|---:|---:|

Use product-specific roles instead of these placeholders when confirmed. Unknown authority is `needs-decision`, not “probably admin”.

## Evidence and acceptance

For each success claim specify:
1. the claim;
2. required evidence;
3. validator;
4. failure behavior;
5. audit/event requirement if applicable.

Example: “Milestone complete” may require all mandatory deliverables, required approvals, and an immutable completion event. A green badge alone is not evidence.

## Open decisions

Each unresolved item records:
- decision;
- why it matters;
- affected actions/states/pages;
- safe temporary assumption, if one exists.

Downstream UI specs must not silently resolve these items.
