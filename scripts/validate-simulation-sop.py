#!/usr/bin/env python3
"""Check that the canonical simulation SOP has evidence-bearing sections."""

from __future__ import annotations

import argparse

import re
import sys
from pathlib import Path


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate canonical project simulation SOP.")
    parser.add_argument("ai_work", type=Path)
    args = parser.parse_args(argv)
    candidates = (
        args.ai_work / "env" / "SIMULATION.md",
        args.ai_work / "guide" / "VIVADO_SIM_SOP.md",
    )
    path = next((item for item in candidates if item.is_file()), None)
    if path is None:
        print("FAIL: missing env/SIMULATION.md and guide/VIVADO_SIM_SOP.md")
        return 1
    text = read_text(path)
    checks = {
        "toolchain": r"Vivado|xsim|ModelSim|Questa",
        "command or Tcl evidence": r"vivado|xvlog|xelab|xsim|launch_simulation|\.tcl",
        "known-good or blocked outcome": r"known.good|PASS|SIM_READY|SIM_BLOCKED|BLOCKED|可用|不可用|失败",
        "output containment": r"AI-work|reports/baseline|out/sim",
        "evidence/log reference": r"log|\.jou|report|证据|日志",
    }
    missing = [name for name, pattern in checks.items() if not re.search(pattern, text, re.IGNORECASE)]
    if missing:
        print(f"FAIL: {path}")
        for name in missing:
            print(f"  - missing {name}")
        return 1
    if re.search(r"SIM_BLOCKED|BLOCKED", text, re.IGNORECASE) and not re.search(r"next|下一步|blocker|阻塞", text, re.IGNORECASE):
        print(f"WARN: {path}: blocked state has no explicit next action")
    print(f"PASS: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
