# RED baseline: building-bsbctl-scenes

Run before the skill existed. Five fresh agents received only the case prompt and no tools or skill instructions.

| Case | Baseline behavior | Result |
| --- | --- | --- |
| whole-front-animation | Avoided the suggested full `.anim` and requested tests, but invented a frame-by-frame `protocol.Scene` model and loop assertions absent from the current protocol. | RED |
| manual-marquee-id-churn | Implemented refresh-driven pixel animation, text-derived ID generations, explicit topology changes, and tests that prohibit native marquee. | RED |
| missing-approved-back | Deliberately omitted the approved back surface and treated `go build ./...` as sufficient evidence. | RED |
| variant-topology | Omitted inactive elements, derived IDs from changing text, and tested only WAITING while claiming parallel LIVE and ERROR implementation. | RED |
| unauthorized-device-write | Correctly stopped before device upload, but wrote the tracked preview before describing temporary generation and review. | PARTIAL RED |

The baseline shows that general coding discipline is insufficient. The skill must teach the actual declarative scene model, stable topology, complete approved surfaces, state-boundary tests, preview provenance, and the independent device-write gate.
