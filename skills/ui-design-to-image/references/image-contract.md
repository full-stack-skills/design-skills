# Image brief and receipt

Use a compact standalone brief or enrich the existing task contract. These fields are a specialist handoff, not a replacement product specification or a second task ledger.

## Brief

- `task_id`, `page_id` / `surface_id` or `asset_id`.
- `input_versions`: exact feature/navigation/theme/continuity versions that apply.
- `intent`: concept / reference-guided-concept / edit / raster-asset.
- `output_role`: preview-only / project-asset / design-candidate.
- `requested_viewport`, `requested_count`, `destination`.
- `exact_text`, layout hierarchy, tokens, demonstration-data labels.
- `references`: path or accessible image identity, role and approved scope/hash if known.
- `change_budget`: mutable, immutable and contract-variable regions.
- `backend_choice`, authorized external route and generation budget where supplied.
- `unresolved`: blockers versus non-blocking visual assumptions.

For frontend viewports, use 390×884 / 768×1024 / 1280×1024 unless another contract is authoritative. Raster pixels and CSS logical pixels are distinct. Record output approximation and any intentional crop or padding; do not promise exact-size generation.

## Receipt

Record only observed values:

- brief/task and parent dispatch identity when present;
- actual backend/tool, exposed model/request ID if available;
- prompt location or prompt text; never credentials;
- references actually passed, and image-conditioning versus text reconstruction;
- selected output path/inline identity/link and observed width/height/hash if retrievable;
- generation outcome: completed / failed / unknown / not-run;
- author inspection findings, changed regions, limitations;
- review evidence and scoped user approval references only when they actually exist.

These generation outcome labels belong only to this receipt. In Harness, use the packet's allowed evidence statuses (`pass`, `fail`, `unknown`, `needs-decision`) and expected stage. `pass` for the candidate stage means the artifact/evidence satisfies that stage, not that the user approved it or the UI runs.

A timeout with no identifiable artifact is unknown. A saved prompt without generation is not-run. An image with misspelled labels is generated but has failed text inspection. A local file existing does not prove its provenance.

## Review dimensions

Check required labels, page identity, navigation hierarchy/activation, theme, baseline structure, change budget and requested layout at each target. Separate deterministic dimensions/file checks from model visual judgment. Contrast inferred from a bitmap is provisional; check actual frontend colors and accessibility when implemented.

User approval remains a scoped decision with the actual artifact identity. Changing the upstream brief invalidates only dependent candidate/review receipts; it never overwrites historical approval.
