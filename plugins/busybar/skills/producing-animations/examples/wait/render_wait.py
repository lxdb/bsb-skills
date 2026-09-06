#!/usr/bin/env python3
"""Render a deterministic WAIT label with motion confined to a 16x16 icon."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw


# Original 3x5 bitmap lettering, drawn at integer 2x scale.
LETTERS = {
    "W": ("101", "101", "111", "111", "101"),
    "A": ("010", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"),
    "T": ("111", "010", "010", "010", "010"),
}
DOTS = ((4, 4), (8, 3), (12, 4), (13, 8), (12, 12), (8, 13), (4, 12), (3, 8))
BACKGROUND = (7, 21, 34)
TEXT = (234, 244, 242)
QUIET = (23, 26, 33)
ACCENT = (42, 199, 181)


def static_frame() -> Image.Image:
    frame = Image.new("RGB", (72, 16), BACKGROUND)
    draw = ImageDraw.Draw(frame)
    for letter_index, letter in enumerate("WAIT"):
        for row, bits in enumerate(LETTERS[letter]):
            for column, bit in enumerate(bits):
                if bit == "1":
                    x, y = 22 + letter_index * 8 + column * 2, 3 + row * 2
                    draw.rectangle((x, y, x + 1, y + 1), fill=TEXT)
    for x, y in DOTS:
        draw.rectangle((x, y, x + 1, y + 1), fill=QUIET)
    return frame


def poses() -> list[Image.Image]:
    base = static_frame()
    result = []
    for x, y in DOTS:
        frame = base.copy()
        ImageDraw.Draw(frame).rectangle((x, y, x + 1, y + 1), fill=ACCENT)
        result.append(frame)
    return result


def render(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    frames = output / "frames"
    frames.mkdir()
    (frames / "meta.json").write_text(
        json.dumps({"fps": 60, "color_mode": "rgb888", "sections": []}, indent=2) + "\n",
        encoding="utf-8",
    )
    sequence = poses()
    for index in range(120):
        sequence[index // 15].save(frames / f"frame_{index}.png")
    sequence[0].save(
        output / "framebuffer.gif", save_all=True, append_images=sequence[1:],
        duration=[250] * len(sequence), loop=0, disposal=1, optimize=False,
    )
    static_frame().save(output / "static.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new authoring output directory")
    args = parser.parse_args()
    render(args.out)
    print(f"Rendered 120 display frames, 8 poses, 2000 ms: {args.out}")


if __name__ == "__main__":
    main()
