# Scene protocol

## Elements and limits

`protocol.Scene` contains `[]protocol.Element`. Each element has a unique semantic `ID`, a `Display`, integer `X`/`Y`, and exactly one payload. Use the package `github.com/lxdb/bsbctl/sdk/protocol` from the target bsbctl checkout.

| Payload | Fields to supply | Use |
| --- | --- | --- |
| `TextElement` | `Value`, `Font`; optional `Color`, `Align`, `Width`, `Marquee` | Static or changing text |
| `RectangleElement` | Positive `Width`, positive `Height`, `Color` | Background, track, fill, solid geometry |
| `ImageElement` | `Asset` | Packaged or firmware stock image |
| `AnimationElement` | `Asset`, `Loop` | Packaged or firmware stock animation |
| `CountdownElement` | `EndsAtUnixSeconds`, `ShowHours`, `Color`; optional `Align` | Native time remaining |

The front is `DisplayFront`, 72x16. The back is `DisplayBack`, 160x80. A scene contains 1-64 elements. Its element origins must lie within their display. Rectangle dimensions must be positive signed 32-bit values. `Scene.Validate()` checks field validity and origin bounds; it does not measure text or ensure the complete painted rectangle or asset stays inside a display.

Colors use `#RRGGBBAA`. Use `FF` for opaque content. Do not depend on undocumented blending behavior to hide an element; an opaque rectangle in the underlying track color is sufficient for a zero fill.

Text fonts are `tiny`, `small`, `normal`, `condensed`, `bold`, `large`, `extra_large`, and `global`. Set a font explicitly; empty font names do not pass scene validation. Text must be valid UTF-8 and no more than 512 bytes (`MaxTextBytes`). Valid UTF-8 does not prove glyph coverage.

`superscript` exists in firmware but is not accepted as a scene text font. The native countdown uses it internally and does not expose a font, width, arbitrary format, or progress fraction. `EndsAtUnixSeconds` is a positive Unix-second timestamp. `ShowHours` is `when_non_zero` or `always`. Supply the future deadline from the model; define the application state that follows expiry.

## Anchors, width, and order

Alignment places the element's box relative to an anchor measured from the display's top-left. It does not change the meaning of X/Y into offsets from the display's opposite edge.

| Align | X/Y locates |
| --- | --- |
| omitted or `top_left` | Top-left of the element box |
| `top_mid` | Top-center |
| `top_right` | Top-right |
| `mid_left` | Middle-left |
| `center` | Center |
| `mid_right` | Middle-right |
| `bottom_left` | Bottom-left |
| `bottom_mid` | Bottom-center |
| `bottom_right` | Bottom-right |

For a value ending at the same horizontal position, use a fixed right anchor and `top_right`. Account for the box width and font bearings before comparing painted bounds. `TextElement.Width` sets the text object's width; zero uses content width. With a positive width, align the whole object, not an assumed centered string within it.

Without marquee, long content uses clipping. Use clipping only when the specification allows it. Put the background before foreground elements, then tracks, fills, assets, and text in their intended layer order. Preserve the order and IDs when updating one view. Check any overlap in the final render.

## Native time and motion

`Marquee` supplies `PixelsPerMinute`, `StartDelayMilliseconds`, and `RepeatDelayMilliseconds`. Convert pixels/second by multiplying by 60. For example, 18px/s becomes 1080px/min. A non-nil marquee requires a positive speed.

Set a bounded `Width` for every scrolling element. A complete long notification may marquee when a product mark, reason, action, or other familiar point of entry remains stable or begins the visible text. Do not replace the message with a private abbreviation merely to keep it static. Firmware scrolling is circular; the protocol has no one-pass count, easing curve, or pause/resume control. A design that requires those behaviors needs an explicit implementation decision before approval. Do not simulate them by changing text offsets every refresh.

`AnimationElement.Loop=false` selects a one-shot asset. It does not schedule a later scene or decide when a task has completed. Reducers and host lifecycle rules own state, expiry, and replacement. The scene builder only maps that state to elements.

## Assets

`AssetRef` requires exactly one of `PackagePath` or `StockName`.

- A package path is a canonical relative path declared by the plugin package. Match the package declaration and file; do not embed host filesystem paths.
- Stock images use a basename ending in `.image`; stock animations use `.anim`.
- Declare source dimensions and intended placement in the design specification. Images and animations have no scene-level scale, crop, mask, or viewport fields.
- Precompose custom masked effects into a suitably sized asset. Do not assume firmware's internal BUSY composition primitives are exposed through this protocol.

Prefer text, rectangles, and countdowns for live content. Use an image for custom static art. Use an animation for an approved local motion element. Do not replace a live scene with a full-screen video to avoid data binding.

## Verify the supported boundary

Before editing, compare this contract with `sdk/protocol/presentation.go` and the target plugin. Check the existing compiler in `internal/presentation/compiler.go` when representation differs from validation. Those are compatibility checks, not prerequisites for discovering how to build a scene.

The scene construction reference explains region conversion, tests, and preview limits.
