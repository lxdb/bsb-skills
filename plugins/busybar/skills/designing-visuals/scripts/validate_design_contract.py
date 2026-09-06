#!/usr/bin/env python3
"""Validate a BUSY Bar design contract with no third-party dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path, PurePosixPath
from typing import Any


SURFACES = {"front": (72, 16), "back": (160, 80)}
HEX_DIGITS = frozenset("0123456789abcdef")


def fail(errors: list[str], path: str, message: str) -> None:
    errors.append(f"{path}: {message}")


def require(mapping: dict[str, Any], key: str, kind: type, path: str, errors: list[str]) -> Any:
    value = mapping.get(key)
    if not isinstance(value, kind):
        fail(errors, f"{path}.{key}", f"expected {kind.__name__}")
        return None
    return value


def image_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 24:
        return struct.unpack(">II", header[16:24])
    if header[:6] in (b"GIF87a", b"GIF89a") and len(header) >= 10:
        return struct.unpack("<HH", header[6:10])
    raise ValueError("only PNG and GIF dimensions are supported")


def safe_relative_path(value: str) -> bool:
    candidate = PurePosixPath(value)
    return (
        bool(value)
        and "\\" not in value
        and not candidate.is_absolute()
        and ".." not in candidate.parts
        and candidate.as_posix() == value
    )


def validate_spec_binding(
    binding: Any, path: str, contract_path: Path, check_files: bool, errors: list[str]
) -> tuple[str, str] | None:
    if not isinstance(binding, dict):
        fail(errors, path, "expected design specification path and sha256")
        return None
    relative_path = require(binding, "path", str, path, errors)
    digest = require(binding, "sha256", str, path, errors)
    if relative_path is None or digest is None:
        return None
    if not safe_relative_path(relative_path) or PurePosixPath(relative_path).suffix != ".md":
        fail(errors, f"{path}.path", "expected canonical contract-relative Markdown path")
        return None
    if len(digest) != 64 or set(digest.lower()) - HEX_DIGITS:
        fail(errors, f"{path}.sha256", "expected 64 hexadecimal characters")
        return None
    if check_files:
        file_path = (contract_path.parent / relative_path).resolve()
        try:
            file_path.relative_to(contract_path.parent.resolve())
        except ValueError:
            fail(errors, f"{path}.path", "resolved path escapes the contract directory")
            return None
        try:
            content = file_path.read_bytes()
        except FileNotFoundError:
            fail(errors, f"{path}.path", f"file not found: {file_path}")
        except OSError as exc:
            fail(errors, f"{path}.path", f"cannot read file: {exc}")
        else:
            if hashlib.sha256(content).hexdigest() != digest.lower():
                fail(errors, f"{path}.sha256", "digest does not match file")
    return relative_path, digest.lower()


def validate_contract(data: Any, contract_path: Path, check_files: bool) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["$: expected object"]

    if data.get("schema_version") != 1:
        fail(errors, "$.schema_version", "expected 1")
    require(data, "artifact_id", str, "$", errors)
    intent = require(data, "intent", dict, "$", errors)
    if intent is not None:
        for key in ("message", "meaning", "priority", "freshness"):
            require(intent, key, str, "$.intent", errors)

    targets = require(data, "targets", list, "$", errors)
    target_map: dict[str, tuple[int, int]] = {}
    if targets is not None:
        for index, target in enumerate(targets):
            path = f"$.targets[{index}]"
            if not isinstance(target, dict):
                fail(errors, path, "expected object")
                continue
            surface = require(target, "surface", str, path, errors)
            width = require(target, "width", int, path, errors)
            height = require(target, "height", int, path, errors)
            require(target, "role", str, path, errors)
            if not isinstance(target.get("required"), bool):
                fail(errors, f"{path}.required", "expected bool")
            if surface in target_map:
                fail(errors, f"{path}.surface", "duplicate surface")
            elif surface in SURFACES and width is not None and height is not None:
                target_map[surface] = (width, height)
                if (width, height) != SURFACES[surface]:
                    fail(errors, path, f"{surface} must be {SURFACES[surface][0]}x{SURFACES[surface][1]}")
            elif surface is not None:
                fail(errors, f"{path}.surface", "expected front or back")

    constraints = require(data, "constraints", dict, "$", errors)
    if constraints is not None:
        require(constraints, "language", str, "$.constraints", errors)
        require(constraints, "required_content", list, "$.constraints", errors)
        require(constraints, "forbidden_content", list, "$.constraints", errors)
        require(constraints, "palette_roles", dict, "$.constraints", errors)
        require(constraints, "motion_intent", str, "$.constraints", errors)

    candidates = require(data, "candidates", list, "$", errors)
    candidate_keys: set[tuple[str, int]] = set()
    candidate_artifacts: dict[tuple[str, int], set[tuple[str, str, str]]] = {}
    candidate_specs: dict[tuple[str, int], tuple[str, str] | None] = {}
    if candidates is not None:
        if len(candidates) != 3:
            fail(errors, "$.candidates", "expected exactly 3 candidates")
        for index, candidate in enumerate(candidates):
            path = f"$.candidates[{index}]"
            if not isinstance(candidate, dict):
                fail(errors, path, "expected object")
                continue
            candidate_id = require(candidate, "id", str, path, errors)
            revision = require(candidate, "revision", int, path, errors)
            require(candidate, "rationale", str, path, errors)
            require(candidate, "tradeoffs", list, path, errors)
            if candidate.get("status") != "review_only":
                fail(errors, f"{path}.status", "expected review_only")
            if candidate_id is not None and revision is not None:
                key = (candidate_id, revision)
                if key in candidate_keys:
                    fail(errors, path, "duplicate candidate id and revision")
                candidate_keys.add(key)
                if candidate.get("design_spec") is not None:
                    candidate_specs[key] = validate_spec_binding(
                        candidate["design_spec"], f"{path}.design_spec", contract_path, check_files, errors
                    )
            artifacts = require(candidate, "artifacts", list, path, errors)
            artifact_surfaces: set[str] = set()
            artifact_bindings: set[tuple[str, str, str]] = set()
            if artifacts is None:
                continue
            for artifact_index, artifact in enumerate(artifacts):
                artifact_path = f"{path}.artifacts[{artifact_index}]"
                if not isinstance(artifact, dict):
                    fail(errors, artifact_path, "expected object")
                    continue
                surface = require(artifact, "surface", str, artifact_path, errors)
                relative_path = require(artifact, "path", str, artifact_path, errors)
                width = require(artifact, "width", int, artifact_path, errors)
                height = require(artifact, "height", int, artifact_path, errors)
                digest = require(artifact, "sha256", str, artifact_path, errors)
                if surface is not None:
                    if surface in artifact_surfaces:
                        fail(errors, f"{artifact_path}.surface", "duplicate candidate surface")
                    artifact_surfaces.add(surface)
                    if surface not in target_map:
                        fail(errors, f"{artifact_path}.surface", "surface is not declared in targets")
                    elif (width, height) != target_map[surface]:
                        fail(errors, artifact_path, "dimensions do not match target")
                if digest is not None and (len(digest) != 64 or set(digest.lower()) - HEX_DIGITS):
                    fail(errors, f"{artifact_path}.sha256", "expected 64 hexadecimal characters")
                if relative_path is not None and not safe_relative_path(relative_path):
                    fail(errors, f"{artifact_path}.path", "expected canonical contract-relative path")
                if surface is not None and relative_path is not None and digest is not None:
                    artifact_bindings.add((surface, relative_path, digest.lower()))
                if check_files and relative_path is not None:
                    file_path = (contract_path.parent / relative_path).resolve()
                    try:
                        file_path.relative_to(contract_path.parent.resolve())
                    except ValueError:
                        fail(errors, f"{artifact_path}.path", "resolved path escapes the contract directory")
                        continue
                    if not file_path.is_file():
                        fail(errors, f"{artifact_path}.path", f"file not found: {file_path}")
                        continue
                    try:
                        actual_dimensions = image_dimensions(file_path)
                    except ValueError as exc:
                        fail(errors, f"{artifact_path}.path", str(exc))
                    else:
                        if actual_dimensions != (width, height):
                            fail(errors, artifact_path, f"file dimensions are {actual_dimensions[0]}x{actual_dimensions[1]}")
                    actual_digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
                    if digest is not None and actual_digest != digest.lower():
                        fail(errors, f"{artifact_path}.sha256", "digest does not match file")
            for surface, target in ((item.get("surface"), item) for item in targets or [] if isinstance(item, dict)):
                if target.get("required") is True and surface not in artifact_surfaces:
                    fail(errors, f"{path}.artifacts", f"missing required {surface} artifact")
            if candidate_id is not None and revision is not None:
                candidate_artifacts[(candidate_id, revision)] = artifact_bindings

    gate = require(data, "selection_gate", dict, "$", errors)
    if gate is not None:
        status = gate.get("status")
        selected_id = gate.get("selected_candidate_id")
        selected_revision = gate.get("selected_revision")
        approval = gate.get("approval_record")
        if status == "pending":
            if selected_id is not None or selected_revision is not None or approval is not None:
                fail(errors, "$.selection_gate", "pending gate cannot contain a selection or approval")
        elif status == "approved":
            selected_key = (selected_id, selected_revision)
            if selected_key not in candidate_keys:
                fail(errors, "$.selection_gate", "approved selection must match one candidate")
            if selected_key not in candidate_specs:
                fail(errors, "$.selection_gate.design_spec", "selected candidate requires a design_spec binding")
            if not isinstance(approval, dict):
                fail(errors, "$.selection_gate.approval_record", "expected object for approved gate")
            else:
                for key in ("actor", "text", "approved_at"):
                    value = require(approval, key, str, "$.selection_gate.approval_record", errors)
                    if value == "":
                        fail(errors, f"$.selection_gate.approval_record.{key}", "must not be empty")
                approved_spec = validate_spec_binding(
                    approval.get("design_spec"), "$.selection_gate.approval_record.design_spec",
                    contract_path, False, errors,
                )
                if approved_spec is not None and approved_spec != candidate_specs.get(selected_key):
                    fail(errors, "$.selection_gate.approval_record.design_spec", "must match the selected candidate design_spec exactly")
                approved_artifacts = require(approval, "artifacts", list, "$.selection_gate.approval_record", errors)
                bindings: set[tuple[str, str, str]] = set()
                if approved_artifacts is not None:
                    for index, artifact in enumerate(approved_artifacts):
                        artifact_path = f"$.selection_gate.approval_record.artifacts[{index}]"
                        if not isinstance(artifact, dict):
                            fail(errors, artifact_path, "expected object")
                            continue
                        surface = require(artifact, "surface", str, artifact_path, errors)
                        relative_path = require(artifact, "path", str, artifact_path, errors)
                        digest = require(artifact, "sha256", str, artifact_path, errors)
                        if digest is not None and (len(digest) != 64 or set(digest.lower()) - HEX_DIGITS):
                            fail(errors, f"{artifact_path}.sha256", "expected 64 hexadecimal characters")
                        if relative_path is not None and not safe_relative_path(relative_path):
                            fail(errors, f"{artifact_path}.path", "expected canonical contract-relative path")
                        if surface is not None and relative_path is not None and digest is not None:
                            bindings.add((surface, relative_path, digest.lower()))
                    if len(bindings) != len(approved_artifacts):
                        fail(errors, "$.selection_gate.approval_record.artifacts", "contains duplicate artifact bindings")
                    if selected_key in candidate_artifacts and bindings != candidate_artifacts[selected_key]:
                        fail(errors, "$.selection_gate.approval_record.artifacts", "must match the selected candidate artifacts exactly")
        else:
            fail(errors, "$.selection_gate.status", "expected pending or approved")

    verification = require(data, "verification", dict, "$", errors)
    if verification is not None and verification.get("hardware") not in {"unknown", "passed", "failed"}:
        fail(errors, "$.verification.hardware", "expected unknown, passed, or failed")
    handoff = require(data, "handoff", dict, "$", errors)
    if handoff is not None and handoff.get("production_kind") not in {"bsbctl_scene", "standalone_animation"}:
        fail(errors, "$.handoff.production_kind", "expected bsbctl_scene or standalone_animation")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-files", action="store_true", help="check PNG/GIF dimensions and artifact/specification hashes")
    parser.add_argument("contract", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.contract.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_contract(data, args.contract, args.check_files)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    mode = "structure and files" if args.check_files else "structure"
    print(f"OK: {args.contract} ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
