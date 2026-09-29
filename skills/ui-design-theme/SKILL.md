---
name: ui-design-theme
description: Select, reuse or define a color and typography theme for UI and visual artifacts. Preserve existing brand choices and return a versioned theme contract for visual production and continuity checks.
license: Apache-2.0
---

# UI Design Theme

## When to use this skill

Use when colors/fonts need a shared contract, when exploring a new visual direction, or when applying an already selected theme to new artifacts. This is a color/typography theme library, not a complete component design system.

## How to use this skill

1. Read the canonical task, current brand/design-system sources and any explicit theme choice. Reuse an applicable choice without asking again. Conflicting approved sources require a decision; do not silently replace them.
2. If no theme has been selected, present applicable options using `theme-showcase.pdf` and the bundled theme files, or propose a custom theme based on actual requirements. A proposed theme remains proposed until selected or authorized; unavailable preview tools must be reported honestly.
3. Read the selected theme file. Produce a theme contract containing `theme_id`, `version`, `source`, `maturity` (proposed/selected/approved), colors, typography, fallback fonts, contrast checks, allowed overrides and unresolved decisions. Do not infer approval from file existence.
4. Write or reference the contract in the canonical design package. ui-design-spec includes its identity/version in the design task; ui-design-continuity fixes the permitted variations; ui-design-visual applies it; ui-design-review checks actual use. Do not create duplicate task status or dispatch a new run.
5. For a standalone apply request, style the requested artifact within scope and return the contract plus changed artifacts. Inside a Harness task, return the bounded result/evidence to its caller, without launching another workflow.

## Best Practices

- Existing user choices and approved brand sources take precedence over presets.
- Theme changes affecting an approved baseline are explicit changes with affected artifacts; do not silently restyle siblings.
- Check actual color combinations and font availability; preset selection alone does not prove accessibility or rendering fidelity.
- Record required approval separately from theme generation. Reuse explicit prior selection; do not add redundant confirmation.
- Preserve source licenses and avoid adding promotional branding to user artifacts.

## Themes Available

The following 10 themes are available, each showcased in `theme-showcase.pdf`:

1. **Ocean Depths** - Professional and calming maritime theme
2. **Sunset Boulevard** - Warm and vibrant sunset colors
3. **Forest Canopy** - Natural and grounded earth tones
4. **Modern Minimalist** - Clean and contemporary grayscale
5. **Golden Hour** - Rich and warm autumnal palette
6. **Arctic Frost** - Cool and crisp winter-inspired theme
7. **Desert Rose** - Soft and sophisticated dusty tones
8. **Tech Innovation** - Bold and modern tech aesthetic
9. **Botanical Garden** - Fresh and organic garden colors
10. **Midnight Galaxy** - Dramatic and cosmic deep tones

## Theme Details

Each theme is defined in the `themes/` directory with complete specifications including:
- Cohesive color palette with hex codes
- Complementary font pairings for headers and body text
- Distinct visual identity suitable for different contexts and audiences


## Output contract

Return the theme identity/version/source/maturity, palette and typography, fallback behavior, allowed overrides, checks actually performed, unresolved issues and affected artifacts. The parent task references this contract as an authority; theme selection does not require a new Harness state.

## Keywords

UI theme, palette, typography, brand inheritance, theme contract, 配色, 字体, 主题, 品牌继承
