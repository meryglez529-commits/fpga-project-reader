#!/usr/bin/env python3
"""Validate the mode-neutral fpga-cowork AI-work skeleton.

Run a mode-specific validator for Mode 1 foundations, Mode 3 feature units, or
Mode 4 new-board work packages. Partial env/ or bringup/ content must not make
this common bootstrap validator silently select a mode.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_DIRS = (
    "guide", "annotations", "env", "features", "bringup", "scripts", "reports",
)
REQUIRED_TOP = ("README.md", "LOG.md", "OPEN-QUESTIONS.md", ".gitignore")
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

    for relative in ("env/RULES.md", "env/SETUP_STATUS.md"):
        path = ai_work / relative
        if path.is_file():
            count = len(PLACEHOLDER.findall(read_text(path)))
            if count:
                warnings.append(f"AI-work/{relative}: {count} unresolved placeholder(s)")

    log = ai_work / "LOG.md"
    if log.is_file() and not re.search(r"\d{4}-\d{2}-\d{2}", read_text(log)):
        warnings.append("LOG.md has no dated entry")
    questions = ai_work / "OPEN-QUESTIONS.md"
    if questions.is_file() and not re.search(r"\|", read_text(questions)):
        warnings.append("OPEN-QUESTIONS.md has no structured question table")
    if not any((ai_work / area).iterdir() for area in ("features", "bringup") if (ai_work / area).is_dir()):
        warnings.append("no Mode 3 feature or Mode 4 bring-up unit is present yet")
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
