---
name: ui-design-to-image
description: Generate or edit UI concept images and frontend raster assets from a scoped design brief, using native imagegen or an explicitly chosen baoyu-image-gen backend. Use for screen mockups, visual variants, hero art and scoped image corrections; exact UI screenshots come from rendering the real frontend.
license: Apache-2.0
compatibility: Requires an available image-generation tool or an explicitly configured image-generation skill. API and CLI paths have provider-specific credentials and dependencies; design briefing alone has no image-provider dependency.
---

# UI Design to Image

## When to use this skill

Create UI concept bitmaps, page-direction images, illustrations, hero assets or edits from an existing design contract. This skill owns the image production step, not product behavior, navigation, theme selection, user approval or frontend implementation.

For exact screenshots, editable layouts, semantic controls or functioning pages, render the actual HTML/CSS/application through the existing frontend workflow. Do not substitute a generated screenshot for runtime evidence. For an established SVG/icon system, prefer its editable source unless a generated bitmap is explicitly requested.

## How to use this skill

### 1. Resolve the brief

Read the existing page/task, feature and navigation contracts, selected theme and continuity brief. Preserve their IDs, versions and authority. A clear standalone visual request may use a compact brief without starting Harness or a specification package.

Identify:
- intent: new concept, reference-guided concept, image edit, or project raster asset;
- target page/Surface or asset role, requested count and destination;
- exact visible text, hierarchy, component regions and design tokens;
- requested viewport and the provider's actual output dimensions;
- reference roles: edit target, approved visual baseline, style reference or supporting insert;
- mutable regions, frozen decisions and known limits.

Default project viewports, unless the existing contract differs: Mobile 390×884, Tablet 768×1024, Desktop 1280×1024. These are frontend logical viewports, not a claim that an image tool accepts those exact raster sizes. State any size or aspect-ratio approximation; never stretch an image or invent CSS-pixel verification.

For inherited or correction work, inspect the actual reference image and verify its approved scope. A screenshot cannot override the product or navigation contract. Missing required references block that edit; do not silently reconstruct them from prose.

Use [references/image-contract.md](references/image-contract.md) when a structured handoff or recorded receipt is needed.

### 2. Select an available backend

Discover capabilities in the current runtime; a model name, installed skill name or login alone does not prove an image tool is callable.

- In Codex, use the available native image-generation tool and current `imagegen` instructions by default. Do not require an OpenAI API key for this path.
- A user-selected provider, API, CLI or baoyu workflow routes to the actually available `baoyu-image-gen` or approved imagegen CLI. Resolve its installed directory; read its current instructions and use its maintained scripts.
- If native image generation fails or is absent, describe the available alternative. Switch to a paid API, another provider or model only when that route is already authorized or the user chooses it.
- For text-only preparation, produce a prompt and brief and label the image as not generated. Do not fabricate an image, receipt or tool invocation.

Read [references/backends.md](references/backends.md) for provider setup, credentials, references, batching and fallback boundaries. Do not install dependencies, initialize provider preferences or edit host credentials merely because this skill is selected.

### 3. Prepare and generate

Use [assets/ui-image-prompt.md](assets/ui-image-prompt.md) as an optional compact prompt shape. Keep confirmed requirements separate from visual proposals. Include quoted visible text, layout regions, theme, reference identities, change budget and exclusions. Do not add unrelated business functions, branding or promotional watermarks.

For edits, describe one scoped change and the invariants. Pass the real edit target through the backend's supported mechanism. References described only in text are not image-conditioned generation. Report that difference.

A request for several assets does not force CLI mode: native tools can be called once per requested asset. Use baoyu batch execution when the user chose that backend and prompts are ready. Sequential work is valid; this skill never implies permission to spawn agents or exceed the requested output count.

Let one layer own retries. Follow the chosen backend's documented bounded retry behavior; do not wrap it in another automatic retry loop. Authentication, unsupported input and configuration failures need correction, not repeated generation. For a timeout with unknown outcome, inspect existing outputs/request state first; do not submit a second possibly billable generation blindly.

### 4. Inspect and hand off

Inspect the returned image for visual hierarchy, required text, navigation identity, approved shell/theme, scoped changes and unintended content. A generated reference edit cannot promise pixel-identical frozen regions: any drift must be reported and reviewed.

For project assets, copy the selected output to the requested project location using a versioned name unless replacement was authorized. Preserve original references. Verify file existence and record dimensions and hash when available. Never claim alpha transparency or exact text fidelity without inspecting the actual file. If only inline output or a remote link is available, record that limitation instead of inventing a local path.

Compare Mobile/Tablet/Desktop as separately designed layouts when requested, not as three scaled copies. Transparent bitmap requests need actual alpha support; changing provider/model to obtain it requires the corresponding authorization. Exact typography and UI geometry may require a frontend-rendered artifact instead.

Inside an existing Harness dispatch, keep its `run_id`, `dispatch_id`, expected stage and input versions. Return the bounded image artifact and provider evidence to the caller. Do not create a second run or directly mark approval. `ui-design-review` owns cross-artifact findings; Harness owns reconciliation, invalidation and promotion. These skills are optional for standalone use: if unavailable, return the brief, artifact and limitations without claiming their checks ran.

## Output contract

Return the brief/task identity, selected backend and actual tool, model only if exposed, reference roles and how they were passed, prompt, requested versus observed size, actual artifacts, checks performed, failures/unknowns and next scoped action.

Separate four claims: generated, inspected, visually approved and runtime verified. Image generation proves none of the last three by itself. Map evidence to an existing Harness packet only through its documented contract; do not treat the image receipt as a new state machine.

## Best Practices

- Follow explicit user backend choices and preserve prior authorization.
- Native generation uses host entitlement; API credentials and Codex login are different.
- Never put keys in prompts, chat, committed manifests or output receipts.
- No unconditional generation at SessionStart or on unrelated edits.
- Preserve original assets, approved scope and source provenance.

## References

- [Backend selection](references/backends.md): read before choosing a non-native route or handling missing capabilities.
- [Image brief and receipt](references/image-contract.md): read for repeatable delivery, traceability or Harness handoffs.
- [Prompt shape](assets/ui-image-prompt.md): use only fields relevant to the task.
- [Source notes](references/sources.md): maintenance provenance and integration boundaries.

## Keywords

UI mockup, design to image, frontend raster asset, reference image, imagegen, baoyu-image-gen, 界面设计图, 页面生图, UI 素材, 局部改图
