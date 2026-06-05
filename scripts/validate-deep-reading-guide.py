#!/usr/bin/env python3
"""Structure checker for FPGA selected-path deep-reading guides.

This script is a guardrail, not an RTL reviewer. It catches the common failure
where a "deep read" becomes a conclusion summary and loses the per-file reading
steps required by the fpga-cowork skill.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_FIELDS = [
    ("本步目标", re.compile(r"本步目标\s*[:：]")),
    ("搜索入口", re.compile(r"搜索入口\s*[:：]")),
    ("本模块相关信号/相关信号", re.compile(r"(本模块.*相关信号|相关信号)\s*[:：]")),
    ("先忽略", re.compile(r"先忽略\s*[:：]")),
    ("代码阅读顺序", re.compile(r"代码阅读顺序\s*[:：]")),
    ("读完应能回答", re.compile(r"读完应能回答\s*[:：]")),
    ("下一步", re.compile(r"下一步\s*[:：]")),
]

HEADING_RE = re.compile(r"^(#{2,5})\s+(.+?)\s*$")


@dataclass
class Section:
    level: int
    title: str
    line: int
    body: str


def read_markdown(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"ERROR: {path} is not valid UTF-8: {exc}") from exc


def split_sections(text: str) -> list[Section]:
    lines = text.splitlines()
    headings: list[tuple[int, int, str]] = []

    for index, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if match:
            headings.append((index, len(match.group(1)), match.group(2).strip()))

    sections: list[Section] = []
    for pos, (start, level, title) in enumerate(headings):
        end = len(lines)
        for next_start, next_level, _ in headings[pos + 1 :]:
            if next_level <= level:
                end = next_start
                break
        sections.append(
            Section(
                level=level,
                title=title,
                line=start + 1,
                body="\n".join(lines[start + 1 : end]),
            )
        )

    return sections


def is_file_reading_pass(section: Section) -> bool:
    if "打开" in section.title:
        return True

    # Support chapters may name several files in the body instead of the
    # heading. Count them if they still use the required pass template.
    if "支撑模块" in section.title:
        return all(pattern.search(section.body) for _, pattern in REQUIRED_FIELDS)

    return False


def find_file_reading_passes(text: str) -> list[Section]:
    return [section for section in split_sections(text) if is_file_reading_pass(section)]


def validate(text: str, min_passes: int, summary_only: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not text.strip():
        return ["document is empty"], warnings

    if summary_only:
        warnings.append("summary-only mode: selected-path pass checks skipped")
        return errors, warnings

    passes = find_file_reading_passes(text)
    if len(passes) < min_passes:
        errors.append(f"found {len(passes)} file-reading pass(es), expected at least {min_passes}")

    for section in passes:
        missing = [label for label, pattern in REQUIRED_FIELDS if not pattern.search(section.body)]
        if missing:
            errors.append(
                f"line {section.line}: '{section.title}' is missing "
                + ", ".join(missing)
            )

    if not re.search(r"^##+ .*?(上板|仿真|验证|ILA|ila)", text, re.MULTILINE):
        warnings.append("no final verification/ILA section found")
    if not re.search(r"^##+ .*关键证据", text, re.MULTILINE):
        warnings.append("no key evidence index section found")
    if not re.search(r"(CDC|FIFO|缓存|跨时钟)", text):
        warnings.append("no CDC/FIFO/cache discussion found")

    return errors, warnings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a path-specific FPGA code reading guide."
    )
    parser.add_argument("guide", type=Path, help="Markdown guide to validate")
    parser.add_argument("--min-passes", type=int, default=5)
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="skip selected-path guide checks for an intentionally summary-only document",
    )
    args = parser.parse_args(argv)

    if not args.guide.exists():
        print(f"ERROR: file not found: {args.guide}")
        return 2

    text = read_markdown(args.guide)
    errors, warnings = validate(text, args.min_passes, args.summary_only)

    for warning in warnings:
        print(f"WARN: {warning}")

    if errors:
        print(f"FAIL: {args.guide}")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"PASS: {args.guide}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
