# Product Design Orchestration Anti-patterns

## Monolithic reimplementation

**Failure:** The orchestrator rewrites feature, navigation, rendering, and testing logic inside itself.

**Fix:** Route to the narrowest existing skill and pass explicit contracts.

## Restarting on “continue”

**Failure:** Re-ask product positioning, IA, or style questions that were already approved.

**Fix:** Recover state and continue from the next unfinished gate.

## Visual-first gap filling

**Failure:** Missing permissions/routes are invented inside a render prompt.

**Fix:** Resolve them upstream with `ui-design-feature` / `ui-design-nav` or mark them `needs-decision`.

## Tool-success completion

**Failure:** A generated screen is called final.

**Fix:** Keep candidate, preferred direction, approved visual master, product-contract approval, runtime verification, and archival distinct.

## Competing facts

**Failure:** Every skill maintains its own menu/page truth.

**Fix:** Share stable IDs and versioned contracts; use `ui-design-review` before promotion.

## Recursive routing

**Failure:** ui-design-spec hands execution to Harness, then its baseline/task handler re-enters the full product router and starts another run.

**Fix:** user-entry routing happens once. A dispatch handles its exact scope and evidence stage and returns to the active run.

## Duplicate specification ownership

**Failure:** spec mode, ui-design-feature and ui-design-nav each create their own full document package or task checklist.

**Fix:** spec mode owns package organization; specialists refine their canonical sections with shared IDs and versions. Existing sufficient content is inspected and reused.
