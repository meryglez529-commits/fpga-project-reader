#!/usr/bin/env python3
"""Validate one Mode 4 new-board bring-up package and its Mode 3 gate."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType


REQUIRED_FILES = (
    "STATUS.md", "SOURCE_REGISTER.md", "BOARD_CONTRACT.md", "INTERFACE_MATRIX.md",
    "BRINGUP_PLAN.md", "ACCEPTANCE_MATRIX.md", "DEMO_DEPENDENCY_MATRIX.md", "MODE3_HANDOFF.md",
    "release/RELEASE_MANIFEST.md",
)
REQUIRED_DIRS = ("demos", "hardware-handoff", "work", "out", "release")
VALID_STATES = {
    "DISCOVERED", "CONTRACT_READY", "DEMOS_IN_PROGRESS", "DEMO_BUILD_READY",
    "INTERFACES_QUALIFIED", "PRODUCT_BASELINE_READY", "MODE3_READY", "HARDWARE_BLOCKED",
}
PLACEHOLDER_RE = re.compile(r"<[^>\n]+>")
STATUS_RE = re.compile(r"^-\s*State:\s*`?([A-Z0-9_]+)`?\s*$", re.MULTILINE)
FIELD_RE = re.compile(r"^-\s*([^:]+):\s*`?(.+?)`?\s*$", re.MULTILINE)
SHA256_RE = re.compile(r"^[0-9A-Fa-f]{64}$")
EMPTY = {"", "-", "N/A", "NONE", "NOT_APPLICABLE", "NOT_CREATED", "NOT_RUN"}
PASS_BUILD = {"PASS", "BUILD_PASS"}


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def fields(text: str) -> dict[str, str]:
    return {key.strip().lower(): value.strip().strip("`") for key, value in FIELD_RE.findall(text)}


def markdown_table(text: str) -> tuple[list[str], list[dict[str, str]]]:
    raw_rows: list[list[str]] = []
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        raw_rows.append(cells)
    if not raw_rows:
        return [], []
    header = [cell.lower() for cell in raw_rows[0]]
    rows = [dict(zip(header, row)) for row in raw_rows[1:] if len(row) == len(header)]
    return header, rows


def meaningful_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return [item for item in path.rglob("*") if item.is_file() and item.name != ".gitkeep" and item.stat().st_size]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def load_script_module(name: str, module_name: str) -> ModuleType:
    script = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(module_name, script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load demo validator: {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_demo_validator() -> ModuleType:
    return load_script_module("validate-demo-work-package.py", "fpga_cowork_demo_validator")


def resolve_release_artifact(unit: Path, value: str) -> Path | None:
    raw = Path(value)
    candidates = [raw] if raw.is_absolute() else [unit / raw, unit / "release" / raw]
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def validate(
    unit: Path,
    design_root: Path | None = None,
    project_root: Path | None = None,
) -> tuple[list[str], list[str], str | None]:
    errors: list[str] = []
    warnings: list[str] = []
    if not unit.is_dir():
        return [f"bring-up unit not found: {unit}"], warnings, None

    for relative in REQUIRED_FILES:
        path = unit / relative
        if not path.is_file() or not path.stat().st_size:
            errors.append(f"missing or empty file: {relative}")
    for relative in REQUIRED_DIRS:
        if not (unit / relative).is_dir():
            errors.append(f"missing directory: {relative}")

    state: str | None = None
    status_fields: dict[str, str] = {}
    status_path = unit / "STATUS.md"
    if status_path.is_file():
        status_text = read_text(status_path)
        status_fields = fields(status_text)
        match = STATUS_RE.search(status_text)
        if not match:
            errors.append("STATUS.md: missing '- State: `...`'")
        else:
            state = match.group(1)
            if state not in VALID_STATES:
                errors.append(f"STATUS.md: invalid bring-up state {state}")

    all_text = "\n".join(read_text(unit / name) for name in REQUIRED_FILES if (unit / name).is_file())
    placeholders = sorted(set(PLACEHOLDER_RE.findall(all_text)))
    if placeholders:
        message = f"unresolved placeholders: {', '.join(placeholders[:10])}"
        if state in {"INTERFACES_QUALIFIED", "PRODUCT_BASELINE_READY", "MODE3_READY"}:
            errors.append(message)
        else:
            warnings.append(message)

    interface_rows: list[dict[str, str]] = []
    acceptance_rows: list[dict[str, str]] = []
    if (unit / "INTERFACE_MATRIX.md").is_file():
        _, interface_rows = markdown_table(read_text(unit / "INTERFACE_MATRIX.md"))
    if (unit / "ACCEPTANCE_MATRIX.md").is_file():
        _, acceptance_rows = markdown_table(read_text(unit / "ACCEPTANCE_MATRIX.md"))

    required_interfaces = {
        row.get("interface", ""): row for row in interface_rows
        if row.get("required", "").upper() in {"YES", "Y", "TRUE", "REQUIRED"}
        and not PLACEHOLDER_RE.search(row.get("interface", ""))
    }
    acceptance_by_interface = {row.get("interface", ""): row for row in acceptance_rows}
    for interface in required_interfaces:
        if interface not in acceptance_by_interface:
            errors.append(f"required interface missing from ACCEPTANCE_MATRIX.md: {interface}")

    demo_validator = load_demo_validator()
    demo_units = [path.parent for path in (unit / "demos").glob("*/*/STATUS.md")]
    demo_states: dict[Path, str | None] = {}
    for demo in demo_units:
        demo_errors, demo_warnings, demo_state = demo_validator.validate(demo, None)
        demo_states[demo.resolve()] = demo_state
        for error in demo_errors:
            errors.append(f"demo {demo.relative_to(unit).as_posix()}: {error}")
        for warning in demo_warnings:
            warnings.append(f"demo {demo.relative_to(unit).as_posix()}: {warning}")

    blocked = any(row.get("board result", "").upper() == "FPGA_READY_HARDWARE_BLOCKED" for row in acceptance_rows)
    if (blocked or state == "HARDWARE_BLOCKED") and not meaningful_files(unit / "hardware-handoff"):
        errors.append("hardware-blocked state requires a non-empty hardware-handoff record")

    release_path = unit / "release/RELEASE_MANIFEST.md"
    valid_release_rows = 0
    if release_path.is_file():
        _, release_rows = markdown_table(read_text(release_path))
        for row in release_rows:
            artifact_value = row.get("artifact", "").strip()
            digest_value = row.get("sha-256", "").strip()
            if not artifact_value or PLACEHOLDER_RE.search(artifact_value):
                continue
            artifact = resolve_release_artifact(unit, artifact_value)
            if artifact is None:
                errors.append(f"release artifact not found: {artifact_value}")
                continue
            if not SHA256_RE.fullmatch(digest_value):
                errors.append(f"release artifact has invalid SHA-256: {artifact_value}")
                continue
            if sha256(artifact) != digest_value.upper():
                errors.append(f"release artifact SHA-256 mismatch: {artifact_value}")
                continue
            valid_release_rows += 1

    release_files = [
        path for path in meaningful_files(unit / "release")
        if path.name != "RELEASE_MANIFEST.md"
    ]
    if release_files and not valid_release_rows:
        errors.append("release contains artifacts but no valid hashed release-manifest row")

    dependency_path = unit / "DEMO_DEPENDENCY_MATRIX.md"
    if dependency_path.is_file():
        _, dependency_rows = markdown_table(read_text(dependency_path))
        for row in dependency_rows:
            asset_class = row.get("asset class", "").upper()
            consumers = row.get("product consumers", "").upper()
            if asset_class in {"TEST_ONLY", "GENERATED", "OBSOLETE"} and consumers not in EMPTY:
                errors.append(
                    f"DEMO_DEPENDENCY_MATRIX.md: {asset_class} source has product consumer '{consumers}'"
                )

    handoff_path = unit / "MODE3_HANDOFF.md"
    handoff_text = read_text(handoff_path) if handoff_path.is_file() else ""
    handoff_fields = fields(handoff_text)
    handoff_state_match = STATUS_RE.search(handoff_text)
    handoff_state = handoff_state_match.group(1) if handoff_state_match else None

    if design_root:
        if not design_root.is_dir():
            errors.append(f"official design root not found: {design_root}")
        else:
            spilled = [
                path for name in (".Xil", ".runs", ".gen", "xsim.dir")
                for path in design_root.rglob(name) if path.is_dir()
            ]
            if spilled:
                sample = ", ".join(str(path) for path in spilled[:4])
                errors.append(f"generated tool workspace found in official design root: {sample}")

    if project_root:
        marker = unit / "work/.artifact_start"
        if not marker.is_file():
            errors.append("missing work/.artifact_start for artifact-spill boundary")
        elif not project_root.is_dir():
            errors.append(f"project root not found: {project_root}")
        else:
            spill_validator = load_script_module("scan-artifact-spill.py", "fpga_cowork_spill_validator")
            findings = spill_validator.scan(
                project_root,
                spill_validator.DEFAULT_PATTERNS + ["tmp"],
                5,
                marker.stat().st_mtime,
            )
            if findings:
                sample = ", ".join(str(path) for path in findings[:6])
                errors.append(f"runtime artifacts spilled outside AI-work after unit start: {sample}")

    if state == "MODE3_READY":
        if not required_interfaces:
            errors.append("MODE3_READY requires at least one required interface")
        if handoff_state != "MODE3_READY":
            errors.append("STATUS.md is MODE3_READY but MODE3_HANDOFF.md is not MODE3_READY")
        if design_root is None:
            errors.append("MODE3_READY validation requires --design-root")
        if project_root is None:
            errors.append("MODE3_READY validation requires --project-root for artifact-spill checks")
        status_design_value = status_fields.get("authorized design root", "")
        handoff_design_value = handoff_fields.get("official design root", "")
        if not status_design_value or PLACEHOLDER_RE.search(status_design_value):
            errors.append("STATUS.md lacks the authorized design root")
        if not handoff_design_value or PLACEHOLDER_RE.search(handoff_design_value):
            errors.append("MODE3_HANDOFF.md lacks the official design root")
        if design_root and project_root and status_design_value and handoff_design_value:
            for label, value in (
                ("STATUS.md authorized design root", status_design_value),
                ("MODE3_HANDOFF.md official design root", handoff_design_value),
            ):
                declared = Path(value)
                if not declared.is_absolute():
                    declared = project_root / declared
                if declared.resolve() != design_root.resolve():
                    errors.append(f"{label} does not match --design-root: {declared}")
        product_value = handoff_fields.get("product project", "")
        if not product_value or product_value.upper() in EMPTY or PLACEHOLDER_RE.search(product_value):
            errors.append("MODE3_HANDOFF.md lacks a qualified product project path")
        elif design_root:
            product_path = Path(product_value)
            if not product_path.is_absolute():
                product_path = design_root / product_path
            if not product_path.exists():
                errors.append(f"product project path not found: {product_path}")

        for interface, row in required_interfaces.items():
            acceptance = acceptance_by_interface.get(interface, {})
            build = acceptance.get("build", "").upper()
            board = acceptance.get("board result", "").upper()
            waiver = acceptance.get("waiver", "").upper()
            waived = waiver not in EMPTY
            if build not in PASS_BUILD and not waived:
                errors.append(f"required interface {interface}: build is not BUILD_PASS")
            if board != "BOARD_PASS" and not waived:
                errors.append(f"required interface {interface}: neither BOARD_PASS nor explicit waiver")
            demo_value = acceptance.get("demo unit", "")
            if demo_value and not waived and not PLACEHOLDER_RE.search(demo_value):
                demo_path = Path(demo_value)
                if not demo_path.is_absolute():
                    demo_path = unit / "demos" / demo_path
                if not demo_path.is_dir():
                    errors.append(f"required interface {interface}: demo unit not found: {demo_path}")
                elif board == "BOARD_PASS" and demo_states.get(demo_path.resolve()) != "BOARD_PASS":
                    errors.append(
                        f"required interface {interface}: acceptance says BOARD_PASS but demo state is "
                        f"{demo_states.get(demo_path.resolve())}"
                    )

        if not valid_release_rows:
            errors.append("MODE3_READY requires at least one valid hashed release artifact")

    return errors, warnings, state


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate a Mode 4 new-board work package.")
    parser.add_argument("unit", type=Path)
    parser.add_argument("--design-root", type=Path, default=None)
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    errors, warnings, state = validate(args.unit, args.design_root, args.project_root)
    for warning in warnings:
        print(f"WARN: {warning}")
    if errors:
        print(f"FAIL: {args.unit}")
        for error in errors:
            print(f"  - {error}")
        return 1
    if args.strict and warnings:
        print(f"FAIL (strict): {args.unit}")
        return 1
    print(f"PASS: {args.unit} (state={state})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
