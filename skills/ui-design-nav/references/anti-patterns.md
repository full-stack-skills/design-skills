# Navigation Design Anti-patterns

## Dynamic hierarchy mirroring

**Failure:** Copy workspace tabs or page-local views into the sidebar.

**Fix:** Maintain each navigation scope independently and connect them through activation/route contracts.

## Over-correction

**Failure:** A request to stop dynamic injection causes deletion of already-approved fixed submenu items.

**Fix:** Change only the violated rule. Preserve the approved inventory.

## Same-label deduplication

**Failure:** Remove one “Plan” item because another scope also uses “Plan”.

**Fix:** Compare scope, route, context, and responsibility; text equality does not imply duplication.

## Local views replace parent navigation

**Failure:** Summary/WBS/Gantt replaces the workspace tab row.

**Fix:** Parent navigation stays structurally present; only the local-view group changes inside its page.

## Screenshot becomes authority

**Failure:** Latest generated screenshot silently overrides the IA registry.

**Fix:** Use screenshots for visual evidence unless explicitly promoted to product-structure authority.

## Invented activation synchronization

**Failure:** Clicking one navigation level automatically changes another because it “seems logical”.

**Fix:** Record synchronization explicitly or mark it `needs-decision`.
