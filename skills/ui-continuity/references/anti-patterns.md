# UI Continuity Anti-patterns

## Rebuilding the product around each page

**Failure:** Every new page gets a new sidebar, header, or tab hierarchy.

**Fix:** Partition the approved baseline and replace only page-local regions.

## Freezing everything

**Failure:** “Keep the shell” is interpreted as every text value and DOM byte being immutable.

**Fix:** Preserve structure and identity while allowing contract-defined active states and live data.

## Positive feedback becomes blanket approval

**Failure:** “This is better” promotes all visible labels, values, and interactions to product truth.

**Fix:** Record the approved scope explicitly.

## Local feedback triggers global redesign

**Failure:** Correct one navigation issue by deleting or reorganizing unrelated approved elements.

**Fix:** Use the scoped feedback patch.

## Latest screenshot wins

**Failure:** A newer generated image overrides an approved specification.

**Fix:** Resolve authority by artifact type; surface conflicts between approved sources.

## Rendered equals accepted

**Failure:** Successful generation is reported as final approval.

**Fix:** Keep candidate, preferred, approved visual master, and approved product contract as separate maturity states.
