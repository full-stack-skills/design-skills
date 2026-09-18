# Design Guard Anti-patterns

## Latest file wins

**Failure:** The newest mockup silently overrides an approved registry.

**Fix:** Resolve authority by artifact role/version, not modification time.

## Narrative-only lint

**Failure:** A deterministic order/ID mismatch is discussed but never enumerated.

**Fix:** Run or request a mechanical comparison and attach evidence.

## Existence equals completion

**Failure:** “All files exist” becomes “design is complete”.

**Fix:** Separate existence, structure, semantics, visual approval, runtime verification, and user approval.

## Guard becomes product owner

**Failure:** The checker chooses between conflicting approved sources.

**Fix:** Report `NEEDS DECISION` and the affected artifacts.

## Unverified PASS

**Failure:** A check that could not run is marked successful.

**Fix:** Use `NOT VERIFIED`.

## Fix without regression

**Failure:** A mismatch is corrected but dependent prompts/assets/tests are not rechecked.

**Fix:** Identify downstream impact and re-run the relevant guard set.
