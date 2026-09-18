# Design Guard Check Catalog

Use the narrowest applicable checks. Prefer repository scripts/schema validators when available.

## Mechanical checks

Good candidates for automation:
- stable IDs exist and are unique;
- navigation labels/order match the declared registry;
- route patterns and target IDs resolve;
- manifests include expected assets/skills/pages;
- referenced files/links exist;
- prompt metadata points to current spec/baseline versions;
- page-task IDs match generated artifact names;
- forbidden dynamic menu entries are absent when a machine-readable contract exists.

A mechanical check is only PASS when it actually ran against the target artifact/version.

## Semantic checks

Require judgment:
- same label used at different scopes is intentional rather than duplicate;
- actions preserve the feature contract;
- status wording matches evidence semantics;
- permissions are consistent across spec/UI/test;
- local views have not replaced parent navigation;
- error/recovery behavior is represented consistently.

## Visual continuity checks

With actual visual evidence:
- immutable shell regions preserved;
- intended active state changed and unrelated active states did not drift;
- approved component/token family remains recognizable;
- page-local content matches the target task;
- accidental menu/page additions are visible.

Do not claim pixel-level or runtime equivalence without the appropriate evidence/tool.

## Gate separation

Track independently:
1. artifact exists;
2. format/schema valid;
3. structural consistency;
4. semantic consistency;
5. visual review;
6. user approval;
7. runtime/interaction verification;
8. archival/promotion.

Passing an earlier gate never implies a later one.
