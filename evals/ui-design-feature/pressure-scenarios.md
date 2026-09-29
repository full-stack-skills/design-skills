# Feature Design — Pressure Scenarios

These scenarios capture baseline failures observed before the skill existed. They are intentionally product-agnostic.

## RED-01 — Jumping from a feature name straight to UI

**Prompt**

> Design a milestone feature for an enterprise project-delivery product. The information architecture is already approved. I want to see the page quickly.

**Observed baseline failure**

The agent jumps directly to KPI cards, tables, and timelines. It does not define who can create or complete a milestone, what “complete” means, what evidence is required, what happens on delay, or which states and permissions exist.

**Expected behavior with the skill**

Produce a feature contract first: outcome, actors, domain object, actions with preconditions/results, states and recovery, permissions, evidence, acceptance criteria, assumptions, and open questions. Preserve the approved information architecture.

## RED-02 — Inventing missing semantics to make the page look complete

**Prompt**

> Add “Approve”, “Complete”, and “AI Analyze” actions. We have not decided their rules yet. Make the specification production-ready.

**Observed baseline failure**

The agent silently invents approval rules, completion authority, and AI side effects, then presents them as confirmed product behavior.

**Expected behavior with the skill**

Separate confirmed facts from proposals. Define the observable contract that is known, mark unresolved semantics as `needs-decision`, and do not fabricate authority or side effects.

## RED-03 — Treating status as evidence

**Prompt**

> The task is marked Done. Is that enough for delivery acceptance?

**Observed baseline failure**

The agent equates a status value with completed delivery.

**Expected behavior with the skill**

Distinguish status from evidence. Define what artifacts/events/approvals prove completion and what validation is required before the status can be trusted.

## GREEN acceptance

A response passes when it:
- preserves upstream IA and terminology;
- defines observable behavior before visual layout;
- distinguishes facts, proposals, and open questions;
- covers actions, states, permissions, failure/recovery, evidence, and acceptance;
- does not implement UI, code, or backend policy that was not requested.
