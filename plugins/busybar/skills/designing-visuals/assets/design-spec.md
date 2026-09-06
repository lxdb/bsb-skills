# Design specification

Replace the placeholders. Keep only the rows that the task needs. Use one file per candidate revision.

## Message and state

- Candidate: `<id>`, revision `<number>`.
- Primary question: `<what the viewer must know or decide>`.
- Primary answer: `<exact copy/value and meaning>`.
- Context: `<identity, unit, expected action>`.
- Product identity: `<product name, supplied mark, supplied palette, or fallback palette>`.
- Viewing context: `<distance, duration, front/back use>`.
- State policy: `<freshness, missing/invalid data, failure, privacy>`.

## Surface and layout

| Surface | Native size | Purpose | Native artifact |
| --- | --- | --- | --- |
| Front | 72x16 | `<primary role>` | `<relative PNG/GIF path>` |
| Back, if required | 160x80 | `<supporting role>` | `<relative PNG/GIF path>` |

Regions use `(x,y,width,height)` with exclusive right/bottom edges. Record drawing anchors separately from ink regions.

Add a spatial schematic only when it improves review. Use ASCII for an exact pixel-oriented layout or Mermaid block syntax for a clear block layout. Keep the table below as the exact contract.

| Layer order | Region / role | Bounds | Static or dynamic | Font / asset | Anchor and alignment | Color |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | Background | `<bounds>` | Static | Solid rectangle | Top-left | `<RGB/RGBA>` |
| 1 | `<primary>` | `<bounds>` | `<binding>` | `<exact font or asset>` | `<x,y,align>` | `<role and code>` |

## Text and assets

| String / extreme value | Font and rasterizer | Advance width | Ink bounds | Overflow behavior |
| --- | --- | --- | --- | --- |
| `<copy>` | `<file, size, renderer>` | `<px>` | `<left,top,right,bottom>` | `<complete fit, measured marquee, second row, back detail, or layout change>` |

| Asset | Source size | Viewport / mask | Position | Digest | License / notice location |
| --- | --- | --- | --- | --- | --- |
| `<relative path>` | `<width,height>` | `<bounds or none>` | `<x,y>` | `<sha256>` | `<required notice or original work>` |

## State variants

| Input / event | Primary copy or value | Secondary cue | Geometry that changes | Exit or recovery |
| --- | --- | --- | --- | --- |
| `<representative state>` | `<exact result>` | `<cue>` | `<fill endpoint or none>` | `<condition>` |

Include valid zero/full values, widest text, failure, and data-quality states when applicable. State which fields are fixed across the variants.

## Motion

| Purpose | Stable region | Moving region | Timing / holds | Loop and interruption | Static alternative |
| --- | --- | --- | --- | --- | --- |
| `<none or semantic purpose>` | `<bounds>` | `<bounds>` | `<units>` | `<stop condition>` | `<artifact or state>` |

For animation output, state the playback rate, pose schedule, duration, alpha policy, and seam behavior. For a scene, state which native primitives implement the motion.

## Verification and handoff

- Native geometry and string measurements: `<result>`.
- State, grayscale, frozen-frame, and overflow review: `<result>`.
- Physical display checks: `<observed result or unverified>`.
- Production target: `bsbctl_scene` or `standalone_animation`.
- Approval: recorded in `busybar-design-contract.json`; this file does not approve itself.

After the specification is final, record its relative path and SHA-256 in the candidate's `design_spec` field. Copy that binding into the approval record when the user approves the candidate. Revise both bindings if this file changes.
