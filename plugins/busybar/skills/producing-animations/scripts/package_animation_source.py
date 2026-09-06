#!/usr/bin/env python3
"""Create a deterministic compiler-input ZIP from native animation frames."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path


FRAME_PATTERN = re.compile(r"frame_(0|[1-9][0-9]*)\.png$")
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def source_files(source: Path) -> list[Path]:
    meta_path = source / "meta.json"
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid {meta_path}: {exc}") from exc
    if meta != {"fps": 60, "color_mode": "rgb888", "sections": []}:
        raise ValueError('meta.json must equal {"fps": 60, "color_mode": "rgb888", "sections": []}')

    numbered: list[tuple[int, Path]] = []
    for path in source.iterdir():
        match = FRAME_PATTERN.fullmatch(path.name)
        if match and path.is_file():
            numbered.append((int(match.group(1)), path))
    numbered.sort()
    if not numbered:
        raise ValueError("source contains no frame_N.png files")
    for expected, (number, _) in enumerate(numbered):
        if number != expected:
            raise ValueError(f"missing frame_{expected}.png")
    return [meta_path, *(path for _, path in numbered)]


def package_source(source: Path, output: Path) -> None:
    if output.suffix != ".zip" or not output.stem:
        raise ValueError("output must be a named .zip file")
    files = source_files(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    try:
        with zipfile.ZipFile(
            temporary,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
            strict_timestamps=True,
        ) as archive:
            for path in files:
                info = zipfile.ZipInfo(f"{output.stem}/{path.name}", FIXED_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                info.create_system = 3
                archive.writestr(info, path.read_bytes(), compresslevel=9)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        package_source(args.source.resolve(), args.output.resolve())
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
