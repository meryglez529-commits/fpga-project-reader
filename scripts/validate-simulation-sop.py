#!/usr/bin/env python3
"""Validate project-level simulation SOP presence and key fields."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PATTERNS = [
    ("toolchain/path", re.compile(r"Vivado|xsim|ModelSim|Questa", re.IGNORECASE)),
    ("working path", re.compile(r"可用|推荐|working|PASS", re.IGNORECASE)),
    ("broken path or limitation", re.compile(r"不可用|失败|BLOCKED|Broken|加密|Webtalk|wbtcv|init\.tcl", re.IGNORECASE)),
    ("batch flow", re.compile(r"batch|PowerShell|run_manual|xvlog|xelab", re.IGNORECASE)),
    ("GUI flow", re.compile(r"GUI|Tcl Console|launch_simulation", re.IGNORECASE)),
    ("verification record", re.compile(r"验证记录|验证日期|testbench|结果", re.IGNORECASE)),
]


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_bytes().decode("utf-8", errors="replace")


def find_sop(ai_work: Path) -> Path | None:
    candidates = [
        ai_work / "env" / "SIMULATION.md",
        ai_work / "guide" / "VIVADO_SIM_SOP.md",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate simulation SOP in AI-work.")
    parser.add_argument("ai_work", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    sop = find_sop(args.ai_work)
    if not sop:
        print(f"FAIL: no simulation SOP found under {args.ai_work}/env or guide")
        return 1

    text = read_text(sop)
    errors: list[str] = []
    warnings: list[str] = []
    for label, rx in PATTERNS:
        if not rx.search(text):
            errors.append(f"missing {label}")

    if "SIMULATION BLOCKED" in text and not re.search(r"仍可使用|可替代|Mode 5", text):
        warnings.append("SIMULATION BLOCKED is recorded but no fallback/Mode 5 consequence is described")

    for warning in warnings:
        print(f"WARN: {warning}")
    if errors:
        print(f"FAIL: {sop}")
        for error in errors:
            print(f"  - {error}")
        return 1
    if args.strict and warnings:
        print(f"FAIL (strict): {sop}")
        return 1
    print(f"PASS: {sop}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
