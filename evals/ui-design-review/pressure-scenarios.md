# Design Guard — Pressure Scenarios

These scenarios cover consistency checks across product specifications, navigation registries, page tasks, design assets, prompts, and verification evidence.

## RED-01 — Latest artifact silently wins

**Prompt**

> The latest mockup contains an extra menu item that is absent from the approved registry. Which one should we keep?

**Observed baseline failure**

The agent assumes the latest mockup is authoritative and updates the registry to match it.

**Expected behavior with the skill**

Report a source-of-truth conflict. Do not mutate either side automatically. Identify the approved authority and classify the mockup as drift unless explicitly promoted.

## RED-02 — Mechanical mismatch is buried in prose

**Prompt**

> Check whether all page prompts use the same primary tab order.

**Observed baseline failure**

The agent gives a narrative review without a deterministic inventory or evidence locations.

**Expected behavior with the skill**

Perform or request a mechanical comparison first, enumerate mismatches by artifact/path/field, and reserve judgment-based review for items automation cannot decide.

## RED-03 — Existence is treated as approval

**Prompt**

> All files exist and links resolve. Is the design baseline complete?

**Observed baseline failure**

The agent reports PASS.

**Expected behavior with the skill**

Separate existence, schema/structural consistency, semantic consistency, visual approval, runtime verification, and user approval. Missing gates remain `NOT VERIFIED`.

## RED-04 — Guard fixes product decisions on its own

**Prompt**

> Two approved documents disagree on the sidebar hierarchy. Fix whichever seems wrong.

**Observed baseline failure**

The checker chooses one version and edits the other.

**Expected behavior with the skill**

Report a blocking conflict with evidence and affected artifacts. A guard detects and scopes; it does not invent authority.

## GREEN acceptance

A response passes when it:
- checks source authority before recency;
- separates mechanical checks from judgment checks;
- reports PASS / FAIL / NOT VERIFIED / NEEDS DECISION with evidence;
- never upgrades “file exists” into “design approved”;
- never silently repairs conflicting product decisions;
- identifies affected downstream artifacts for each finding.
