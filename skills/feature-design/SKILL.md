---
name: feature-design
description: Use when a product feature is underspecified, when UI work is starting before actions/states/permissions/evidence are defined, or when an existing feature needs a behavior contract without changing approved information architecture.
license: Apache-2.0
---

# Feature Design

## Overview

Turn a feature idea into an observable product-behavior contract before visual design or implementation. Preserve approved product structure; make uncertainty explicit instead of filling gaps with plausible-looking behavior.

## When to use this skill

Use when:
- a feature name exists but roles, actions, states, permissions, failure paths, or completion evidence are unclear;
- a team is about to draw or build UI from a thin requirement;
- product behavior must be refined without redesigning approved IA or brand structure;
- “Done”, “Approved”, or “Delivered” needs verifiable meaning.

Do not use this skill to choose visual style, generate final UI, design backend architecture, or rewrite an approved navigation model.

## How to use this skill

1. **Establish authority.** List the current fact sources: approved requirement, IA, terminology, policy, and explicit user decisions. Separate `confirmed`, `proposed`, and `needs-decision`.
2. **Define the outcome.** State actor, situation, desired result, and out-of-scope behavior.
3. **Model the product object.** Identify the business object, lifecycle owner, version/scope keys, and relationships needed by the feature.
4. **Define actions.** For every user or agent action record preconditions, input, visible result, side effects, evidence, cancellation/undo, and failure handling.
5. **Define states.** Cover normal, empty, loading/running, waiting-human, blocked/conflict, failed, cancelled, and recovered states that materially affect the experience.
6. **Define permissions.** Record who may view, mutate, approve, override, export, or execute automation. Unknown authority stays `needs-decision`.
7. **Define evidence and acceptance.** A status label is not proof. State what artifact, event, approval, or runtime result proves success.
8. **Publish the contract.** Use the structure in [references/feature-contract.md](references/feature-contract.md). Send navigation concerns to `navigation-design`; send page continuation constraints to `ui-continuity`.

## Best Practices

- **Behavior before layout.** Cards and tables are representations, not the feature contract.
- **Preserve upstream decisions.** Never “improve” approved IA while filling a feature spec.
- **Do not invent authority.** Approval, override, AI execution, and destructive actions require explicit rules.
- **Status ≠ evidence.** Record how claims are proven.
- **Design recovery, not only happy paths.** Define retry, rollback, resume, conflict, and human takeover when relevant.
- **Keep proposals labeled.** A useful proposal may be included, but cannot masquerade as confirmed behavior.

## Output contract

Return:
- feature goal and scope;
- actors and objects;
- action contract;
- state model;
- permission matrix;
- evidence/acceptance rules;
- dependencies and open decisions;
- downstream page implications without visual styling.

See [references/anti-patterns.md](references/anti-patterns.md) before finalizing.

## Keywords

feature design, product behavior, action contract, state model, permission, evidence, acceptance criteria, 产品功能设计, 功能规格, 状态, 权限, 验收
