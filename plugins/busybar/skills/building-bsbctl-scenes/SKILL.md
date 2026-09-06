---
name: building-bsbctl-scenes
description: Translate an approved native BUSY Bar visual and design specification into bsbctl protocol.Scene code. Use for region-to-element mapping, fonts and anchors, dynamic state bindings, native countdowns and marquee, stable topology, tests, and faithful preview comparison.
---

# Building bsbctl Scenes

Implement an approved design using native scene elements and the target plugin's existing patterns.

## Reference Loading Gate

| Trigger | Required load | Load before |
| --- | --- | --- |
| Convert regions, use the GitHub example, adapt calendar or telemetry, or compare output | [Scene construction](references/scene-construction.md) | Translating the design |
| Select scene fields, geometry, fonts, assets, or supported motion | [Scene protocol](references/scene-protocol.md) | Translating the design |

## 1. Verify the inputs

Require `busybar-design-contract.json`, its selected `design-spec.md`, and the approved native artifacts. The selection must be approved, the production kind must be `bsbctl_scene`, and every required surface must be included.

Run the bundled validator from the design skill directory:

```sh
python3 scripts/validate_design_contract.py --check-files /absolute/path/to/busybar-design-contract.json
```

Check the intended bsbctl worktree, repository instructions, and staged/unstaged/untracked changes. Compare the protocol reference with `sdk/protocol/presentation.go`. Read the target view, reducer, tests, and preview path before editing.

## 2. Translate the design

Map each region to a semantic element ID, payload, display, coordinates, font, color, alignment, and data binding. Follow the construction guide's worked example.

Build the representative static state first. Use native text for changing values, rectangles for tracks/fills, and countdowns for deadlines. Reuse packaged or stock assets for approved imagery. Convert marquee speeds to pixels/minute and delays to milliseconds.

Preserve the specification's meaning, geometry, layer order, and source assets. Check actual ink bounds; field validation does not prove text fit. If the protocol cannot express an effect, resolve the supported representation before adding code. Route a needed standalone asset to the animation skill instead of creating a per-refresh animation loop in the scene.

## 3. Bind runtime states

Keep IDs, payload kinds, order, and anchors stable across updates within a view. Change the relevant values, colors, or fill widths. Use a positive-width fill painted in the track color at zero.

Map stale, missing, invalid, failure, and recovery according to the specification. Keep valid zero distinct from missing data. Preserve complete product names, reasons, and actions; use a stable identity plus measured marquee instead of private abbreviations when needed. Let the reducer and host own freshness, priority, expiry, and interruption; the view maps their result into a scene.

## 4. Verify fidelity

Add focused tests for meaningful state changes and numeric boundaries. Check `Scene.Validate()`, semantic text, required surfaces, stable anchors/topology, zero/full fills, and the approved overflow behavior. Use a failing regression test when correcting a defect.

Format changed Go files and run the target package tests. Include relevant protocol or preview tests when their behavior is affected. Do not add a broad test suite for unchanged repository behavior.

Render deterministic scenes from production paths with fixed data/time. Compare the native outputs with the approved artifacts. Check the preview renderer's supported elements and fonts; stored fixtures do not verify changed code. Keep compilation, software rendering, device capture, and physical observation distinct.

## 5. Deliver

Report the selected design, files changed, tests, native comparisons, and any unverified rendering or hardware behavior. Do not claim a scene matches the approved pixels when the required renderer was unavailable.

Obtain a revised selection if implementation requires a material design change. Use already authorized device operations only for their stated purpose; building a scene alone does not request installation, restart, or publication.
