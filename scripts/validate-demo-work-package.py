#!/usr/bin/env python3
"""Validate one Mode 4 new-board demo work package."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_FILES = ("REQUIREMENTS.md", "ARCHITECTURE.md", "STATUS.md", "REUSE_MANIFEST.md")
REQUIRED_DIRS = (
    "sim", "build", "board-test", "out", "out/sim", "out/synth", "out/impl",
    "out/bitstream/candidate", "out/bitstream/obsolete", "out/board-test", "release/bitstream",
)
VALID_STATES = {
    "PLANNED", "CONTRACT_READY", "BUILD_PASS", "READY_FOR_BOARD", "BOARD_PASS",
    "FPGA_READY_HARDWARE_BLOCKED", "FAILED_FPGA", "STALE", "NOT_APPLICABLE", "OBSOLETE",
}
BUILD_STATES = {"BUILD_PASS", "READY_FOR_BOARD", "BOARD_PASS", "FPGA_READY_HARDWARE_BLOCKED"}
BOARD_EVIDENCE_STATES = {"BOARD_PASS", "FPGA_READY_HARDWARE_BLOCKED"}
FORBIDDEN_PRODUCT_CLASSES = {"TEST_ONLY", "GENERATED", "OBSOLETE"}
EMPTY_CONSUMERS = {"", "-", "N/A", "NONE", "NOT_APPLICABLE"}
PLACEHOLDER_RE = re.compile(r"<[^>\n]+>")
STATE_RE = re.compile(r"^-\s*State:\s*`?([A-Z0-9_]+)`?\s*$", re.MULTILINE)


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def meaningful_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return [item for item in path.rglob("*") if item.is_file() and item.name != ".gitkeep" and item.stat().st_size]


def markdown_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if not cells or all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def validate(unit: Path, design_root: Path | None = None) -> tuple[list[str], list[str], str | None]:
    errors: list[str] = []
    warnings: list[str] = []
    if not unit.is_dir():
        return [f"demo unit not found: {unit}"], warnings, None

    for relative in REQUIRED_FILES:
        path = unit / relative
        if not path.is_file() or not path.stat().st_size:
            errors.append(f"missing or empty file: {relative}")
    for relative in REQUIRED_DIRS:
        if not (unit / relative).is_dir():
            errors.append(f"missing directory: {relative}")

    state: str | None = None
    status_path = unit / "STATUS.md"
    if status_path.is_file():
        status_text = read_text(status_path)
        match = STATE_RE.search(status_text)
        if not match:
            errors.append("STATUS.md: missing '- State: `...`'")
        else:
            state = match.group(1)
            if state not in VALID_STATES:
                errors.append(f"STATUS.md: invalid demo state {state}")

    all_text = "\n".join(read_text(unit / name) for name in REQUIRED_FILES if (unit / name).is_file())
    placeholders = sorted(set(PLACEHOLDER_RE.findall(all_text)))
    if placeholders:
        message = f"unresolved placeholders: {', '.join(placeholders[:8])}"
        if state and state not in {"PLANNED", "NOT_APPLICABLE"}:
            errors.append(message)
        else:
            warnings.append(message)

    if state in BUILD_STATES:
        build_evidence = []
        for relative in ("out/synth", "out/impl", "out/bitstream/candidate"):
            build_evidence.extend(meaningful_files(unit / relative))
        if not build_evidence:
            errors.append(f"{state} requires build evidence under out/synth, out/impl, or out/bitstream/candidate")

    if state in BOARD_EVIDENCE_STATES and not meaningful_files(unit / "out/board-test"):
        errors.append(f"{state} requires evidence under out/board-test")

    reuse = unit / "REUSE_MANIFEST.md"
    if reuse.is_file():
        rows = markdown_rows(read_text(reuse))
        for cells in rows[1:]:
            if len(cells) < 5:
                continue
            asset_class = cells[1].upper()
            consumer = cells[4].upper()
            if asset_class in FORBIDDEN_PRODUCT_CLASSES and consumer not in EMPTY_CONSUMERS:
                errors.append(
                    f"REUSE_MANIFEST.md: {asset_class} asset '{cells[0]}' has product consumer '{cells[4]}'"
                )

    if meaningful_files(unit / "release/bitstream"):
        status_text = read_text(status_path) if status_path.is_file() else ""
        if not re.search(r"Qualified image:.*[0-9A-Fa-f]{64}", status_text):
            errors.append("release/bitstream contains files but STATUS.md lacks a qualified image SHA-256")

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

    return errors, warnings, state


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate a Mode 4 demo work package.")
    parser.add_argument("unit", type=Path)
    parser.add_argument("--design-root", type=Path, default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    errors, warnings, state = validate(args.unit, args.design_root)
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
