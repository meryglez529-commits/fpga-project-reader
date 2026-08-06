#!/usr/bin/env python3
"""Validate the fpga-cowork AI-work skeleton and Mode 1 entry documents.

Use validate-foundation.py as the companion evidence check. This script keeps
the bootstrap check readable and accepts either canonical simulation-SOP path.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_DIRS = (
    "guide", "guide/data-paths", "guide/diagrams", "annotations", "env",
    "features", "scripts", "reports", "reports/baseline",
)
REQUIRED_TOP = ("README.md", "LOG.md", "OPEN-QUESTIONS.md", ".gitignore")
FOUNDATION_DOCS = (
    "env/ENVIRONMENT.md", "env/HARDWARE.md", "env/DEBUG_CAPABILITY.md",
    "env/SETUP_STATUS.md", "env/RULES.md", "env/SNAPSHOTS.md", "env/GLOSSARY.md",
)
PLACEHOLDER = re.compile(r"<[^>]*(?:TBD|TODO|YYYY|填写|待确认)[^>]*>", re.IGNORECASE)


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def validate(ai_work: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not ai_work.is_dir():
        return [f"AI-work directory not found: {ai_work}"], warnings

    for directory in REQUIRED_DIRS:
        if not (ai_work / directory).is_dir():
            errors.append(f"missing directory: AI-work/{directory}")
    for name in REQUIRED_TOP:
        path = ai_work / name
        if not path.is_file():
            errors.append(f"missing file: AI-work/{name}")
        elif not path.stat().st_size:
            errors.append(f"empty file: AI-work/{name}")

    attempted = any((ai_work / name).is_file() for name in FOUNDATION_DOCS)
    canonical_sop = [
        ai_work / "env" / "SIMULATION.md",
        ai_work / "guide" / "VIVADO_SIM_SOP.md",
    ]
    if attempted:
        for name in FOUNDATION_DOCS:
            path = ai_work / name
            if not path.is_file() or not read_text(path).strip():
                errors.append(f"Mode 1 incomplete: missing or empty AI-work/{name}")
                continue
            count = len(PLACEHOLDER.findall(read_text(path)))
            if count:
                warnings.append(f"AI-work/{name}: {count} unresolved placeholder(s)")
        if not any(path.is_file() and read_text(path).strip() for path in canonical_sop):
            errors.append("Mode 1 incomplete: missing env/SIMULATION.md and guide/VIVADO_SIM_SOP.md")
        status = ai_work / "env" / "SETUP_STATUS.md"
        if status.is_file() and not re.search(r"(DISCOVERED|READY|BLOCKED|IN_PROGRESS)", read_text(status), re.IGNORECASE):
            errors.append("env/SETUP_STATUS.md: missing a declared readiness state")
    else:
        warnings.append("Mode 1 foundation has not been attempted; only bootstrap skeleton is present")

    log = ai_work / "LOG.md"
    if log.is_file() and not re.search(r"\d{4}-\d{2}-\d{2}", read_text(log)):
        warnings.append("LOG.md has no dated entry")
    questions = ai_work / "OPEN-QUESTIONS.md"
    if questions.is_file() and not re.search(r"\|", read_text(questions)):
        warnings.append("OPEN-QUESTIONS.md has no structured question table")
    return errors, warnings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate fpga-cowork AI-work skeleton.")
    parser.add_argument("ai_work", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    errors, warnings = validate(args.ai_work)
    for warning in warnings:
        print(f"WARN: {warning}")
    if errors:
        print(f"FAIL: {args.ai_work}")
        for error in errors:
            print(f"  - {error}")
        return 1
    if args.strict and warnings:
        print(f"FAIL (strict): {args.ai_work}")
        return 1
    print(f"PASS: {args.ai_work}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
