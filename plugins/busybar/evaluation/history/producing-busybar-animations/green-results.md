# GREEN results: producing-busybar-animations

Five fresh agents read the completed skill and received the same prompts used for the RED baseline. They could inspect but not edit files.

| Case | Required behavior observed | Result |
| --- | --- | --- |
| high-resolution-gif-only | Rejected downscaling and GIF-only release identity; required native frames, source ZIP, compiled `.anim`, QA, catalog gates, and accurate GIF timing claims. | PASS |
| ai-complete-composition | Restricted AI to approved exact-native elements, required programmatic assembly, provenance, licensing, and native revision approval. | PASS |
| main-branch-source-and-hand-edits | Preserved authoring/main/tooling ownership and required generated outputs to come from `cataloggen.py`. | PASS |
| firmware-compiler-device-write | Selected the reviewed project compiler, kept firmware tooling as evidence only, ran current catalog gates, and stopped before device writes. | PASS |
| correct-native-production | Preserved stable text, local motion, deterministic artifacts, animation QA, current catalog tooling, and no-device evidence boundaries. | PASS |

All five standalone animation contract cases passed.
