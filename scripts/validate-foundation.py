#!/usr/bin/env python3
"""Validate evidence structure for fpga-cowork Mode 1 foundations.

This is deliberately stricter than a Markdown keyword check. It validates the
latest baseline manifest and whether referenced evidence remains inside
AI-work. It does not replace reading Vivado logs or a functional regression.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_DIRS = ("guide", "guide/data-paths", "env", "scripts", "reports/baseline")
REQUIRED_DOCS = (
    "guide/FPGA_PROJECT_GUIDE.md",
    "env/ENVIRONMENT.md",
    "env/HARDWARE.md",
    "env/DEBUG_CAPABILITY.md",
    "env/SETUP_STATUS.md",
    "env/RULES.md",
    "env/SNAPSHOTS.md",
    "env/GLOSSARY.md",
)
REQUIRED_STAGES = ("simulation", "synthesis", "implementation", "bitstream")
VALID_STAGE_STATUS = {"PASS", "BLOCKED", "NOT_RUN"}


def inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def latest_manifest(ai_work: Path) -> Path | None:
    manifests = sorted(
        (ai_work / "reports" / "baseline").glob("*/foundation_manifest.json"),
        key=lambda p: (p.stat().st_mtime, p.as_posix()),
    )
    return manifests[-1] if manifests else None


def validate(ai_work: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not ai_work.is_dir():
        return [f"AI-work directory not found: {ai_work}"], warnings

    for item in REQUIRED_DIRS:
        if not (ai_work / item).is_dir():
            errors.append(f"missing directory: AI-work/{item}")
    for item in REQUIRED_DOCS:
        path = ai_work / item
        if not path.is_file() or not path.read_text(encoding="utf-8", errors="replace").strip():
            errors.append(f"missing or empty foundation document: AI-work/{item}")

    sim_env = ai_work / "env" / "SIMULATION.md"
    sim_guide = ai_work / "guide" / "VIVADO_SIM_SOP.md"
    if not sim_env.is_file() and not sim_guide.is_file():
        errors.append("missing canonical simulation SOP: env/SIMULATION.md or guide/VIVADO_SIM_SOP.md")

    deep_reads = list((ai_work / "guide" / "data-paths").glob("*_DEEP_READ.md"))
    if not deep_reads:
        warnings.append("no *_DEEP_READ.md found; record excluded main paths if none exist")

    manifest_path = latest_manifest(ai_work)
    if manifest_path is None:
        errors.append("no reports/baseline/<baseline-id>/foundation_manifest.json")
        return errors, warnings

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return errors + [f"invalid foundation manifest {manifest_path}: {exc}"], warnings

    for field in ("baseline_id", "target_profile", "baseline_protection", "stages"):
        if not manifest.get(field):
            errors.append(f"manifest missing required field: {field}")

    target = manifest.get("target_profile", {})
    for field in ("project", "top", "part"):
        if not target.get(field):
            errors.append(f"manifest target_profile missing: {field}")

    protection = manifest.get("baseline_protection", {})
    if not any(protection.get(key) for key in ("git_head", "source_hashes")):
        errors.append("manifest baseline_protection needs git_head or source_hashes")
    if protection.get("state") not in {"CLEAN_BASELINE", "DIRTY_BASELINE"}:
        errors.append("manifest baseline_protection.state must be CLEAN_BASELINE or DIRTY_BASELINE")

    stages = manifest.get("stages", {})
    for name in REQUIRED_STAGES:
        stage = stages.get(name)
        if not isinstance(stage, dict):
            errors.append(f"manifest missing stage: {name}")
            continue
        status = stage.get("status")
        if status not in VALID_STAGE_STATUS:
            errors.append(f"stage {name} has invalid status: {status!r}")
        for field in ("command", "work_dir", "log", "next_action"):
            if field not in stage:
                errors.append(f"stage {name} missing field: {field}")
        for field in ("work_dir", "log"):
            raw = stage.get(field)
            if raw:
                path = Path(raw)
                if not path.is_absolute():
                    path = ai_work / path
                if not inside(path, ai_work):
                    errors.append(f"stage {name} {field} escapes AI-work: {raw}")
                elif status == "PASS" and not path.exists():
                    errors.append(f"stage {name} PASS but {field} does not exist: {raw}")
        if status == "BLOCKED" and not stage.get("blocker"):
            errors.append(f"stage {name} BLOCKED without blocker")

    overall = manifest.get("overall_status")
    if overall == "READY" and any(stages.get(n, {}).get("status") != "PASS" for n in REQUIRED_STAGES):
        errors.append("overall READY requires all baseline stages PASS")
    if overall not in {"READY", "READY_NO_BOARD", "BUILD_BLOCKED", "SIM_BLOCKED", "IN_PROGRESS"}:
        warnings.append(f"unrecognized overall_status: {overall!r}")

    return errors, warnings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate Mode 1 foundation evidence.")
    parser.add_argument("ai_work", type=Path)
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
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
