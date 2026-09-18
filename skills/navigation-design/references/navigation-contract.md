# Navigation Contract Reference

## 1. Navigation inventory

| Nav ID | Label | Scope | Parent | Fixed inventory? | Visibility rule | Route family |
|---|---|---|---|---|---|---|

Recommended scopes:
- `global`: product-wide domain entry;
- `domain`: fixed navigation inside a business domain;
- `workspace`: context-bound switching inside one selected object/workspace;
- `local-view`: views of the current page;
- `transient`: drawer/modal/detail navigation that does not redefine the base hierarchy.

These names are descriptive, not mandatory product labels.

## 2. Activation matrix

| Route pattern | Global active | Domain active | Workspace active | Local-view active |
|---|---|---|---|---|

**Important:** inventory and active state are different contracts. A route may change activation without adding/removing navigation items.

## 3. Route registry

| Source | Action | Target | Required IDs | Query/state | Return behavior | Permission/error |
|---|---|---|---|---|---|---|

Carry identifiers explicitly. Do not use display names as stable keys.

## 4. Context contract

Common categories:
- tenant/account/workspace ID;
- selected business object ID and version;
- source/return target;
- filters, sort, pagination;
- selected row/node;
- serializable viewport/time-range state when necessary.

Only preserve state that materially affects task continuity.

## 5. Deep-link contract

A direct target URL must:
1. reconstruct the required shell/context;
2. activate the correct navigation levels;
3. validate object-to-context ownership;
4. apply permission/not-found behavior;
5. avoid requiring the user to visit a list page first.

## 6. Invariants

Examples:
- fixed menu inventory/order does not change while switching local views;
- local views never replace workspace navigation;
- workspace switching does not mutate sidebar structure unless the approved contract explicitly says so;
- same-label items are not merged without scope analysis.

## 7. Acceptance checks

Write checks as observable invariants, e.g.:
- after switching a workspace tab, the fixed sidebar item IDs are unchanged;
- only one item per navigation group is active;
- Back/close restores the documented source state;
- invalid cross-context IDs are blocked.
