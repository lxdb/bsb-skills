#!/usr/bin/env python3
"""Compile a deterministic 72x16 RGB888 source ZIP into a BUSY .anim file."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is required in the selected Python environment", file=sys.stderr)
    raise SystemExit(2)


WIDTH = 72
HEIGHT = 16
FPS = 60
SIGNATURE = b"bicycle0"
SECTION_NAME = b"default"
HEADER = struct.Struct("<8sBBBBBHBIIIII")
SECTION = struct.Struct("<IIIB")
FRAME = struct.Struct("<BBH")
FRAME_PATTERN = re.compile(r"frame_(0|[1-9][0-9]*)\.png$")


def read_source(path: Path) -> tuple[int, list[bytes]]:
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise ValueError(f"cannot open source ZIP: {exc}") from exc
    with archive:
        root = path.stem
        meta_name = f"{root}/meta.json"
        names = archive.namelist()
        if names.count(meta_name) != 1:
            raise ValueError(f"source ZIP must contain one {meta_name}")
        try:
            metadata = json.loads(archive.read(meta_name))
        except (KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("source ZIP contains invalid meta.json") from exc
        expected_metadata = {"fps": FPS, "color_mode": "rgb888", "sections": []}
        if metadata != expected_metadata:
            raise ValueError(f"meta.json must equal {json.dumps(expected_metadata, separators=(',', ':'))}")

        numbered: list[tuple[int, str]] = []
        for name in names:
            if not name.startswith(root + "/"):
                raise ValueError(f"source ZIP entry lies outside {root}/: {name}")
            relative = name[len(root) + 1 :]
            if relative == "meta.json":
                continue
            match = FRAME_PATTERN.fullmatch(relative)
            if match is None:
                raise ValueError(f"unexpected source ZIP entry: {name}")
            numbered.append((int(match.group(1)), name))
        numbered.sort()
        if not numbered:
            raise ValueError("source ZIP contains no frame_N.png files")

        pixels: list[bytes] = []
        for expected, (number, name) in enumerate(numbered):
            if number != expected:
                raise ValueError(f"missing frame_{expected}.png")
            try:
                with Image.open(io.BytesIO(archive.read(name))) as opened:
                    rgba = opened.convert("RGBA")
            except (KeyError, OSError) as exc:
                raise ValueError(f"cannot decode frame_{number}.png: {exc}") from exc
            if rgba.size != (WIDTH, HEIGHT):
                raise ValueError(f"frame_{number}.png is {rgba.width}x{rgba.height}, want {WIDTH}x{HEIGHT}")
            if rgba.getchannel("A").getextrema() != (255, 255):
                raise ValueError(f"frame_{number}.png is not opaque; flatten it before compilation")
            pixels.append(rgba.convert("RGB").tobytes())
        return int(metadata["fps"]), pixels


def combine_holds(frames: list[bytes]) -> list[tuple[bytes, int]]:
    combined: list[tuple[bytes, int]] = []
    for pixels in frames:
        if combined and combined[-1][0] == pixels and combined[-1][1] < 255:
            previous, duration = combined[-1]
            combined[-1] = (previous, duration + 1)
        else:
            combined.append((pixels, 1))
    return combined


def encode(fps: int, display_frames: list[bytes]) -> bytes:
    frames = combine_holds(display_frames)
    frame_size = WIDTH * HEIGHT * 3
    display_frame_count = sum(duration for _, duration in frames)
    sections_size = SECTION.size + len(SECTION_NAME) + 1
    frames_size = sum(FRAME.size + len(pixels) for pixels, _ in frames)
    first_frame_offset = HEADER.size + sections_size

    output = bytearray(
        HEADER.pack(
            SIGNATURE,
            0,
            WIDTH,
            HEIGHT,
            0,
            fps,
            frame_size,
            0,
            sections_size,
            frames_size,
            1,
            len(frames),
            display_frame_count,
        )
    )
    output.extend(SECTION.pack(0, display_frame_count - 1, first_frame_offset, frames[0][1]))
    output.extend(SECTION_NAME + b"\0")
    for pixels, duration in frames:
        output.extend(FRAME.pack(0, duration, len(pixels)))
        output.extend(pixels)
    return bytes(output)


def compile_source(source: Path, output: Path) -> str:
    fps, frames = read_source(source)
    data = encode(fps, frames)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    try:
        temporary.write_bytes(data)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="deterministic source ZIP")
    parser.add_argument("--output", required=True, type=Path, help="destination .anim file")
    args = parser.parse_args()
    try:
        digest = compile_source(args.input.resolve(), args.output.resolve())
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {args.output} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
