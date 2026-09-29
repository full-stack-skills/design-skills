---
name: ui-design-visual
description: Create HTML UI prototypes and visual artifacts from a scoped specification, theme and continuity brief. Use for visual exploration, page production, slides or animation; cross-artifact acceptance belongs to ui-design-review.
license: Apache-2.0
---

# UI Design Visual

## When to use this skill

Produce interactive HTML prototypes, visual explorations, slides, infographics or animation. For product UI, consume the current feature/page/navigation contracts. Production application implementation requires its own implementation scope.

## How to use this skill

1. **Resolve scope and authority.** Read the canonical task, IDs, source versions, confirmed decisions and expected output. A Harness dispatch takes precedence: perform only its named stage and return through that dispatch; never create another run or task source.
2. **Resolve theme and constraints.** Reuse the theme reference from ui-design-theme and the initial/inherit/correction brief from ui-design-continuity. Missing optional skills do not authorize installation: read the existing contracts and report missing inputs. Initial mode permits visual exploration within confirmed product constraints; inherit mode preserves the approved baseline.
3. **Choose the production path.** Read only the relevant sections of [detailed workflows](references/visual-workflows.md) and its resource routes. Existing confirmed choices override exploratory defaults. A scoped single-page task does not automatically require three alternatives, slides, animation or export.
4. **Generate within the change budget.** Preserve page/Surface/task IDs, business behavior and navigation. Style variations change only explicitly open visual decisions. Keep demonstration data and unavailable assets honestly labeled.
5. **Verify the candidate.** Inspect actual browser/render output when tools permit; record interactions exercised, assets, source and screenshots. If verification is unavailable, report it as unverified. Author self-checks do not replace ui-design-review or user approval.
6. **Return the handoff.** Include candidate/source paths, theme and constraint versions, changed regions, check evidence and limitations. ui-design-review compares the resulting candidate against the same sources; unresolved findings go back to the caller for scoped correction.

## Production references

- UI/HTML: [workflow](references/workflow.md), [React setup](references/react-setup.md), [tweaks](references/tweaks-system.md).
- Visual exploration and resource routing: [detailed workflows](references/visual-workflows.md).
- Slides: [slide decks](references/slide-decks.md).
- Animation: [animations](references/animations.md), [video export](references/video-export.md).
- Optional aesthetic self-review: [critique guide](references/critique-guide.md); this does not substitute for cross-artifact acceptance.

## Best Practices

- Confirmed requirements, theme and baseline take precedence over exploration templates.
- Reuse prior answers and authorization. Ask only about missing decisions that materially affect scope, authority or acceptance.
- Adapt to actual available tools and resource limits, never to model-brand assumptions. Serial execution may replace parallel work; do not claim independent contexts or erased memory.
- Required user decisions, conflicting authorities and approval gates remain required under fallback. Assumptions cannot replace them.
- Preserve the agreed output scope. Report blocked rendering/export honestly; do not install dependencies automatically.
- Do not add promotional watermarks or third-party branding to user output by default. Add user-requested branding only within its specified scope. Preserve source licenses separately.
- A rendered candidate is neither an approved visual baseline nor verified production behavior.

## Output contract

Return task/page identity, input versions, theme reference, continuity mode and brief, candidate and editable source, actual verification evidence, changed regions, unresolved findings and the next bounded action. Dispatched candidate evidence uses the supplied evidence stage and existing runtime statuses.

## Keywords

UI prototype, HTML design, visual exploration, slides, animation, candidate generation, 界面原型, 视觉制作, 设计交接
