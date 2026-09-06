---
name: producing-animations
description: Produce standalone 72x16 BUSY Bar animations from an approved native design and specification. Use for product-branded programmatic layers and motion, deterministic frames and holds, static fallbacks, source ZIPs, self-contained .anim compilation, framebuffer previews, QA, and optional catalog integration.
---

# Producing BUSY Bar Animations

Turn one approved native front-display design into reproducible frames, a compiled animation, and catalog-ready previews.

## Reference Loading Gate

| Trigger | Required load | Load before |
| --- | --- | --- |
| Implement layers, timing, holds, the runnable local-motion example, or QA | [Animation production](references/animation-production.md) | Implementing the composition |
| Package source, compile `.anim`, or integrate with a supplied catalog | [Animation format and catalog](references/animation-format-and-catalog.md) | Rendering, compiling, or integrating |

Use `$busybar:designing-visuals` if a temporal choice remains unresolved. Material changes return to design selection.

## 1. Verify the handoff

Require an approved `busybar-design-contract.json` with `handoff.production_kind=standalone_animation`, the selected specification, and its native 72x16 front artifact. Verify image and specification hashes with the design skill's validator and `--check-files`.

Check the authoring workspace and preserve existing Git changes. Use a catalog repository only when the task supplies one. Do not assume sibling clones or local tool paths. A required back-display scene belongs in `$busybar:building-bsbctl-scenes`.

## 2. Implement the composition

Translate the specification into static pixels, moving layers, masks, and a pose schedule. Compose programmatically at 72x16. Do not downscale a complete high-resolution design.

Reuse the approved static content and product identity unchanged. Do not replace GitHub, Slack, Codex, or another product palette with the fallback palette. Keep motion inside its region, preserve a recognizable message or identity anchor on every persistent frame, and produce a static fallback. Use seeded or deterministic motion and explicit frame holds.

AI may supply an element that adds value, but the compositor owns placement, masking, timing, and output. Use an exact-native element or reconstruct it programmatically. Keep source identity and required license notices with the authoring inputs. The assembled native result must match the approved revision.

## 3. Render and check

Copy [animation-qa.json](assets/animation-qa.json) and set regions, duration, frame count, and thresholds from the specification. Thresholds are review inputs, not universal safety limits.

Render contiguous source frames, `meta.json`, a static fallback, and `framebuffer.gif`. Run the bundled QA and deterministic source packager as described in the production reference. Render twice and compare frame/ZIP hashes. Test bounds, static pixel preservation, intentional timing, and the seam.

Inspect native frames and nearest-neighbor enlargements. A QA pass does not establish physical comfort, emitted color, or device playback.

## 4. Compile and integrate

Use the bundled compiler in the format reference. If a catalog repository is supplied, place only the required authored release inputs there. Let its catalog tooling generate metadata, hashes, device previews, and documentation regions.

When catalog integration applies, run its drift check after generation and its relevant tooling tests. Keep source frames, generator, specification, QA configuration, reports, and source ZIP in the authoring workspace.

## 5. Deliver

Report the approved revision, output paths/digests, frame count/duration, QA, deterministic rebuild, compiler/catalog results, and unresolved physical checks. If a required tool or check fails, report that exact boundary rather than changing the output contract silently.

Device installation/playback and publication follow the user's authorization for those operations. Reuse authorization already provided; do not treat compilation or a connected device as a request to write to it.
