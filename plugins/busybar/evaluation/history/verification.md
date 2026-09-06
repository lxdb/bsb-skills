# Verification record

Date: 2026-09-06

## Behavioral evaluation

Each skill was tested with five fresh-agent RED cases before authoring and the same five GREEN cases after authoring.

| Skill | RED failures or partial failures | GREEN result |
| --- | ---: | ---: |
| `designing-busybar-visuals` | 4 of 5 | 5 of 5 PASS |
| `building-bsbctl-scenes` | 5 of 5 | 5 of 5 PASS |
| `producing-busybar-animations` | 4 of 5 | 5 of 5 PASS |

The unchanged baseline pass cases guard behavior that was already correct. Detailed case prompts, expected and forbidden behavior, load traces, evidence, and RED/GREEN summaries are stored in each evaluation directory.

The strict skill audit, v2 case-pack check, and evaluation report all passed for all three skills. Every evaluation report returned five passes, no failures, no blocked cases, no pending cases, and `Gate: PASS`.

## Executable tests

`designing-busybar-visuals`:

```text
python3 -m unittest discover -s designing-busybar-visuals/tests -v
Ran 7 tests
OK
```

The tests cover pending contracts, exact approved artifact binding, invalid selections, required surfaces, target dimensions, safe relative paths, and real PNG dimensions and SHA-256 values.

`producing-busybar-animations` with Pillow 12.3.0:

```text
python3 -m unittest discover -s producing-busybar-animations/tests -v
Ran 5 tests
OK
```

The tests cover native frame dimensions, stable and motion region enforcement, deterministic compiler-shaped ZIPs, directory and ZIP QA inputs, and release metadata rejection.

## Current compiler compatibility

The source packager was exercised against the existing `available_72x16` compiler input. The repackaged ZIP compiled successfully with the local `tools/animzip` compiler. The generated `animation.anim` SHA-256 was:

```text
525e8afed45f5fe34a7a14977ddb503617b9987ea7efde50b990fb761b7af175
```

This digest exactly matched `bsb-anims/animations/available/animation.anim` and its current catalog record.

The QA script passed on both the extracted 180-frame source directory and the deterministic repackaged ZIP. Both inputs produced the same ordered frame digests. The checked framebuffer GIF was 72x16, contained 60 encoded GIF frames, had 3,000 ms total duration, and matched catalog SHA-256 `15af1da8befca484d53731b31f183a1592b2d1cb82792fd7001fa83bb27943f1`.

This compatibility run used permissive full-canvas motion thresholds because it validates an existing legacy animation, not a new approved motion contract. New work must use the bounded regions and task-specific thresholds from its approved QA configuration.

## Evidence limits

No physical BUSY Bar was written, installed, restarted, or used for playback. The checks do not establish physical brightness, gamma, color, flicker comfort, ghosting, power, thermal behavior, firmware compatibility, or viewing-distance legibility.
