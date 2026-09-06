# Notification wording revision ledger

| Previous contract | Previous evidence or location | Final home or status | Rationale | Verification case |
| --- | --- | --- | --- | --- |
| Require a supplied URL before checking the device | Start section; observed chat stopped without a default attempt | Rephrased in Start and command reference; CLI now defaults to busylib local origin | Try the default before treating an absent URL as a blocker; preserve explicit-origin precedence and error distinctions | default-origin-first; DeviceURLTests |
| Proactively infer completion and attention notifications | Skill description and Draw section | Preserved in description and Draw section | Invocation remains proactive; presentation follows the design skill | infer-completion-screen, infer-blocker-screen |
| Compress text to fit; explain it in conversation | Proactive paragraph; prior CHOOSE ENV recipe | removed-stale | Conflicts with designing-visuals recognition, complete language, and independent front meaning | infer-blocker-screen |
| Brief text bypasses design approval | Finish section | removed-stale | No blanket bypass of the owning design workflow | infer-completion-screen |
| Direct execution of existing requested assets | Finish section | Preserved, scoped to unchanged supplied assets | Uploading does not author a new composition or establish approval | generated-content |
| No repeat pings or session/controller disruption; preserve priority errors | Draw section | Preserved verbatim except notification-routing wording | Notification inference does not expand disruptive authority | unchanged-blocker-no-repeat; both positive cases |
| HTTP, events, credentials, uploads, themes, BUSY, output evidence, sibling production handoffs, packaging limits | Other skill sections, scripts, reference and verification.md | Unchanged | Wording-only correction; runtime contracts and release limitations remain | Existing six command/handoff cases and recorded 23-test run |
