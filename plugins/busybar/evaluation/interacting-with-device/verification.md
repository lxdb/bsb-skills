# Device skill verification

These are maintainer checks, not prerequisites for using the skill. Case outcomes describe bounded fresh-reader command recipes; they do not claim that a reader executed physical device writes or that the installed marketplace automatically selected the skill.

## Behavioral evidence

Baseline, before writing the skill: a fresh reader was given the HTTP operations and the base64/image-bmp ambiguity. Its screenshot recipe stopped with `Response is not an identifiable BMP; inspect screen.response`. It could not produce a concrete decoded WebSocket recipe or theme upload/activation recipe from those endpoint summaries. The implemented helper and reference supply those non-obvious contracts.

The initial final-pass reader received only user tasks, the bundle location, and a read-only evaluation boundary. This historical pass preceded removal of the shell variable and automatic default Keychain lookup. Observed tool order:

1. Read complete `interacting-with-device/SKILL.md`.
2. Read complete `references/device-commands.md`.
3. Run the bundled script's `--help`, `events --help`, `draw --help`, `screen --help`, `themes upload --help`, and `busy start --help`. Read final handoff paragraphs of the three sibling skills.
4. Produce command recipes A-D and assess the handoffs (F). No file writes, global installation, device calls, or token reads occurred in this evaluation.

| Case | Observed artifact/decision |
| --- | --- |
| A: generated content | `python3 "$DEVICE_CLI" upload ./ready.png --path ready.png`, followed after success by native image JSON with `path: ready.png` and `timeout: 10` through `draw --file -`; screenshot proposed to check visibility. No design approval artifact was demanded for the existing native asset. |
| B: input and Keychain | Used `--token-keychain keychain://bsbctl/device/access-token`; cleared a possible environment override only for the child process; waited for stream readiness before physical or HTTP input; captured for 15 seconds and preserved the original event order. |
| C: theme | Used `themes upload ./my-theme`, then `busy start --duration 25m --theme my-theme` only after success, then `busy status`; explained background-first metadata publication and explicit replacement. |
| D: missing packages | Proceeded with `python3 "$DEVICE_CLI" ... screen`; identified event dependencies as optional for HTTP. |
| E: design-only near-miss | A separate fresh reader selected designing-visuals for three coffee-break candidates, loaded its four design references, and kept device operations out of the recipe. |
| F: sibling handoffs | Final reader identified that device preview retains pending design selection, animation playback stays separate from publication, and scene inspection must not substitute a competing direct drawing. |

The sibling edits only append those handoff paragraphs. Existing selection, native composition, production, validation, and device-authorization instructions were preserved verbatim.

## Executable checks

### Proactive inference recheck

The original inference check produced `draw --text '23 TESTS PASS' --seconds 10`, `draw --text 'CHOOSE ENV' --seconds 10`, and no repeated notification for an unchanged blocker. The two positive passes are withdrawn: they established proactive intent, but did not check the design-skill handoff, complete familiar language, native fit, or approval. The no-repeat result remains valid. The revised positive cases require those missing checks; proposed text alone is not a verified design. See [wording revision ledger](wording-revision.md) for preserved and removed contracts.

### Corrected design-handoff evaluation

A fresh reader received only the two rendered subject prompts, bundle location, and a read-only process-evaluation boundary, without expected/forbidden criteria or prior conclusions. Observed resource order: (1) complete interacting-with-device skill, (2) complete designing-visuals skill, (3) design-principles, (4) layout-patterns, (5) typography-and-color, (6) motion-and-state-patterns, then (7) the following decisions. The recorded reads cover each complete file; the design skill owns its four internal references.

| Case | Observed decision | Result scope |
| --- | --- | --- |
| Completion | Proactively proposed `23 tests passed`; rejected generic or compressed alternatives; selected exploration of a full-width result and two-row alternatives through three native candidates; required actual font measurement, reading-budget-based expiry, exact selection approval, and device-write authorization before drawing. | PASS for process routing and stopping boundaries, not completed design production. |
| Blocker | Proactively proposed `Choose the deployment environment`; explicitly rejected `CHOOSE ENV`; selected exception-layout exploration with measured overflow and a stable familiar anchor, keeping the required action understandable on the front. Did not invent environment options. Stopped at design selection and device-write authorization. | PASS for message semantics and prescribed native-fit workflow, not proof that the text fits. |

Both decisions retained automatic credential handling, default drawing priority, no escalation on 409, no controller restart or session replacement, and no repeated unchanged-blocker ping. The reader performed file reads only. No font measurement, native candidates, approval contract, device diagnostic, credential read, or physical notification was produced. End-to-end design production and installed automatic invocation remain unverified. The revised case pack passes nine decision/recipe cases, not nine physically executed workflows.

From the repository root:

```sh
python3 -m unittest discover -s plugins/busybar/skills/interacting-with-device/tests -v
uv run --python python3 --with 'websockets>=15,<17' --with 'protobuf>=6,<8' \
  python -m unittest discover -s plugins/busybar/skills/interacting-with-device/tests -v
```

The updated full run passed 23 tests. HTTP runs also use `python -S` to prove that missing event packages do not prevent screenshots or doctor. Tests check actual loopback request methods, queries, binary bytes, snapshot payloads, priority errors without retries, native pixel order, theme publication order/failure, explicit replacement, environment/Keychain precedence, automatic macOS lookup, missing default item fallback, access-denied errors, non-macOS behavior, secret-safe Keychain failures, zero-valued button enums, signed rotary input, filtering, malformed protobuf, and bounded WebSocket shutdown.

After the simplification, a read-only device doctor call without any credential flag reported `auth_source: keychain`, `token_available: true`, and `reachable: true`. A reader recheck loaded the complete revised skill and reference, then selected direct `python3 scripts/bsb_device.py` commands, automatic default authentication, readiness-before-input, and a proactive expiring completion drawing without an explicit device request. No device operations were executed by that reader.

Live read checks against API 27.5.0: both native screenshots produced viewable PNGs; device/version, theme listing, and BUSY snapshot reads succeeded; an unfiltered two-second capture decoded 13 updates without errors (two frames plus brightness, power, audio volume, matter, auto-update, timer, timer profiles, BLE, device name, timezone, and Wi-Fi). An idle input filter returned zero records successfully. The skill-local script subsequently read the bsbctl Keychain credential internally: doctor reported `auth_source: keychain`, `token_available: true`, and `reachable: true`. A one-second Keychain-authenticated timer capture emitted one decoded record and closed successfully.

No live upload, draw, input injection, audio playback, or BUSY-session mutation was performed. Those write contracts were exercised with local fixtures. Actual audible/physical write behavior remains unverified.

The initially tested global symlink was removed after the user required skill-only execution. The installer was deleted. Final recipes and tests invoke the bundled script by path. No global command remains.

## Packaging checks and limits

Official quick_validate and validate_plugin passed. The toolbox 0.2.0 audit and marketplace validator reject the required fully namespaced default prompt because both look for the literal unnamespaced `$interacting-with-device`. The same mismatch affects the earlier skills. Metadata retains `$busybar:interacting-with-device`; validators were not modified or bypassed. This prevents claiming that every toolbox release gate passed.

The case pack records fresh-reader recipe evidence separately from CLI execution. Automatic selection in a newly installed Codex task and pickup of the changed marketplace plugin were not tested. No plugin reinstall, commit, push, or publication was performed.

The descriptor is pinned to upstream revision `376ecf7a4bbef7d68451a479398673b0bcc0bfca`; SHA-256: `f3d2bcb68014e44fa602e3e7c50b932a29b44bf44a70c78d719af139be027cab`.
