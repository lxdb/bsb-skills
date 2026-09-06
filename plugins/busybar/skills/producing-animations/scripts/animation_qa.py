#!/usr/bin/env python3
"""Validate native BUSY Bar source frames and framebuffer motion boundaries."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageSequence
except ImportError:
    print("ERROR: Pillow is required in the selected Python environment", file=sys.stderr)
    raise SystemExit(2)


FRAME_PATTERN = re.compile(r"frame_(0|[1-9][0-9]*)\.png$")


@dataclass(frozen=True)
class Region:
    name: str
    x: int
    y: int
    width: int
    height: int
    limit: int

    def indexes(self, canvas_width: int) -> set[int]:
        return {
            row * canvas_width + column
            for row in range(self.y, self.y + self.height)
            for column in range(self.x, self.x + self.width)
        }


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid JSON from {path}: {exc}") from exc


def parse_fraction(config: dict[str, Any], key: str) -> float:
    value = config.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise ValueError(f"{key} must be a number from 0 through 1")
    return float(value)


def parse_nonnegative_int(config: dict[str, Any], key: str) -> int:
    value = config.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{key} must be a non-negative integer")
    return value


def parse_regions(
    raw: Any,
    *,
    width: int,
    height: int,
    limit_key: str,
) -> list[Region]:
    if not isinstance(raw, list):
        raise ValueError(f"{limit_key} regions must be an array")
    result: list[Region] = []
    names: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"region {index} must be an object")
        expected = {"name", "x", "y", "width", "height", limit_key}
        if set(item) != expected:
            raise ValueError(f"region {index} must contain exactly {sorted(expected)}")
        name = item["name"]
        values = [item[key] for key in ("x", "y", "width", "height", limit_key)]
        if not isinstance(name, str) or not name or name in names:
            raise ValueError(f"region {index} has an invalid or duplicate name")
        if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
            raise ValueError(f"region {name!r} coordinates and limits must be integers")
        x, y, region_width, region_height, limit = values
        if x < 0 or y < 0 or region_width <= 0 or region_height <= 0 or limit < 0:
            raise ValueError(f"region {name!r} coordinates, dimensions, or limit are invalid")
        if x + region_width > width or y + region_height > height:
            raise ValueError(f"region {name!r} lies outside the {width}x{height} canvas")
        names.add(name)
        result.append(Region(name, x, y, region_width, region_height, limit))
    return result


def validate_config(data: Any) -> tuple[dict[str, Any], list[Region], list[Region]]:
    if not isinstance(data, dict):
        raise ValueError("QA configuration must be an object")
    required = {
        "schema_version",
        "width",
        "height",
        "fps",
        "expected_frame_count",
        "allow_transparency",
        "stable_regions",
        "motion_regions",
        "max_changed_pixels_outside_motion_regions",
        "max_changed_pixel_fraction_per_transition",
        "max_mean_luminance_delta_per_transition",
        "max_loop_seam_changed_pixel_fraction",
        "framebuffer_duration_tolerance_milliseconds",
    }
    if set(data) != required:
        missing = sorted(required - set(data))
        extra = sorted(set(data) - required)
        raise ValueError(f"QA configuration keys differ; missing={missing}, extra={extra}")
    if data["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    if (data["width"], data["height"], data["fps"]) != (72, 16, 60):
        raise ValueError("current standalone catalog requires width=72, height=16, fps=60")
    if isinstance(data["expected_frame_count"], bool) or not isinstance(data["expected_frame_count"], int) or data["expected_frame_count"] <= 0:
        raise ValueError("expected_frame_count must be a positive integer")
    if not isinstance(data["allow_transparency"], bool):
        raise ValueError("allow_transparency must be a boolean")
    parse_nonnegative_int(data, "max_changed_pixels_outside_motion_regions")
    parse_nonnegative_int(data, "framebuffer_duration_tolerance_milliseconds")
    parse_fraction(data, "max_changed_pixel_fraction_per_transition")
    parse_fraction(data, "max_mean_luminance_delta_per_transition")
    parse_fraction(data, "max_loop_seam_changed_pixel_fraction")
    stable = parse_regions(
        data["stable_regions"],
        width=72,
        height=16,
        limit_key="max_changed_pixels",
    )
    motion = parse_regions(
        data["motion_regions"],
        width=72,
        height=16,
        limit_key="min_changed_transitions",
    )
    return data, stable, motion


def source_entries(source: Path) -> tuple[bytes, list[tuple[str, bytes]]]:
    if source.is_dir():
        try:
            meta = (source / "meta.json").read_bytes()
            frames = [
                (path.name, path.read_bytes())
                for path in source.iterdir()
                if path.is_file() and FRAME_PATTERN.fullmatch(path.name)
            ]
        except OSError as exc:
            raise ValueError(f"cannot read source directory {source}: {exc}") from exc
        return meta, frames
    if source.suffix != ".zip" or not source.is_file():
        raise ValueError("source must be a directory or .zip file")
    try:
        with zipfile.ZipFile(source) as archive:
            prefix = source.stem + "/"
            allowed_pattern = re.compile(re.escape(prefix) + r"frame_(0|[1-9][0-9]*)\.png$")
            file_names = [item.filename for item in archive.infolist() if not item.is_dir()]
            allowed = {prefix + "meta.json"}
            allowed.update(name for name in file_names if allowed_pattern.fullmatch(name))
            unexpected = sorted(set(file_names) - allowed)
            if unexpected:
                raise ValueError(f"source ZIP contains unexpected files: {unexpected}")
            meta = archive.read(prefix + "meta.json")
            frames = [
                (Path(name).name, archive.read(name))
                for name in file_names
                if allowed_pattern.fullmatch(name)
            ]
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        raise ValueError(f"cannot read source ZIP {source}: {exc}") from exc
    return meta, frames


def load_frames(source: Path, config: dict[str, Any]) -> tuple[list[tuple[tuple[int, int, int], ...]], list[str]]:
    meta_bytes, entries = source_entries(source)
    try:
        meta = json.loads(meta_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"source meta.json is invalid: {exc}") from exc
    expected_meta = {"fps": 60, "color_mode": "rgb888", "sections": []}
    if meta != expected_meta:
        raise ValueError(f"source meta.json must equal {expected_meta}")

    numbered: list[tuple[int, str, bytes]] = []
    for name, payload in entries:
        match = FRAME_PATTERN.fullmatch(name)
        assert match is not None
        numbered.append((int(match.group(1)), name, payload))
    numbered.sort()
    if len(numbered) != config["expected_frame_count"]:
        raise ValueError(f"source has {len(numbered)} frames; expected {config['expected_frame_count']}")

    frames: list[tuple[tuple[int, int, int], ...]] = []
    hashes: list[str] = []
    for expected, (number, name, payload) in enumerate(numbered):
        if number != expected:
            raise ValueError(f"missing frame_{expected}.png")
        try:
            with Image.open(io.BytesIO(payload)) as opened:
                opened.load()
                if opened.size != (72, 16):
                    raise ValueError(f"{name} is {opened.width}x{opened.height}; expected 72x16")
                rgba = opened.convert("RGBA")
                if not config["allow_transparency"] and rgba.getchannel("A").getextrema() != (255, 255):
                    raise ValueError(f"{name} contains transparency")
                rgb = tuple(rgba.convert("RGB").get_flattened_data())
        except OSError as exc:
            raise ValueError(f"cannot decode {name}: {exc}") from exc
        frames.append(rgb)
        hashes.append(sha256(payload))
    return frames, hashes


def changed_indexes(first: tuple[Any, ...], second: tuple[Any, ...]) -> set[int]:
    return {index for index, (left, right) in enumerate(zip(first, second)) if left != right}


def luminance(pixel: tuple[int, int, int]) -> float:
    red, green, blue = pixel
    return (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255


def analyze_frames(
    frames: list[tuple[tuple[int, int, int], ...]],
    config: dict[str, Any],
    stable: list[Region],
    motion: list[Region],
) -> dict[str, Any]:
    pixel_count = 72 * 16
    allowed_motion = set().union(*(region.indexes(72) for region in motion)) if motion else set()
    transitions = [changed_indexes(frames[index - 1], frames[index]) for index in range(1, len(frames))]
    luminance_deltas = [
        sum(abs(luminance(frames[index][pixel]) - luminance(frames[index - 1][pixel])) for pixel in range(pixel_count)) / pixel_count
        for index in range(1, len(frames))
    ]
    max_fraction = max((len(changed) / pixel_count for changed in transitions), default=0.0)
    max_luminance_delta = max(luminance_deltas, default=0.0)
    outside_counts = [len(changed - allowed_motion) for changed in transitions]
    max_outside = max(outside_counts, default=0)
    if max_fraction > config["max_changed_pixel_fraction_per_transition"]:
        raise ValueError(f"changed-pixel fraction {max_fraction:.6f} exceeds configured maximum")
    if max_luminance_delta > config["max_mean_luminance_delta_per_transition"]:
        raise ValueError(f"mean luminance delta {max_luminance_delta:.6f} exceeds configured maximum")
    if max_outside > config["max_changed_pixels_outside_motion_regions"]:
        raise ValueError(f"{max_outside} pixels changed outside approved motion regions")

    stable_results: dict[str, int] = {}
    for region in stable:
        indexes = region.indexes(72)
        maximum = max(
            (sum(frames[0][pixel] != frame[pixel] for pixel in indexes) for frame in frames[1:]),
            default=0,
        )
        if maximum > region.limit:
            raise ValueError(f"stable region {region.name!r} changed by {maximum} pixels")
        stable_results[region.name] = maximum

    motion_results: dict[str, int] = {}
    for region in motion:
        indexes = region.indexes(72)
        changed_transitions = sum(bool(changed & indexes) for changed in transitions)
        if changed_transitions < region.limit:
            raise ValueError(
                f"motion region {region.name!r} changed in {changed_transitions} transitions; expected at least {region.limit}"
            )
        motion_results[region.name] = changed_transitions

    seam = changed_indexes(frames[-1], frames[0])
    seam_fraction = len(seam) / pixel_count
    if seam_fraction > config["max_loop_seam_changed_pixel_fraction"]:
        raise ValueError(f"loop seam changed-pixel fraction {seam_fraction:.6f} exceeds configured maximum")
    return {
        "max_changed_pixel_fraction_per_transition": max_fraction,
        "max_mean_luminance_delta_per_transition": max_luminance_delta,
        "max_changed_pixels_outside_motion_regions": max_outside,
        "loop_seam_changed_pixel_fraction": seam_fraction,
        "stable_region_max_changed_pixels": stable_results,
        "motion_region_changed_transitions": motion_results,
    }


def validate_framebuffer(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = path.read_bytes()
        with Image.open(io.BytesIO(payload)) as animation:
            if animation.size != (72, 16):
                raise ValueError(f"framebuffer is {animation.width}x{animation.height}; expected 72x16")
            if animation.info.get("loop") != 0:
                raise ValueError("framebuffer GIF must loop forever")
            durations: list[int] = []
            for frame in ImageSequence.Iterator(animation):
                duration = frame.info.get("duration", animation.info.get("duration", 0))
                if isinstance(duration, bool) or not isinstance(duration, int) or duration <= 0:
                    raise ValueError("framebuffer GIF contains a non-positive delay")
                durations.append(duration)
    except OSError as exc:
        raise ValueError(f"cannot decode framebuffer GIF {path}: {exc}") from exc
    expected_duration = config["expected_frame_count"] * 1000 / config["fps"]
    actual_duration = sum(durations)
    delta = abs(actual_duration - expected_duration)
    if delta > config["framebuffer_duration_tolerance_milliseconds"]:
        raise ValueError(
            f"framebuffer duration is {actual_duration} ms; expected {expected_duration:.3f} ms within configured tolerance"
        )
    return {
        "sha256": sha256(payload),
        "frame_count": len(durations),
        "duration_milliseconds": actual_duration,
        "duration_delta_milliseconds": delta,
        "distinct_delays_milliseconds": sorted(set(durations)),
    }


def run(source: Path, framebuffer: Path, config_path: Path) -> dict[str, Any]:
    config, stable, motion = validate_config(read_json(config_path))
    frames, frame_hashes = load_frames(source, config)
    motion_report = analyze_frames(frames, config, stable, motion)
    framebuffer_report = validate_framebuffer(framebuffer, config)
    return {
        "schema_version": 1,
        "status": "pass",
        "source": str(source),
        "frame_count": len(frames),
        "frame_sha256": frame_hashes,
        "unique_frame_count": len(set(frame_hashes)),
        "motion": motion_report,
        "framebuffer": framebuffer_report,
        "hardware_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--framebuffer", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        report = run(args.source.resolve(), args.framebuffer.resolve(), args.config.resolve())
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    serialized = json.dumps(report, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized, encoding="utf-8")
        print(f"OK: {args.report}")
    else:
        print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
