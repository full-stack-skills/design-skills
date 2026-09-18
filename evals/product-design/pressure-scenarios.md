# Product Design — Pressure Scenarios

These scenarios capture orchestration failures that occur when a product-design task spans requirements, navigation, visual continuity, documentation, rendering, and verification.

## RED-01 — One giant skill reimplements everything

**Prompt**

> Design this product end to end. We already have skills for feature specifications, navigation, documentation, Stitch/Pencil, and testing.

**Observed baseline failure**

The agent writes a new monolithic workflow that duplicates feature modeling, route contracts, documentation templates, rendering instructions, and test mechanics instead of delegating to existing atomic skills.

**Expected behavior with the skill**

Act as an orchestrator. Identify the current design stage, invoke only the atomic skills required for the missing decisions, and pass stable contracts between them.

## RED-02 — “Continue” restarts discovery

**Prompt**

> The information architecture and first two pages are already approved. Continue with the next page.

**Observed baseline failure**

The agent starts over by asking for product positioning, style direction, or menu structure that is already approved.

**Expected behavior with the skill**

Recover the latest approved state, determine the next unfinished task, preserve locked decisions, and continue from the current checkpoint. Ask only when a missing decision materially blocks the next step.

## RED-03 — Visual execution starts before behavior/navigation are ready

**Prompt**

> Generate the next high-fidelity page now. The actions, permissions, and route behavior are still ambiguous.

**Observed baseline failure**

The agent jumps directly to visual generation and invents missing semantics in the prompt.

**Expected behavior with the skill**

Route unresolved behavior to `feature-design` and unresolved hierarchy/route behavior to `navigation-design` before visual execution.

## RED-04 — Tool success is reported as product completion

**Prompt**

> Stitch rendered successfully. Mark the page done.

**Observed baseline failure**

The agent treats a rendered artifact as approved product design.

**Expected behavior with the skill**

Keep rendering, visual approval, contract approval, implementation verification, and archival as separate gates.

## GREEN acceptance

A response passes when it:
- identifies current stage and authority sources;
- reuses existing atomic skills instead of duplicating them;
- preserves approved decisions while continuing;
- refuses to silently invent missing product semantics;
- distinguishes candidate, approved design, implementation, and verified delivery;
- outputs a clear next action and handoff contract.
