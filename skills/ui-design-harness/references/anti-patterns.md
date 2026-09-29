# Design Harness Anti-patterns

## Stateless orchestration

**Failure:** Every “continue” reconstructs workflow state from prose and often restarts completed stages.

**Fix:** Persist run state, authority versions, evidence, invalidations, and exactly one next action.

## Giant SOP prompt

**Failure:** One prompt contains feature design, navigation, visual generation, testing, and approval logic.

**Fix:** Harness the atomic skills; do not duplicate them.

## Provider success skips gates

**Failure:** “Stitch/Pencil/ImageGen succeeded” becomes “design complete”.

**Fix:** Provider evidence advances only its stage; guard and approval gates remain.

## Blind retry

**Failure:** A timed-out write is immediately resent, creating duplicate projects/screens/runs.

**Fix:** Enter `RECONCILING`; inspect read-only state first.

## Global reset after local feedback

**Failure:** A sidebar correction causes feature, IA, and approved shell work to restart.

**Fix:** Invalidate only dependent downstream evidence and resume at the earliest affected state.

## Latest artifact as authority

**Failure:** Newest render silently changes menus or behavior.

**Fix:** Bind the run to versioned authority sources; drift becomes a guard finding.

## Parallel baseline fork

**Failure:** Multiple pages each recreate the shared shell independently.

**Fix:** Pin one shared baseline version and require child tasks to reference it.
