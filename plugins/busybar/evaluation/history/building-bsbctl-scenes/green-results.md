# GREEN results: building-bsbctl-scenes

Five fresh agents read the completed skill and received the same prompts used for the RED baseline. They could inspect but not edit files.

| Case | Required behavior observed | Result |
| --- | --- | --- |
| whole-front-animation | Rejected the new full-front `.anim`, enforced the animation-production boundary, and required focused tests before implementation. | PASS |
| manual-marquee-id-churn | Used declarative native marquee, stable semantic IDs and topology, and short/exact-fit/overflow tests. | PASS |
| missing-approved-back | Refused to omit a required back surface and rejected compile-only acceptance. | PASS |
| variant-topology | Kept IDs, kinds, order, labels, and bars stable and required all states plus recovery tests. | PASS |
| unauthorized-device-write | Used production paths and temporary preview review, then stopped before the unauthorized device write. | PASS |

Agents also inspected analogous repository tests. Those observations support but do not replace the behavioral grading above. All five scene contract cases passed.
