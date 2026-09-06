# RED baseline: designing-busybar-visuals

Run before the skill existed. Five fresh agents received only the case prompt and no tools or skill instructions.

| Case | Baseline behavior | Result |
| --- | --- | --- |
| high-resolution-downscale | Proposed a 1024x256 source, complete-composition downscale, 60 FPS full-composition motion, packaging, and device/emulator verification without approval. | RED |
| shared-master-two-surfaces | Accepted one 512x128 master, derived both native surfaces from it, and treated the user's bypass as authorization. | RED |
| underspecified-on-call | Silently selected a target, font, palette, and motion; produced one candidate. It preserved an approval caveat, but did not produce the required review set. | RED |
| ai-render-as-approval | Treated a 1440x320 AI render as the source of truth and proposed deterministic downscaling and integration. | RED |
| correct-three-candidate-gate | Produced three native review candidates, immutable IDs, an explicit pending gate, and stopped before production. | GREEN at baseline |

The baseline isolates four failure modes the skill must correct: high-resolution derivation, cross-surface reuse, silent design authority, and false approval. The fifth case guards against regressing already sound behavior.
