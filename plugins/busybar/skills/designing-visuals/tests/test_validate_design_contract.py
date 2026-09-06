from __future__ import annotations

import copy
import importlib.util
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_design_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_design_contract", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
EXAMPLE = Path(__file__).parents[1] / "assets" / "busybar-design-contract.json"


def write_png(path: Path, width: int, height: int) -> None:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))

    rows = b"".join(b"\x00" + b"\x00\x00\x00\xff" * width for _ in range(height))
    payload = b"\x89PNG\r\n\x1a\n"
    payload += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    payload += chunk(b"IDAT", zlib.compress(rows))
    payload += chunk(b"IEND", b"")
    path.write_bytes(payload)


class ValidateDesignContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def approve(self) -> None:
        selected = self.contract["candidates"][1]
        selected["design_spec"] = {"path": "candidates/focus-b.md", "sha256": "a" * 64}
        self.contract["selection_gate"] = {
            "status": "approved",
            "selected_candidate_id": selected["id"],
            "selected_revision": selected["revision"],
            "approval_record": {
                "actor": "user", "text": "Approve focus-b revision 1.",
                "approved_at": "2026-09-05T12:00:00Z",
                "artifacts": [{key: artifact[key] for key in ("surface", "path", "sha256")}
                              for artifact in selected["artifacts"]],
                "design_spec": copy.deepcopy(selected["design_spec"]),
            },
        }

    def test_approved_spec_is_required_and_bound_to_approval(self) -> None:
        self.approve()
        self.assertEqual(MODULE.validate_contract(self.contract, EXAMPLE, False), [])
        for mutation in ("missing", "changed"):
            with self.subTest(mutation=mutation):
                broken = copy.deepcopy(self.contract)
                if mutation == "missing":
                    del broken["candidates"][1]["design_spec"]
                else:
                    broken["candidates"][1]["design_spec"]["sha256"] = "b" * 64
                errors = MODULE.validate_contract(broken, EXAMPLE, False)
                self.assertTrue(any("design_spec" in error for error in errors), errors)

    def test_spec_binding_rejects_unsafe_paths_and_bad_digests(self) -> None:
        self.approve()
        for path, digest in (("../outside.md", "a" * 64), ("candidates/spec.md", "bad")):
            with self.subTest(path=path, digest=digest):
                self.contract["candidates"][1]["design_spec"] = {"path": path, "sha256": digest}
                errors = MODULE.validate_contract(self.contract, EXAMPLE, False)
                self.assertTrue(any("design_spec" in error for error in errors), errors)

    def test_spec_file_change_missing_file_and_symlink_escape_fail(self) -> None:
        self.approve()
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            (root / "candidates").mkdir()
            for candidate in self.contract["candidates"]:
                for artifact in candidate["artifacts"]:
                    target = root / artifact["path"]
                    write_png(target, 72, 16)
                    artifact["sha256"] = MODULE.hashlib.sha256(target.read_bytes()).hexdigest()
            selected = self.contract["candidates"][1]
            approval = self.contract["selection_gate"]["approval_record"]
            approval["artifacts"] = [{key: artifact[key] for key in ("surface", "path", "sha256")}
                                     for artifact in selected["artifacts"]]
            spec_path = root / selected["design_spec"]["path"]
            spec_path.write_text("# Exact approved specification\n", encoding="utf-8")
            selected["design_spec"]["sha256"] = MODULE.hashlib.sha256(spec_path.read_bytes()).hexdigest()
            approval["design_spec"] = copy.deepcopy(selected["design_spec"])
            contract_path = root / "contract.json"
            self.assertEqual(MODULE.validate_contract(self.contract, contract_path, True), [])
            spec_path.write_text("# Changed geometry\n", encoding="utf-8")
            errors = MODULE.validate_contract(self.contract, contract_path, True)
            self.assertTrue(any("design_spec" in error and "digest" in error for error in errors), errors)
            spec_path.unlink()
            errors = MODULE.validate_contract(self.contract, contract_path, True)
            self.assertTrue(any("design_spec" in error and "file not found" in error for error in errors), errors)
            outside_path = Path(outside) / "outside.md"
            outside_path.write_text("# Outside\n", encoding="utf-8")
            spec_path.symlink_to(outside_path)
            errors = MODULE.validate_contract(self.contract, contract_path, True)
            self.assertTrue(any("design_spec" in error and "escapes" in error for error in errors), errors)

    def test_pending_example_is_structurally_valid(self) -> None:
        self.assertEqual(MODULE.validate_contract(self.contract, EXAMPLE, False), [])

    def test_approved_gate_must_select_an_existing_candidate(self) -> None:
        self.contract["selection_gate"] = {
            "status": "approved",
            "selected_candidate_id": "missing",
            "selected_revision": 1,
            "approval_record": {
                "actor": "user",
                "text": "Approve missing v1",
                "approved_at": "2026-09-05T12:00:00Z",
                "artifacts": []
            }
        }
        errors = MODULE.validate_contract(self.contract, EXAMPLE, False)
        self.assertTrue(any("approved selection must match" in error for error in errors), errors)

    def test_approved_gate_binds_selected_candidate_artifacts(self) -> None:
        selected = self.contract["candidates"][1]
        artifact = selected["artifacts"][0]
        self.contract["selection_gate"] = {
            "status": "approved",
            "selected_candidate_id": selected["id"],
            "selected_revision": selected["revision"],
            "approval_record": {
                "actor": "user",
                "text": "Approve focus-b revision 1 for the front surface.",
                "approved_at": "2026-09-05T12:00:00Z",
                "artifacts": [
                    {
                        "surface": artifact["surface"],
                        "path": artifact["path"],
                        "sha256": artifact["sha256"],
                    }
                ],
            },
        }
        selected["design_spec"] = {"path": "candidates/focus-b.md", "sha256": "a" * 64}
        self.contract["selection_gate"]["approval_record"]["design_spec"] = copy.deepcopy(selected["design_spec"])
        self.assertEqual(MODULE.validate_contract(self.contract, EXAMPLE, False), [])

        self.contract["selection_gate"]["approval_record"]["artifacts"][0]["path"] = "another.png"
        errors = MODULE.validate_contract(self.contract, EXAMPLE, False)
        self.assertTrue(any("must match the selected candidate artifacts exactly" in error for error in errors), errors)

    def test_required_surface_must_exist_in_every_candidate(self) -> None:
        self.contract["targets"][1]["required"] = True
        errors = MODULE.validate_contract(self.contract, EXAMPLE, False)
        self.assertEqual(sum("missing required back artifact" in error for error in errors), 3)

    def test_artifact_dimensions_must_match_native_target(self) -> None:
        self.contract["candidates"][0]["artifacts"][0]["width"] = 1024
        errors = MODULE.validate_contract(self.contract, EXAMPLE, False)
        self.assertTrue(any("dimensions do not match target" in error for error in errors), errors)

    def test_artifact_path_must_be_canonical_and_contract_relative(self) -> None:
        self.contract["candidates"][0]["artifacts"][0]["path"] = "../outside.png"
        errors = MODULE.validate_contract(self.contract, EXAMPLE, False)
        self.assertTrue(any("canonical contract-relative path" in error for error in errors), errors)

    def test_file_check_verifies_dimensions_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_dir = root / "candidates"
            candidate_dir.mkdir()
            for candidate in self.contract["candidates"]:
                artifact = candidate["artifacts"][0]
                image = root / artifact["path"]
                write_png(image, 72, 16)
                artifact["sha256"] = MODULE.hashlib.sha256(image.read_bytes()).hexdigest()
            contract_path = root / "busybar-design-contract.json"
            contract_path.write_text(json.dumps(self.contract), encoding="utf-8")
            self.assertEqual(MODULE.validate_contract(self.contract, contract_path, True), [])

            broken = copy.deepcopy(self.contract)
            broken["candidates"][0]["artifacts"][0]["sha256"] = "0" * 64
            errors = MODULE.validate_contract(broken, contract_path, True)
            self.assertTrue(any("digest does not match" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
