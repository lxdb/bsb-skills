from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


QA = load_module("animation_qa", ROOT / "scripts" / "animation_qa.py")
PACKAGER = load_module("package_animation_source", ROOT / "scripts" / "package_animation_source.py")
COMPILER = load_module("compile_animation", ROOT / "scripts" / "compile_animation.py")


class AnimationToolsTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "rendered"
        self.source.mkdir()
        (self.source / "meta.json").write_text(
            json.dumps({"fps": 60, "color_mode": "rgb888", "sections": []}),
            encoding="utf-8",
        )
        self.frames: list[Image.Image] = []
        cue = [False, True, False, True, False, False]
        for index, enabled in enumerate(cue):
            frame = Image.new("RGBA", (72, 16), (0, 0, 0, 255))
            for x in range(10, 20):
                for y in range(3, 13):
                    frame.putpixel((x, y), (255, 255, 255, 255))
            if enabled:
                frame.putpixel((1, 1), (0, 255, 0, 255))
            frame.save(self.source / f"frame_{index}.png")
            self.frames.append(frame)
        self.framebuffer = self.root / "framebuffer.gif"
        self.frames[0].save(
            self.framebuffer,
            save_all=True,
            append_images=self.frames[1:],
            duration=[20, 20, 20, 20, 10, 10],
            loop=0,
            disposal=1,
            optimize=False,
        )
        self.config = self.root / "animation-qa.json"
        self.config.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "width": 72,
                    "height": 16,
                    "fps": 60,
                    "expected_frame_count": 6,
                    "allow_transparency": False,
                    "stable_regions": [
                        {
                            "name": "status",
                            "x": 10,
                            "y": 3,
                            "width": 10,
                            "height": 10,
                            "max_changed_pixels": 0,
                        }
                    ],
                    "motion_regions": [
                        {
                            "name": "cue",
                            "x": 0,
                            "y": 0,
                            "width": 3,
                            "height": 3,
                            "min_changed_transitions": 2,
                        }
                    ],
                    "max_changed_pixels_outside_motion_regions": 0,
                    "max_changed_pixel_fraction_per_transition": 0.01,
                    "max_mean_luminance_delta_per_transition": 0.01,
                    "max_loop_seam_changed_pixel_fraction": 0.01,
                    "framebuffer_duration_tolerance_milliseconds": 1,
                }
            ),
            encoding="utf-8",
        )

    def test_native_frames_and_bounded_motion_pass_qa(self) -> None:
        report = QA.run(self.source, self.framebuffer, self.config)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["frame_count"], 6)
        self.assertEqual(report["motion"]["stable_region_max_changed_pixels"], {"status": 0})
        self.assertGreaterEqual(report["motion"]["motion_region_changed_transitions"]["cue"], 2)
        self.assertFalse(report["hardware_verified"])

    def test_change_outside_motion_region_fails(self) -> None:
        path = self.source / "frame_2.png"
        with Image.open(path) as opened:
            frame = opened.convert("RGBA")
        frame.putpixel((30, 10), (255, 0, 0, 255))
        frame.save(path)
        with self.assertRaisesRegex(ValueError, "outside approved motion regions"):
            QA.run(self.source, self.framebuffer, self.config)

    def test_wrong_native_dimensions_fail(self) -> None:
        Image.new("RGBA", (1440, 320), (0, 0, 0, 255)).save(self.source / "frame_2.png")
        with self.assertRaisesRegex(ValueError, "expected 72x16"):
            QA.run(self.source, self.framebuffer, self.config)

    def test_package_is_deterministic_and_compiler_shaped(self) -> None:
        first = self.root / "focus_72x16.zip"
        second_dir = self.root / "again"
        second_dir.mkdir()
        second = second_dir / "focus_72x16.zip"
        PACKAGER.package_source(self.source, first)
        PACKAGER.package_source(self.source, second)
        self.assertEqual(hashlib.sha256(first.read_bytes()).digest(), hashlib.sha256(second.read_bytes()).digest())
        with zipfile.ZipFile(first) as archive:
            self.assertEqual(
                archive.namelist(),
                ["focus_72x16/meta.json", *[f"focus_72x16/frame_{index}.png" for index in range(6)]],
            )
        report = QA.run(first, self.framebuffer, self.config)
        self.assertEqual(report["frame_count"], 6)

    def test_bundled_compiler_is_deterministic_and_preserves_holds(self) -> None:
        source_zip = self.root / "focus_72x16.zip"
        PACKAGER.package_source(self.source, source_zip)
        first = self.root / "first.anim"
        second = self.root / "second.anim"
        first_digest = COMPILER.compile_source(source_zip, first)
        second_digest = COMPILER.compile_source(source_zip, second)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(first_digest, second_digest)

        fields = struct.unpack_from("<8sBBBBBHBIIIII", first.read_bytes())
        self.assertEqual(fields[0], b"bicycle0")
        self.assertEqual(fields[2:6], (72, 16, 0, 60))
        self.assertEqual(fields[10:], (1, 5, 6))
        sections_size = fields[8]
        section = first.read_bytes()[36 : 36 + sections_size]
        self.assertTrue(section.endswith(b"default\0"))

    def test_bundled_compiler_rejects_transparency(self) -> None:
        path = self.source / "frame_0.png"
        with Image.open(path) as opened:
            frame = opened.convert("RGBA")
        frame.putpixel((0, 0), (0, 0, 0, 0))
        frame.save(path)
        source_zip = self.root / "focus_72x16.zip"
        PACKAGER.package_source(self.source, source_zip)
        with self.assertRaisesRegex(ValueError, "not opaque"):
            COMPILER.compile_source(source_zip, self.root / "animation.anim")

    def test_package_rejects_nonrelease_metadata(self) -> None:
        (self.source / "meta.json").write_text(
            json.dumps({"fps": 30, "color_mode": "rgb888", "sections": []}),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "meta.json must equal"):
            PACKAGER.package_source(self.source, self.root / "focus_72x16.zip")


if __name__ == "__main__":
    unittest.main()
