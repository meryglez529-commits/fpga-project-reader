#!/usr/bin/env python3
"""Structure checker for an AI-work co-work environment.

This script is a guardrail, not a code reviewer. It catches the common failure
where Mode 4 (co-work environment setup) leaves required files empty, missing
must-have sections, or fills critical fields with placeholders.

Run after Mode 4 finishes, before any RTL edits begin.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Required structure
# ---------------------------------------------------------------------------

REQUIRED_DIRS = [
    "guide",
    "guide/data-paths",
    "guide/diagrams",
    "annotations",
    "env",
    "features",
    "scripts",
    "sim",
    "sim_out",
    "reports",
]

REQUIRED_TOP_FILES = [
    "README.md",
    "LOG.md",
    "OPEN-QUESTIONS.md",
    ".gitignore",
]

# Mode-4-specific required files
ENV_FILES = [
    "env/ENVIRONMENT.md",
    "env/HARDWARE.md",
    "env/RULES.md",
    "env/FOCUS.md",
    "env/SNAPSHOTS.md",
    "env/GLOSSARY.md",
    "env/SIMULATION.md",
]

# Required substring patterns inside each env/*.md.
# A file is "incomplete" if any of its required patterns is missing.
ENV_REQUIRED_PATTERNS: dict[str, list[tuple[str, re.Pattern[str]]]] = {
    "env/ENVIRONMENT.md": [
        ("Vivado executable path", re.compile(r"Vivado\s*\|\s*[`']?[A-Za-z]:[\\/]", re.IGNORECASE)),
        ("Vivado version line", re.compile(r"Vivado.*?\d{4}\.\d", re.IGNORECASE)),
        ("simulator selection", re.compile(r"(xsim|ModelSim|Questa|Riviera)", re.IGNORECASE)),
        ("file encoding row", re.compile(r"(UTF-?8|GBK|GB2312|ANSI)", re.IGNORECASE)),
        ("line ending row", re.compile(r"(CRLF|LF)")),
        ("disk free space", re.compile(r"(GB|TB|MB)\b")),
    ],
    "env/HARDWARE.md": [
        ("FPGA part", re.compile(r"\bxc\w+|\bep\w+|\b10c\w+", re.IGNORECASE)),
        ("device table heading", re.compile(r"\|\s*器件\s*\|") ),
        ("control module column", re.compile(r"控制模块|IP")),
    ],
    "env/RULES.md": [
        ("editable globs section", re.compile(r"可以直接改|editable")),
        ("ask-first section",      re.compile(r"必须先告诉|ask[\s-]?before")),
        ("read-only section",      re.compile(r"只读|read[\s-]?only")),
        ("brake section",          re.compile(r"刹车|brake|预算|budget")),
        ("pass/fail criteria",     re.compile(r"(Pass/Fail|PASS|通过)")),
        ("user confirmation slot", re.compile(r"用户口头确认|用户确认|confirmed by user")),
    ],
    "env/FOCUS.md": [
        ("focus description",      re.compile(r"功能描述|focus|焦点")),
        ("module/path field",      re.compile(r"涉及模块|module|通路")),
        ("symptom field",          re.compile(r"现象|期望|实际|symptom")),
    ],
    "env/SNAPSHOTS.md": [
        ("baseline section",       re.compile(r"baseline|基线", re.IGNORECASE)),
        ("rollback command",       re.compile(r"git reset|Copy-Item|rollback", re.IGNORECASE)),
        ("rollback drill row",     re.compile(r"回滚演练|rollback drill|drill", re.IGNORECASE)),
    ],
    "env/GLOSSARY.md": [
        ("glossary table heading", re.compile(r"\|\s*缩写\s*\|") ),
    ],
    "env/SIMULATION.md": [
        ("simulator/toolchain", re.compile(r"(Vivado|xsim|ModelSim|Questa)", re.IGNORECASE)),
        ("working simulation path", re.compile(r"(可用|推荐|working|PASS)", re.IGNORECASE)),
        ("broken/blocked path", re.compile(r"(不可用|失败|BLOCKED|Broken|加密|Webtalk|wbtcv|init\.tcl)", re.IGNORECASE)),
        ("batch/manual flow", re.compile(r"(batch|PowerShell|run_manual|xvlog|xelab)", re.IGNORECASE)),
        ("GUI flow", re.compile(r"(GUI|Tcl Console|launch_simulation)", re.IGNORECASE)),
    ],
}

# Files that, if they contain too many "TBD"/"⚠️" markers, are still placeholder.
PLACEHOLDER_PATTERNS = [
    re.compile(r"<填>"),
    re.compile(r"<填或"),
    re.compile(r"<YYYY-MM-DD"),
    re.compile(r"<commit hash>"),
]
PLACEHOLDER_MAX = 3   # 每份文件最多允许 3 个未填占位

# Required artifacts of a successful check_env run.
CHECK_ENV_OUTPUTS = [
    "sim_out/check_env.log",
]

# Required scripts (instantiated from skill templates).
REQUIRED_SCRIPTS = [
    "scripts/check_env.tcl",
    "scripts/run_sim.tcl",
    "scripts/run_synth.tcl",
]
RECOMMENDED_SCRIPTS = [
    "scripts/export_csv.tcl",
    "scripts/diff_report.tcl",
    "scripts/run_manual.tcl",
]


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_bytes().decode("utf-8", errors="replace")


def validate(ai_work: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not ai_work.is_dir():
        errors.append(f"AI-work directory not found: {ai_work}")
        return errors, warnings

    # 1. directory skeleton
    for d in REQUIRED_DIRS:
        if not (ai_work / d).is_dir():
            errors.append(f"missing directory: AI-work/{d}")

    # 2. top-level files
    for f in REQUIRED_TOP_FILES:
        p = ai_work / f
        if not p.is_file():
            errors.append(f"missing file: AI-work/{f}")
        elif p.stat().st_size == 0:
            errors.append(f"empty file: AI-work/{f}")

    # 3. env/ files (if any env file exists, treat the project as having attempted Mode 4)
    env_attempted = any((ai_work / f).is_file() for f in ENV_FILES)
    if env_attempted:
        for f in ENV_FILES:
            p = ai_work / f
            if not p.is_file():
                errors.append(f"Mode 4 incomplete: missing AI-work/{f}")
                continue
            text = read_text(p)
            if not text.strip():
                errors.append(f"empty file: AI-work/{f}")
                continue

            patterns = ENV_REQUIRED_PATTERNS.get(f, [])
            for label, regex in patterns:
                if not regex.search(text):
                    errors.append(f"AI-work/{f}: missing field — {label}")

            placeholder_hits = sum(len(p.findall(text)) for p in PLACEHOLDER_PATTERNS)
            if placeholder_hits > PLACEHOLDER_MAX:
                warnings.append(
                    f"AI-work/{f}: {placeholder_hits} placeholder markers "
                    f"still present (max {PLACEHOLDER_MAX} allowed)"
                )

        # 4. RULES.md must record explicit user confirmation as a checkbox or line
        rules = ai_work / "env/RULES.md"
        if rules.is_file():
            text = read_text(rules)
            confirmed = bool(re.search(
                r"(\[x\]\s*用户已确认|\[x\]\s*confirmed|"
                r"用户确认.*\d{4}-\d{2}-\d{2}|"
                r"confirmed by user.*\d{4}-\d{2}-\d{2})",
                text,
                re.IGNORECASE,
            ))
            if not confirmed:
                warnings.append(
                    "env/RULES.md: no explicit user confirmation recorded "
                    "(expected '[x] 用户已确认' with a date)"
                )

        # 5. check_env.log existence
        for art in CHECK_ENV_OUTPUTS:
            if not (ai_work / art).is_file():
                errors.append(f"Mode 4 incomplete: missing artifact AI-work/{art}")

        # 6. scripts present
        for s in REQUIRED_SCRIPTS:
            if not (ai_work / s).is_file():
                errors.append(f"missing script: AI-work/{s}")
        for s in RECOMMENDED_SCRIPTS:
            if not (ai_work / s).is_file():
                warnings.append(f"recommended script missing: AI-work/{s}")

    else:
        warnings.append(
            "no env/*.md files found — Mode 4 has not been run yet. "
            "This is OK if you only ran Mode 1/2/3, but RTL edits should not "
            "begin until Mode 4 is completed."
        )

    # 7. LOG.md should have at least one entry beyond the bootstrap line
    log_md = ai_work / "LOG.md"
    if log_md.is_file():
        text = read_text(log_md)
        # 计入 markdown table 行（| ... | ... |）
        rows = re.findall(r"^\|\s*\d{4}-\d{2}-\d{2}", text, re.MULTILINE)
        if not rows:
            warnings.append("LOG.md has no dated entries yet")

    # 8. OPEN-QUESTIONS.md table presence
    oq = ai_work / "OPEN-QUESTIONS.md"
    if oq.is_file():
        text = read_text(oq)
        if not re.search(r"\|\s*编号\s*\|", text):
            warnings.append("OPEN-QUESTIONS.md: missing the canonical table header")

    return errors, warnings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate an AI-work co-work environment skeleton."
    )
    parser.add_argument(
        "ai_work",
        type=Path,
        help="Path to the AI-work directory at the project root",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    args = parser.parse_args(argv)

    errors, warnings = validate(args.ai_work)

    for w in warnings:
        print(f"WARN: {w}")

    if errors:
        print(f"FAIL: {args.ai_work}")
        for e in errors:
            print(f"  - {e}")
        return 1

    if args.strict and warnings:
        print(f"FAIL (strict): {args.ai_work}")
        return 1

    print(f"PASS: {args.ai_work}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
