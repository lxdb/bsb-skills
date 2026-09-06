from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageSequence


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "examples" / "wait" / "render_wait.py"
SPEC = importlib.util.spec_from_file_location("render_wait", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PACKAGER = load_module("wait_package_animation_source", ROOT / "scripts" / "package_animation_source.py")
COMPILER = load_module("wait_compile_animation", ROOT / "scripts" / "compile_animation.py")


class WaitExampleTest(unittest.TestCase):
    def test_every_pose_preserves_the_word_and_has_only_local_motion(self) -> None:
        base = MODULE.static_frame()
        expected_word = base.crop((18, 0, 72, 16)).tobytes()
        self.assertEqual(base.getpixel((22, 3)), (234, 244, 242))
        for pose in MODULE.poses():
            self.assertEqual(pose.size, (72, 16))
            self.assertEqual(pose.crop((18, 0, 72, 16)).tobytes(), expected_word)
            changed = [(x, y) for y in range(16) for x in range(72)
                       if pose.getpixel((x, y)) != base.getpixel((x, y))]
            self.assertEqual(len(changed), 4)
            self.assertTrue(all(x < 16 for x, _ in changed))

    def test_render_preserves_holds_and_matches_decoded_gif_poses(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "render"
            MODULE.render(output)
            frames = output / "frames"
            self.assertEqual(len(list(frames.glob("frame_*.png"))), 120)
            with Image.open(output / "framebuffer.gif") as gif:
                self.assertEqual(gif.info["loop"], 0)
                decoded = [frame.convert("RGB").copy() for frame in ImageSequence.Iterator(gif)]
                gif.seek(0)
                durations = [frame.info["duration"] for frame in ImageSequence.Iterator(gif)]
            self.assertEqual(durations, [250] * 8)
            for pose_index, frame in enumerate(decoded):
                for offset in range(15):
                    with Image.open(frames / f"frame_{pose_index * 15 + offset}.png") as source:
                        self.assertEqual(frame.tobytes(), source.convert("RGB").tobytes())

    def test_rebuild_is_identical_and_existing_output_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "first", Path(directory) / "second"
            MODULE.render(first)
            MODULE.render(second)
            paths = [path.relative_to(first) for path in first.rglob("*") if path.is_file()]
            for path in paths:
                self.assertEqual((first / path).read_bytes(), (second / path).read_bytes(), str(path))
            with self.assertRaises(FileExistsError):
                MODULE.render(first)

    def test_compiled_wait_matches_the_independent_reference_encoder(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "render"
            MODULE.render(output)
            source_zip = output / "wait_72x16.zip"
            PACKAGER.package_source(output / "frames", source_zip)
            digest = COMPILER.compile_source(source_zip, output / "animation.anim")
            self.assertEqual(digest, "3fbe0a5e20ad434f4f7176440e7fdb9ea12aa87048e0aeb69d6ce5e41aae5598")


if __name__ == "__main__":
    unittest.main()
