# Design principles and message routing

## Apply the principles

1. **Prefer recognition to compression.** Use the product name, familiar action, and ordinary language. Do not make the reader learn private codes such as `SLK`, `NTFN`, `NTION`, or `AUTH` to save pixels.
2. **Answer one primary question.** Lead with what happened, what needs action, how much remains, or what the current state is.
3. **Keep a stable point of entry.** Preserve a product mark, product name, state, value anchor, or action while optional detail moves.
4. **Give exceptions the space they need.** A blocking failure, requested review, mention, or security alert may replace nominal metrics.
5. **Use complete messages across time.** A marquee, a second row, or the back display may reveal a full familiar message. Start with useful words, retain a stable identity, and never require an unexplained abbreviation merely to avoid motion.
6. **Keep state and change separate.** Persistent text or shape says what is true now. A finite transition may say that it just changed.
7. **Match motion to meaning.** Use a measured fill for known progress, a loader for unknown progress, directional movement for transfer, and a finite cue for a new event.
8. **Keep anchors stable.** Values may update, but identity, labels, units, baselines, and numeric edges must not jump.
9. **Do not depend on color alone.** Pair color with complete text, a product mark, a conventional symbol, position, or shape.
10. **Measure pixels.** Approve final strings using the target font, glyph coverage, advances, and ink bounds. Character counts are planning hints only.
11. **Use black space deliberately.** Empty pixels separate groups and reduce crowding. Do not fill them as decoration.
12. **Treat digital and physical review separately.** Native previews establish geometry. Hardware establishes emitted color, glare, flicker, angle, and reading distance.

## Route the message to a pattern

Choose the message before choosing a layout. The examples use complete language intentionally.

| Message | Primary wording | Layout | Motion | Stable content |
| --- | --- | --- | --- | --- |
| Review or approval requested | `Review requested: <title>` | Product mark + headline + context | Headline marquee when measured width exceeds its viewport | Product mark; reason at the start of the headline |
| Mention or assigned work | `Mentioned: <title>` or `Assigned: <title>` | Product mark + headline + context | Optional headline marquee | Product mark and reason |
| Product setup is incomplete | `Slack setup required` | Product mark + message, or state + context | None; action can use the second row or back | Product identity and `setup required` |
| Authentication blocks work | `Sign in to <product>` or `<product> token expired` | State + context or exception takeover | Finite attention cue only if action is time-sensitive | Product name and required action |
| No current notifications | `No unread GitHub notifications` | Product mark + message | Optional one-pass marquee; then quiet | Product mark and `No unread` |
| Known progress | `<task> 63%` | Message + measured bar | Fill follows the real value | Task, number, unit, and endpoint |
| Unknown progress | `<task> is starting` or `Waiting for <dependency>` | Product mark + two rows or fixed anchor + detail | Local loader | Complete operation and dependency |
| Countdown | Event or mode plus `03:18` | Product mark + two rows or dominant timer | Discrete time changes | Event identity and timer position |
| One metric | `CPU 82%` or `Latency 140 ms` | Label over value or value + unit + trend | Numeric update only | Label, unit, and right edge |
| Two comparable metrics | `Used` and `Available` | Related columns | Numeric updates only | Column labels and value anchors |
| Several related metrics | `CPU`, `Memory`, and `Network` | Three-row telemetry | Measured fills; no ambient loop | Row labels, scales, units, and value edges |
| Blocking failure | `GitHub token expired` or `Build failed` | Exception takeover | Immediate cut; optional finite cue | Cause or action remains readable |
| Completed action | `Deployment completed` | Full-width outcome or product mark + message | One finite confirmation | Complete result |
| Optional long detail | Full title, repository, channel, or explanation | Fixed anchor + detail, pagination, or back detail | Marquee or page change | Complete summary or product identity |

## Decide what may be shortened

Keep a term unchanged when shortening adds a code the audience must learn. Product names, actions, failures, and notification reasons normally stay complete.

Use a short form only when it is already conventional for the intended audience and cannot be confused in context. Examples include `CPU`, `RAM`, `PR`, `CI`, `%`, `ms`, `GB`, and clock forms such as `03:18`. Record audience-specific terms in the design specification.

When text does not fit, apply this order:

1. Remove words that repeat visible identity or state without changing meaning.
2. Rewrite in familiar language without inventing a code.
3. Put supporting context on the second row or back display.
4. Use a measured marquee or optional pagination with a stable anchor.
5. Use a smaller supported font only when physical review confirms it remains readable.
6. Change the layout.

Reject the design when it still needs an unfamiliar abbreviation, hides a required action, drops a sign or unit, or makes the reader wait through unrelated pages to learn the core message.

## Separate importance from urgency

Importance determines space, hierarchy, and persistence. Urgency determines whether a finite attention cue is justified. A consequential operation can remain quiet while it proceeds normally. A recoverable failure can occupy the full display without pulsing forever.

The design is semantically rejected if it is compact but unclear. It remains physically unverified until observed on the device under the intended conditions.
