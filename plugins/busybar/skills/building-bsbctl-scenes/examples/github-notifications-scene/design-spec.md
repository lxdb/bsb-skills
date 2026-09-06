# GitHub notification scene specification

Candidate `github-notification-example`, revision 1. This is an instructional example, not an approved production candidate.

## Message

The front identifies GitHub and explains the notification with familiar language. The 16x16 GitHub mark remains fixed. The headline starts with the reason, such as `Review requested` or `Mentioned`, followed by the full subject. The second row shows a repository or a complete action.

Do not substitute codes such as `GH`, `REV`, `NTFN`, or `AUTH`. A long headline uses the native marquee. The back contains full context and controls.

## Product identity

| Role | Color |
| --- | --- |
| Canvas | `#0D1117FF` |
| Primary text | `#F0F6FCFF` |
| Secondary text | `#8B949EFF` |
| Mention / information | `#58A6FFFF` |
| Review / action | `#D29922FF` |
| Failure | `#F85149FF` |

Use the bundled `assets/github-mark.png` unchanged at 16x16. Its SHA-256 is `1f7ef0c666e09d5792c9e81b4a042f46c270223e2dc72521e6a0ff86e0151f66`.

## Front geometry

```text
Front 72x16

x=0             15  18                                         71
 +---------------+  +---------------------------------------------+
 |               |  | headline / native marquee                  | y=0..6
 | GitHub mark   |  +---------------------------------------------+
 | 16x16         |  | repository or action / native marquee      | y=9..15
 +---------------+  +---------------------------------------------+
```

Columns x=16..17 are the 2px gap between the mark and text viewports. The table is the exact geometry contract.

| Region | Element ID | Payload | Contract |
| --- | --- | --- | --- |
| Canvas | `front-background` | Rectangle | `(0,0,72,16)`, GitHub canvas |
| Headline | `front-headline` | Normal text | `(18,0)`, width 54, reason first, native marquee |
| Context | `front-context` | Tiny text | `(18,9)`, width 54, repository or action, native marquee |
| Identity | `front-icon` | Image | `(0,0,16,16)`, bundled GitHub mark |

The icon, text origins, widths, payload kinds, and element order remain stable across the example states. The headline color may change with meaning.

## State copy

| State | Headline | Context | Headline color |
| --- | --- | --- | --- |
| Review requested | `Review requested: <subject>` | Full repository | Review / action |
| Mentioned | `Mentioned: <subject>` | Full repository | Mention / information |
| No unread items | `No unread GitHub notifications` | `Source is current` | Primary text |
| Setup required | `GitHub setup required` | `Run bsbctl app setup` | Review / action |
| Connection failed | `GitHub connection failed` | `Check token and network` | Failure |

Both text rows start visible, pause for 1000ms, move at 1000 pixels/minute when needed, and pause 2500ms before repeating. Motion stays inside each 54px viewport. A renderer may keep a fitting string still.

## Back geometry

The back uses an independent 160x80 canvas. It contains four small-text rows at x=4 and y=4,18,32,46. Each row has width 152 and may marquee. The rows provide product name, full reason or state, subject/repository detail, and a complete action such as `START: OPEN AND MARK READ`.

## Verification

- Validate every scene.
- Verify that all states keep the front IDs, kinds, order, coordinates, widths, and GitHub mark fixed.
- Verify complete state wording and the absence of private abbreviations.
- Verify headline and context clipping independently.
- Compare the native render and every marquee phase. Software validation does not establish hardware color, speed comfort, or reading distance.
