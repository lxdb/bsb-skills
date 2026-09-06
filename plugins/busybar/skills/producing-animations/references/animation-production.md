# Build animation frames

## Turn the specification into layers

Read the selected native artifact and its bound design specification. Identify which pixels must stay fixed, which region moves, and what the motion means. Preserve the selected product identity and palette. Keep the primary message, familiar reason, or stable product anchor available in every persistent frame.

| Design input | Production representation |
| --- | --- |
| Text, track, and static icon | Static native layer, rendered once |
| Animated icon or texture | Separate layer with integer coordinates |
| Allowed moving area | Explicit region or mask |
| Layer overlap | Fixed drawing order and alpha rule |
| Pause or pose | Frame-duration schedule |
| Loop | Defined last-to-first transition |
| Reduced motion | Static frame or separately selectable quiet asset |

Render the background first, then supporting motion, then protected foreground text where appropriate. A mask may crop a large source layer to its intended viewport; it must not crop the primary message. Review the composite, not only each layer.

Reuse approved text pixels across frames. Use the actual device font or approved custom bitmap lettering. Avoid host-default fonts, fractional positions, smooth scaling, unseeded randomness, wall-clock input, and locale-dependent output. If an AI element is useful, retain the selected input and apply its position/mask in code. The programmatic compositor remains the source of the complete frame.

## Time the poses

The catalog playback clock is 60 FPS. Choose the rate of visible change separately. For four poses per second, hold each pose for 15 display frames. A two-second clip contains 120 display frames even if it contains only eight distinct images.

Use whole display-frame durations. The compiler can combine identical consecutive images into duration counts. Do not remove intended holds just to maximize unique frames.

Keep measured progress tied to the real value. A standalone animation cannot obtain live progress by itself; use it for a known status or decorative component, or use a bsbctl scene for live values. A loop that looks active does not prove an external process is alive.

## Runnable example: WAIT with a local loader

[render_wait.py](../examples/wait/render_wait.py) draws original bitmap lettering and an eight-pose loader. The word stays fixed at `(22,3)` with 10px ink height. Only the 16x16 left region changes. Each pose lasts 250ms. The static alternative retains the word and quiet icon.

This example teaches layer and timing construction; it does not imply approval for a production design. Its lettering is custom bitmap art, not a substitute for measuring firmware fonts in a scene.

Use a Python environment with Pillow. From this skill directory:

```sh
authoring_dir=/path/to/authoring
python3 examples/wait/render_wait.py --out "$authoring_dir/wait"
python3 scripts/animation_qa.py \
  --source "$authoring_dir/wait/frames" \
  --framebuffer "$authoring_dir/wait/framebuffer.gif" \
  --config examples/wait/animation-qa.json \
  --report "$authoring_dir/wait/qa-report.json"
python3 scripts/package_animation_source.py \
  --source "$authoring_dir/wait/frames" \
  --output "$authoring_dir/wait/wait_72x16.zip"
python3 scripts/compile_animation.py \
  --input "$authoring_dir/wait/wait_72x16.zip" \
  --output "$authoring_dir/wait/animation.anim"
```

The renderer writes `frames/meta.json`, `frames/frame_0.png` through `frame_119.png`, `framebuffer.gif`, and `static.png`. It requires a new output directory so a shorter rerun cannot leave stale source frames. QA returns success only when the source and GIF satisfy the declared configuration. The packager writes a deterministic compiler-input ZIP, and the bundled compiler writes `animation.anim` without another project checkout.

For another design, replace the drawing code and specification together. Copy [animation-qa.json](../assets/animation-qa.json) and set the frame count, stable regions, moving regions, and thresholds to that design. Do not weaken a failed region check to admit an unintended effect.

## QA configuration

| Field | Meaning |
| --- | --- |
| `expected_frame_count` | Number of display frames before compiler compression |
| `allow_transparency` | Whether source frames may contain non-opaque alpha; use false for flattened RGB output |
| `stable_regions` | Regions with a permitted changed-pixel count; use zero for fixed text |
| `motion_regions` | Regions where change is allowed; optional minimum activity catches accidentally static motion |
| `max_changed_pixels_outside_motion_regions` | Leakage outside the moving regions; normally zero |
| `max_changed_pixel_fraction_per_transition` | Frame-to-frame change budget, divided by 1152 |
| `max_mean_luminance_delta_per_transition` | Digital mean-luminance change budget |
| `max_loop_seam_changed_pixel_fraction` | Last-to-first change budget |
| `framebuffer_duration_tolerance_milliseconds` | Permitted total GIF timing difference |

The checker validates dimensions, source numbering, metadata, region bounds, motion limits, the seam, and GIF structure/duration. It records frame digests. It does not identify words, validate state semantics, certify flashing safety, or prove every GIF pixel matches the source; inspect the decoded preview and compare its poses to source frames.

Render twice into separate directories. Compare ordered frame digests and source-ZIP hashes. A deterministic ZIP uses fixed entry metadata, ordering, and content. Keep the generator and font/asset inputs with the authoring handoff.

## Inspect the output

Review the primary frame, each distinct pose/state, and the loop seam at native size and nearest-neighbor enlargement. Check grayscale and the static fallback. Look for changed letters, covered signs, clipping, ambiguous intermediate icons, and motion that dominates the message.

The last frame need not equal the first. It must advance naturally or enter an intentional hold. Do not add an extra repeated frame that changes the rhythm at the seam.

GIF uses centisecond delays. For a source with changes on a 60 FPS clock, schedule positive 10ms/20ms delays or combine held poses so total time remains correct. Do not claim uniform 16.667ms GIF playback. Verify exported delays, not only the nominal FPS.

Continue with [format and catalog integration](animation-format-and-catalog.md). Keep physical brightness, color, optical blur, frame pacing, and prolonged comfort separate from source and preview QA.
