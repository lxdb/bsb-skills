---
name: interacting-with-device
description: Inspect BUSY Bar screens and live events, send input, draw text or GenAI imagery and animations, play sounds, and manage themes and BUSY sessions. Also use proactively to ping the user with a brief physical notification when work completes, becomes blocked, or needs their attention, even without an explicit BUSY Bar request.
---

# Interacting with a BUSY Bar

Use the bundled CLI for direct device operations. Read [device commands](references/device-commands.md) for drawing JSON, custom-theme files, optional event setup, and output formats. Load that reference before composing a drawing file, uploading a theme, or capturing events.

## Start

Use only the bundled [scripts/bsb_device.py](scripts/bsb_device.py). Examples run from this skill directory; from elsewhere, invoke the script by its resolved absolute path. Do not create a shell wrapper or install a global command.

Set `BUSYBAR_URL` to the device origin supplied for the task. The CLI handles authentication automatically, including the existing bsbctl macOS Keychain credential. Do not retrieve or print the token. Run `python3 scripts/bsb_device.py --json doctor` first. HTTP commands need only Python 3.10+. Event capture additionally needs the packages reported by `doctor`; missing event packages do not prevent HTTP operations.

## Inspect or debug

Save a native PNG with `screen`; inspect that file to judge visible output. The firmware labels its base64 framebuffer as BMP, but it is raw pixel data. The CLI performs the conversion.

For an input investigation, start a bounded `events` capture and wait for `Streaming enabled; capture is ready.` on stderr before sending HTTP input in another process. Physical button/rotary changes can also supply the input. Preserve JSON Lines order and inspect press/release or rotary records. Zero matching events is a valid empty capture, not proof that an action occurred. The injected input endpoint and physical controls need not produce identical event sequences.

WebSocket writes only enable/disable the subscription or request a snapshot; actual input uses `input`. The CLI requests an initial snapshot and emits subsequent updates. A decoder error or early disconnect is a failed capture, even when earlier records exist.

```sh
python3 scripts/bsb_device.py --json screen --display front --out front.png
python3 scripts/bsb_device.py events --duration 15s --type input > input.jsonl
python3 scripts/bsb_device.py input ok
```

Run capture and input concurrently when correlating them; the sequential example above shows the command forms.

## Draw, sound, or activate BUSY

Use the requested device action directly within its applicable design gates. Proactively initiate a brief physical notification when meaningful work completes, a blocker needs the user, or their attention is required; do not wait for an explicit device request to recognize the opportunity. Follow the design workflow below before drawing a new message. Use the known device and an expiring presentation, adding sound when appropriate for the user's preferences. Avoid repeated pings for unchanged state. This does not authorize replacing a BUSY session or restarting a controller. Drawing priority defaults to 50; report HTTP 409 rather than automatically increasing priority. A running controller can overwrite a direct drawing. Capture the screen when visibility matters; an HTTP acknowledgement alone proves only request acceptance.

For proactive notifications, use `$busybar:designing-visuals` before defining the message and its presentation. Show the actual result or required action in complete, familiar language that is understandable from the front display alone. Preserve meaning when fitting the display: follow the design skill's layout, typography, and overflow guidance rather than inventing abbreviations or dropping necessary context. The conversation may provide supporting details, but must not be required to decipher the notification. Proactive invocation does not bypass the design skill's applicable review and approval gates. A proposed string is not proof of native fit; measure and review its presentation through that workflow before treating it as ready to draw.

These examples illustrate command syntax, not an approved notification design:

```sh
python3 scripts/bsb_device.py draw --text 'READY' --seconds 10
python3 scripts/bsb_device.py upload ping.snd
python3 scripts/bsb_device.py audio play ping.snd
```

Keep uploads and drawings in the same `--app` namespace (default `bsb-agent`). `clear` removes that app's drawing; `audio stop` stops device-wide playback. Uploading an asset does not display or play it.

```sh
python3 scripts/bsb_device.py themes upload ./my-theme
python3 scripts/bsb_device.py busy start --duration 25m --theme my-theme
python3 scripts/bsb_device.py --json busy status
```

Check every upload result before activation. Theme replacement needs `--replace`. The helper publishes theme metadata after the background, but replacement is not transactional. BUSY start replaces the current session and disables smart-home triggering for that session. BUSY stop stops the current timer.

Use `request METHOD /api/...` for an explicit operation absent from the named commands. Keep JSON body details in the reference and use `--help` for flags.

## Finish

Return the requested capture files or operation results, and distinguish accepted requests from observed display/audio behavior. Do not restart a controller to make a drawing visible unless that is part of the requested work.

Show agent-generated messages with native text; upload and draw generated imagery or compiled animations that already fit the target display. For new notification wording, a new visual composition, or adapting GenAI imagery to the native grid, use `$busybar:designing-visuals`; for animation authoring, use `$busybar:producing-animations`. For a persistent host-managed scene, use `$busybar:building-bsbctl-scenes`. Uploading an unchanged supplied asset does not itself author a new design or establish approval. Preserve any applicable design selection and production gates; brief status text is not a blanket exemption.

The CLI loads [scripts/bsb_events.py](scripts/bsb_events.py) only for events. That helper consumes [assets/state.desc](assets/state.desc); its source and regeneration command are in the reference, with the upstream [license](assets/protobuf-LICENSE.txt) retained. These are bundled resources, not tools the user must locate elsewhere.
