# Integration provenance

This skill is an original UI-design specialization of two inspected workflows:

- Codex system `imagegen` skill: native-tool-first routing, explicit CLI fallback, image input inspection, save-path and non-destructive asset handling. This system skill is supplied by the host and is not copied into the plugin.
- `baoyu-image-gen` in the supplied baoyu-skills checkout: maintained provider scripts, preference setup, reference-image capabilities, batching and separation of Codex login from API credentials. No baoyu scripts or SDK code are copied here.

The existing ui-design-spec / feature / nav / theme / continuity / visual / preview / review / harness contracts define product authority and execution responsibilities. Resolve these skills only when installed or supplied by the caller; do not auto-install them.

Source model catalogs and CLI interfaces can change. Read the actually installed backend instructions before execution. This skill deliberately does not freeze provider/model defaults from the inspected checkout.
