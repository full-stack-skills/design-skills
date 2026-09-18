---
name: navigation-design
description: Use when menus, tabs, routes, deep links, return behavior, or active states are drifting across pages, especially when fixed navigation and page-local views are being confused or duplicated.
license: Apache-2.0
---

# Navigation Design

## Overview

Design navigation as a scoped contract, not as a list of labels. Separate structural inventory from activation state so local views cannot silently become global menus and corrections cannot erase approved navigation.

## When to use this skill

Use when:
- sidebar, domain submenu, workspace tabs, and page-local tabs are mixed together;
- the same label appears in several navigation scopes;
- routes, deep links, return state, or context propagation are unclear;
- a local correction risks changing the whole navigation hierarchy;
- generated pages keep changing menu order, wording, or nesting.

Do not use this skill merely to style a navbar or pick icons.

## How to use this skill

1. **Load the authority baseline.** Prefer approved IA/registries and explicit decisions over incidental content in screenshots.
2. **Inventory navigation by scope.** Give each item a stable ID and classify it as global, domain-level, workspace-level, page-local, or transient navigation.
3. **Separate existence from activation.** Record the fixed item inventory independently from which item becomes active for a route.
4. **Define routes.** For each navigation action specify source, target, required context, canonical route, deep-link reconstruction, and not-found/forbidden behavior.
5. **Define context propagation.** Preserve stable identifiers and serializable page state when the user expects return continuity.
6. **Define return behavior.** Drawer/modal close, drill-down return, browser Back, and cross-page return must have explicit contracts.
7. **Define invariants.** State what must not change when switching within a scope: item inventory, order, labels, shell regions, or context keys.
8. **Surface unresolved synchronization.** If changing a workspace tab may or may not change sidebar activation and the rule is not approved, mark it `needs-decision` rather than guessing.

Use [references/navigation-contract.md](references/navigation-contract.md) as the output shape.

## Best Practices

- **Do not deduplicate by label.** Same text can validly exist at different scopes.
- **Do not mirror dynamically.** A workspace/page-local set does not automatically become sidebar children.
- **Do not over-correct.** “Stop adding items” does not mean “delete approved fixed items”.
- **Route by stable IDs, not display names.**
- **Keep structure and active state separate.**
- **Screenshots are visual evidence, not automatically the IA source of truth.**

## Output contract

Return:
- navigation inventory by scope;
- route registry;
- activation matrix;
- context and return contract;
- deep-link/error behavior;
- invariants and `needs-decision` items;
- acceptance checks suitable for UI/E2E validation.

Read [references/anti-patterns.md](references/anti-patterns.md) before finalizing.

## Keywords

information architecture, navigation, sidebar, tabs, route, deep link, returnTo, active state, context propagation, IA, 导航设计, 菜单, 路由, Tab, 返回
