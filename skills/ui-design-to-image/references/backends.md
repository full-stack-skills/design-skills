# Image backend selection

This skill integrates workflow contracts; it does not bundle an image model, expose an MCP service or bypass a backend's current instructions.

| Route | Required evidence | Action |
|---|---|---|
| Codex native | Callable native image-generation tool | Read current imagegen instructions; generate/edit through that tool |
| Explicit baoyu | Available baoyu-image-gen skill, its real scripts, selected backend and prerequisites | Read its current SKILL.md and matching provider/setup references |
| Explicit imagegen CLI | Available maintained CLI and authorized API/model route | Follow current imagegen CLI workflow |
| No runnable backend | No verified route | Deliver prompt/brief only; report generation unavailable |

## Native Codex

Use the native tool exposed by the current host, not a guessed HTTP endpoint or copied system skill. Tool schemas are authoritative for parameters; do not assume width/height, masks, model, output-path or batch parameters exist. Inspect local image inputs before editing. Use the documented reference mechanism and preserve transparency when required and supported.

Follow current imagegen save-path rules. When the tool returns a local artifact under host-managed storage and the asset belongs to the project, copy the selected artifact into that project. If no local path was returned, do not guess it or download remote media merely to work around host restrictions.

No API key is required for a native entitled route. Size or batch requests alone do not authorize an API fallback.

## baoyu-image-gen

Resolve the actual installed `baoyu-image-gen` directory; do not hardcode a maintainer's E: or C: path. Reuse `scripts/main.ts` and the provider references instead of creating another SDK runner.

The inspected source requires preferences to be resolved through `EXTEND.md` before generation. Reuse existing preferences and explicit user choices. If first-time setup is needed, follow its setup interaction; do not silently create settings or collect credentials in chat. Inspect local credentials only for availability, not by printing their contents.

Use an installed Bun/runtime. Do not silently use `npx -y` to download a missing runtime. Provider/model support changes: verify selected references, sizes, edits and transparency against the installed backend and its maintained provider documentation before claiming support.

For an explicitly chosen baoyu route, the inspected script accepts:

```text
<runtime> <baoyu-skill>/scripts/main.ts
  --promptfiles <saved-prompt.md>
  --image <project-output.png>
  --provider <chosen-provider>
  --model <chosen-model>
  --ref <actual-reference-files>
```

This is an argument shape, not a ready command. Omit optional arguments not required or supported; construct argv safely and use the current CLI help. A prompt-only style reconstruction is not equivalent to supplying `--ref`.

The dedicated `codex-cli` provider uses a logged-in Codex CLI and must be explicitly selected; it is not the OpenAI API provider. Do not place a Codex OAuth token in `OPENAI_API_KEY`. Selecting this nested CLI route also requires checking recursion boundaries: it must generate the image, not reopen the parent UI workflow.

For batching, reuse saved prompts and the maintained batch format. Honor the chosen backend's own concurrency and retry bounds; no extra outer retries or unrequested variants.

## Failure handling

- Missing tool/runtime/credential: report the specific prerequisite and continue brief work when useful.
- Native route unavailable: offer available alternatives; switch only within explicit authorization.
- Unsupported reference/edit/alpha: do not omit the constraint silently. Choose an already authorized capable route or request a decision.
- Unknown paid request outcome: reconcile returned artifacts/request identifiers first. If the backend has no query capability, report unknown; a second request requires accepting potential duplicate cost.
- Failed generation does not invalidate an already approved design baseline. Candidate changes and dependent review evidence are handled by the parent workflow.
