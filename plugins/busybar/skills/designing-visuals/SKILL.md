---
name: designing-visuals
description: Design BUSY Bar status screens and animation compositions at native resolution. Use to select layouts by scenario, fit device typography, define semantic color and motion, compare native candidates, or prepare a design specification for bsbctl scenes or standalone animations.
---

# Designing BUSY Bar Visuals

Produce three native design candidates and an approved handoff for one production path. Compose at 72x16 for the front and, when required, 160x80 for the back.

## Reference Loading Gate

| Trigger | Required load | Load before |
| --- | --- | --- |
| Define message priority, wording, or pattern | [Design principles and message routing](references/design-principles.md) | Defining the message |
| Choose message, layout, or front/back roles | [Layout patterns](references/layout-patterns.md) | Building candidates |
| Fit fonts or select product identity and palette | [Typography and color](references/typography-and-color.md) | Building candidates |
| Define state variants, freshness, motion, or overflow over time | [Motion and state patterns](references/motion-and-state-patterns.md) | Building candidates |

Read all four for a complete design. For scene output, also use `$busybar:building-bsbctl-scenes` before selecting fonts, masks, or temporal behavior that must be implemented natively.

## 1. Define the message

Identify the primary question, exact message, audience, locale, required surfaces, and expected action. Resolve freshness, priority, persistence, and privacy when they affect the meaning. Establish the product identity before choosing colors or imagery. Use the product's supplied mark and palette when available; use the documented fallback palette only when no product identity applies.

Ask only for missing choices that change the outcome. Record reversible layout assumptions. Keep the front understandable without reading the back.

## 2. Build the native candidates

Select suitable recipes from the layout catalog. Create three directions that differ in hierarchy, composition, or semantic encoding. Give each an ID and revision.

Compose every candidate programmatically on its exact pixel grid. Measure the real font and strings. Prefer complete, familiar language to private abbreviations. Keep a recognizable product or message anchor visible, numeric anchors stable, and motion in declared regions. Define the static alternative and data-quality variants before adding decorative motion.

AI imagery may provide inspiration or a useful element. It must not supply a high-resolution complete composition that is reduced into the display. Reconstruct that composition programmatically. An incorporated element must fit its native region and use explicit position, mask, and layer order.

Export exact native artifacts for every required surface. Add integer nearest-neighbor enlargements for review. Label unselected candidates `REVIEW ONLY`. Explain each candidate's useful tradeoff without repeating the design rules.

## 3. Specify and review

Copy [design-spec.md](assets/design-spec.md) for each candidate. Record regions, text metrics, palette, layer order, dynamic fields, state variants, assets, and motion. The specification must explain how to reproduce the image without guessing from pixels.

Review primary recognition, glyph coverage, clipping, grayscale meaning, frozen frames, overflow, and the loop seam when applicable. Digital review cannot establish physical brightness, flicker, or reading distance. Record physical checks as unverified unless observed.

## 4. Bind the selection

Present the three candidates and obtain approval of one exact ID and revision. Honor an explicit selection already provided by the user. Do not infer native approval from general encouragement or a high-resolution inspiration image.

Copy [busybar-design-contract.json](assets/busybar-design-contract.json). Set each artifact's relative path, dimensions, and SHA-256. Bind each completed specification as:

```json
{
  "design_spec": {
    "path": "candidates/focus-b.md",
    "sha256": "<64-character SHA-256>"
  }
}
```

For an approved selection, `approval_record` contains `actor`, the user's `text`, `approved_at`, the selected `artifacts` bindings, and the same `design_spec` binding. `artifacts` entries contain `surface`, `path`, and `sha256`. Keep `selection_gate.status` pending until selection is established.

Run from this skill directory:

```sh
python3 scripts/validate_design_contract.py /absolute/path/to/busybar-design-contract.json
python3 scripts/validate_design_contract.py --check-files /absolute/path/to/busybar-design-contract.json
```

The first check validates structure and matching approval bindings. The second checks native image dimensions and image/specification hashes. It does not parse the specification's prose or judge its design. A pending contract may leave `design_spec` null; an approved contract requires it. Existing approved schema-version-1 contracts without a specification must add and approve that binding before downstream production.

## 5. Hand off

Set `handoff.production_kind` to `bsbctl_scene` for `$busybar:building-bsbctl-scenes`, or `standalone_animation` for `$busybar:producing-animations`. Supply the JSON, selected specification, native artifacts, and required source assets together.

If production changes the approved composition or behavior, revise the candidate and its bindings. Report the selection, artifacts, verification results, and remaining physical checks. Device writes and publication require the user's authorization for those operations.

When the task includes showing a native candidate or generated asset on the physical device, use `$busybar:interacting-with-device` to upload, draw, and capture it. Device preview does not change a pending design selection into approval.
