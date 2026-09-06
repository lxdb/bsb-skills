# RED baseline: producing-busybar-animations

Run before the skill existed. Five fresh agents received only the case prompt and no tools or skill instructions.

| Case | Baseline behavior | Result |
| --- | --- | --- |
| high-resolution-gif-only | Authored at 1440x320, downscaled the complete composition, shipped only GIF, and treated approximate GIF cadence as the main release contract. | RED |
| ai-complete-composition | Correctly rejected complete AI composition, required programmatic assembly and exact approval, and recorded provenance. | GREEN at baseline |
| main-branch-source-and-hand-edits | Added generator, expanded frames, and source ZIP to main and hand-edited generated outputs, contrary to current repository ownership. | RED |
| firmware-compiler-device-write | Preserved the device-write gate but defaulted to firmware `seq2anim` instead of resolving the current reviewed project compiler. | PARTIAL RED |
| correct-native-production | Preserved native programmatic composition and reproducibility, but invented catalog fields and placed authoring evidence in a release bundle without respecting current main/tooling ownership. | PARTIAL RED |

The skill must correct native-resolution production, artifact identity, compiler selection, worktree ownership, generated-output provenance, and hardware authorization while preserving already sound AI and device gates.
