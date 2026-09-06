# Revision review

## Local reader walkthrough

This is a maintainer review of the instructions and examples. It is not a fresh-agent behavioral evaluation.

| Reader task | Result |
| --- | --- |
| Choose layouts for product notifications, status, events, progress, failures, and related metrics | Message matrix, fourteen coordinate recipes, and ASCII spatial schematics provide the choices and their limits |
| Resolve stock-icon margins and text overflow | Separate 16/14/12px recipes; measured fitting and complete-message marquee latency are specified |
| Preserve complete language | Familiar product names, reasons, causes, and actions precede marquee, back detail, or layout changes; private codes are rejected |
| Apply product identity | GitHub, Slack, Codex, and fallback colors are self-contained; product palettes take precedence |
| Translate a native visual into a scene | Bound Markdown specification, region map, GitHub notification code/asset, and calendar/telemetry variations provide the route |
| Handle notification states | Scene example exercises review, mention, empty, setup, and connection-failure copy with unchanged front anchors/topology |
| Choose motion and respond to newer state | Pattern table includes fixed regions, timing, stop/interruption, and static equivalents |
| Produce and package animation frames | Runnable WAIT example follows the documented source, QA, ZIP, and bundled compiler route |
| Use the skills without research links or sibling clones | Operational guidance, fallback colors, compiler format, and compiler are local; only Python and Pillow are needed for standalone production |

## Executable verification

| Check | Result |
| --- | --- |
| Skill metadata (`quick_validate.py`) | All three skill entrypoints pass |
| Active documentation | 17 Markdown files pass local-link, fence, JSON, and case-route checks |
| Design contract tests (`python3 -m unittest discover -s plugins/busybar/skills/designing-visuals/tests -v`) | 10 tests pass, including specification binding, changed/missing files, and path escape rejection |
| Animation tests (`python3 -m unittest discover -s plugins/busybar/skills/producing-animations/tests -v`) | 11 tests pass with Pillow 12.3.0, including bundled compilation, opacity rejection, deterministic generation, fixed text, bounded motion, decoded GIF poses, and frame holds |
| GitHub notification scene (`GOWORK=off go test ./...`) | Passes in an isolated module against the local bsbctl SDK; checks full copy, GitHub colors, native asset size, marquee contracts, invalid inputs, anchors, and topology |
| GitHub source design review | Current production scene, contract tests, 72x16 preview, and contact sheet inspected; the example preserves its fixed mark and independent text viewports |
| WAIT production path | Native frames pass QA; repeated source ZIPs are byte-identical; bundled compilation is byte-compatible with the independently verified encoder |
| Catalog integration | Not rerun for this revision; the bundled compiler emits the same verified WAIT bytes, and catalog work is now conditional on a supplied repository |
| Visual review | All eight native and enlarged WAIT poses and the catalog-generated preview inspected; fixed text and local motion match the example contract |
| Patch whitespace (`git diff --check`) | Passes |

The compiled WAIT animation has SHA-256 `3fbe0a5e20ad434f4f7176440e7fdb9ea12aa87048e0aeb69d6ce5e41aae5598`. Its source ZIP has SHA-256 `e73ba613ae5f78a1492254fe584db343cd40f86db9c7bed365f61bbf7d8355a1`.

Fresh-agent case packs remain pending; earlier agent results are archived. Mermaid workflow and state source was checked structurally but not rendered with a Mermaid CLI in this environment. The scene example was not rendered on a device. Physical brightness, reading distance, flicker, and hardware playback remain unverified. No device writes or publication were performed.
