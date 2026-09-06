# Device commands

Run `python3 scripts/bsb_device.py` from this skill directory, or use the script's resolved absolute path from elsewhere. No global command or installation is needed. Global `--url`, `--app`, `--token-keychain`, and `--timeout` precede the command. `--json` works anywhere. Origin precedence is `--url`, nonempty `BUSYBAR_URL`, then `http://10.0.4.20` (the busylib local default). Run the bounded `doctor` check even without URL configuration; ask for a reachable address only after connection failure, reporting the origin attempted. An explicit origin is not silently replaced by the default. The device's local HTTP API may work without a token.

## Setup and output

HTTP commands require Python 3.10+ and no packages. The CLI uses `BUSYBAR_TOKEN` when set, otherwise automatically reads the existing bsbctl credential on macOS (service `bsbctl`, account `device/access-token`). No authentication flag is needed. A missing default item permits an unauthenticated request; access failures remain errors. Other platforms use no token unless configured. For a nonstandard Keychain item only, override with `--token-keychain keychain://service/account`. Lookup captures `/usr/bin/security` output internally with a timeout; it never modifies Keychain or stores tokens. `doctor` reports only token availability and source (`env`, `keychain`, or `none`).

Only `events` needs `websockets>=15,<17` and `protobuf>=6,<8`. Use an existing virtual environment with those packages, or an isolated uv invocation (substitute the actual bundled script path):

```sh
uv run --python python3 --with 'websockets>=15,<17' --with 'protobuf>=6,<8' \
  python scripts/bsb_device.py --url http://10.0.4.20 events --duration 30s
```

For a virtual environment, install the two packages with that environment's `python -m pip install 'websockets>=15,<17' 'protobuf>=6,<8'`, then run the script with that Python. No automatic package installation occurs. If `doctor` reports missing event packages, HTTP remains usable.

Normal output is indented JSON; `--json` produces compact JSON and machine-readable errors on stdout. Events always emit JSON Lines; readiness and completion messages go to stderr. Exit 0 means success, 1 means request/data/setup failure, 2 means invalid CLI arguments, and 130 means interrupted. Invalid captures retain already emitted lines and finish nonzero. Tokens are redacted from diagnostics. Raw API results, including deliberate sensitive reads, are returned as requested.

| Family | Success shape |
| --- | --- |
| `status`, `input`, `draw`, `audio`, `busy`, `themes list`, JSON `request` | API pass-through, e.g. `{"success":true}` |
| `doctor` | `{"url":"http://device","token_available":false,"auth_source":"none","reachable":true,"version":{"api_semver":"27.5.0"},"events":{...}}` |
| `screen`, `request --out` | `{"path":"/output/file","bytes":123,...}`; screens also include display, width and height |
| `upload` | `{"application_name":"bsb-agent","path":"ready.png","result":{...}}` |
| `themes upload` | `{"theme":"my-theme","uploaded":["themes/my-theme/background.png","themes/my-theme/theme.json"]}` |
| `events` | `{"received_at":"...","device_timestamp":"123456","type":"input","data":{"button_event":{"button":"OK","action":"PRESS"}}}` |

Errors use `{"error":{"message":"...","status":409}}`; non-HTTP failures have null status. Theme upload errors also include an `uploaded` array, which may be empty. Downloads require a new filename and never silently overwrite an existing capture. Durations accept `ms`, `s`, `m`, or `h`; bare numbers mean seconds. Text expiry uses whole positive seconds.

## Screens and input

`screen --display front --out front.png` writes 72x16 RGB PNG. `--display back` writes 160x80 grayscale pixels in RGB PNG. The underlying `/api/screen` returns base64, not an encoded BMP: front bytes are BGR888 and back pixels are packed low-nibble-first L4. The CLI validates lengths and converts both without Pillow.

`input KEY` sends one `POST /api/input?key=KEY`. Keys: `up`, `down`, `ok`, `back`, `start`, `busy`, `custom`, `off`, `apps`, `settings`. `up` and `down` are the available HTTP rotary-style actions, not arbitrary encoder deltas.

## Upload and draw

`upload ready.png --path ready.png` sends raw bytes to `/api/assets/upload` under `--app` (default `bsb-agent`). Remote paths are relative to that application's assets, at most 64 characters, using letters, digits, dots, underscores, hyphens, and slashes. Existing asset paths are overwritten.

For an existing native image, upload it and send this JSON through `draw --file drawing.json`:

```json
{
  "elements": [
    {"id":"ready","type":"image","path":"ready.png","display":"front","x":0,"y":0,"align":"top_left","timeout":10}
  ]
}
```

Use `type: "animation"` and an uploaded `.anim` path for animations. Native text, rectangle, countdown, and xpmbitmap elements can also be supplied. `draw --file -` reads an object from stdin. The CLI supplies `application_name`; an explicitly different name in the JSON requires matching `--app`. JSON priority is retained unless `--priority` overrides it. The device validates the full native element schema; the CLI does not duplicate it.

`draw --text 'READY' --seconds 10` uses centered small white ASCII text on the front, priority 50, with a 10-second expiry. A higher-priority application can reject it with 409. The default does not preempt an active BUSY session at priority 90. `clear` deletes only the selected application drawing. There is no automatic controller restart, restoration, or priority escalation.

## Audio

Upload a supplied `.snd` file, then `audio play ping.snd`. For an existing stock asset, use `audio play shared/sounds/NAME.snd --stock` with a verified device path; stock filenames are not assumed. `audio stop` is device-wide. HTTP 410 means no audio is playing and remains an API error. Sound generation/conversion is outside this CLI.

## Themes and BUSY sessions

A supplied theme directory contains `theme.json` and its referenced `.png`, `.bin`, or `.anim` background. Example metadata:

```json
{"bg_path":"background.png","order":100}
```

`themes upload ./my-theme` uses the directory basename as its name; `--name NAME` overrides it. The name follows the application-name character rules and is at most 32 characters. The helper validates `bg_path` within that directory, uploads the background to application `busy` at `themes/my-theme/background.png`, and then uploads `themes/my-theme/theme.json` with `bg_path` rewritten to `/ext/apps_assets/busy/themes/my-theme/background.png`. It preserves the local files and metadata order. Existing themes require `--replace`. The default built-in `busy` name is reserved.

Only the referenced background and metadata are uploaded. Failure stops the sequence and reports completed paths; it does not delete files or start a session. Replacement is not atomic: updating a background can affect an existing theme even if the later metadata write fails.

`themes list` lists `/ext/apps_assets/busy/themes`. `busy start --duration 25m --theme my-theme` activates a SIMPLE snapshot, while `--infinite` activates an INFINITE snapshot. The default theme is `busy`. Starts use a fresh card UUID, current timestamp, unpaused state, `show_work_phase_only=false`, and `trigger_smart_home=false`. They replace the current session without editing saved profile slots. `busy stop` sends NOT_STARTED with the current theme settings. `busy status` reads back the snapshot; use it to check the resulting type and theme.

## Events

`events --duration 15s --type input` connects to `/api/status/ws`, sends `{"enable":true,"send":"all"}`, and captures updates. Start it in a separate running process and wait for the readiness message before injecting input. `--follow` continues until interrupted. `--type` is a protobuf field name such as `input`, `timer`, `frame`, or `power`; omitting it emits all updates. An invalid type fails before connection. Frame records retain their protobuf metadata and base64 payload; use `screen` for a viewable still image.

Both received wall-clock time and the device's original timestamp are kept. The latter is a decimal string to preserve fixed64 precision; do not assume it shares the host clock's epoch. Proto3 defaults are emitted, so zero-valued OK/PRESS enums remain readable. Text messages are emitted as `type: "text"` even when a type filter is set. Device errors are never hidden by filtering. The CLI does not reconnect or silently discard an undecodable update. The server can throttle its own publication; this is an ordered capture of received updates, not a guarantee of every physical event.

## Raw requests

`request GET /api/status/power` returns JSON. Use `request GET '/api/storage/read?path=/ext/FILE' --out file.bin` for raw bytes. `request PUT /api/... --body payload.json` performs exactly the named method. GET/HEAD reject bodies. The configured origin and token are reused, redirects are rejected, and another origin cannot be supplied as the request path.

## Schema provenance and regeneration

The bundled `assets/state.desc` was generated from `busy-app/busybar-protobuf` revision `376ecf7a4bbef7d68451a479398673b0bcc0bfca`, using its `state.proto` and transitive imports. The upstream MIT license is retained in `assets/protobuf-LICENSE.txt`. Runtime users need neither protoc nor a firmware checkout.

For maintainers, from this skill directory with a checkout at that revision:

```sh
protoc --proto_path=/path/to/busybar-protobuf --include_imports \
  --descriptor_set_out=assets/state.desc state.proto
```

HTTP request shapes were checked against the device's OpenAPI 27.5.0. WebSocket subscription/auth behavior and theme layout were also checked against the firmware handlers. Revisit the pinned schema when a firmware change introduces unknown event fields.
