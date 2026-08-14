#!/usr/bin/env python3
"""Self-test the Mode 4 validators with template, ready, and rejection cases."""

from __future__ import annotations

import hashlib
import importlib.util
import shutil
import tempfile
from pathlib import Path
from types import ModuleType


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent


def load_script(name: str, module_name: str) -> ModuleType:
    path = SCRIPT_DIR / name
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def build_ready_fixture(root: Path) -> tuple[Path, Path]:
    unit = root / "AI-work" / "bringup" / "test-board" / "BRINGUP_001"
    design = root / "fpga"
    shutil.copytree(SKILL_DIR / "assets" / "new-board-work-package", unit)
    demo = unit / "demos" / "uart_loopback" / "UART_DEMO_001"
    shutil.copytree(SKILL_DIR / "assets" / "demo-work-package", demo)
    (design / "product").mkdir(parents=True)
    write(design / "common" / "uart" / "uart_core.v", "module uart_core; endmodule")

    write(unit / "STATUS.md", """
# New-board bring-up status
- State: `MODE3_READY`
- Board: `test-board`
- Board revision: `A`
- Bring-up unit: `BRINGUP_001`
- Authorized design root: `fpga`
- Product project: `product`
- Product top / part: `product_top` / `xc7a100tfgg484-2`
- Tool/version: `Vivado 2021.1`
- Current authority: this file
## Current conclusion
UART is board-qualified and the product baseline is ready.
""")
    write(unit / "SOURCE_REGISTER.md", """
# Source register
| ID | Source | Origin/owner | Revision/date | SHA-256 | Role | Confidence/status |
|---|---|---|---|---|---|---|
| SRC-001 | schematic.pdf | user | A | N/A | Board contract | CONFIRMED |
""")
    write(unit / "BOARD_CONTRACT.md", """
# Board contract
Board A uses xc7a100tfgg484-2 and the reviewed UART board constraints.
""")
    write(unit / "INTERFACE_MATRIX.md", """
# Interface matrix
| Interface | Purpose | Required | Contract state | Minimum demo | Acceptance evidence | Current state |
|---|---|---:|---|---|---|---|
| UART | Control | YES | CONFIRMED | uart_loopback | Echo with zero errors | BOARD_PASS |
""")
    write(unit / "BRINGUP_PLAN.md", """
# Bring-up plan
Build and board-test UART, promote the core, then build the product baseline.
""")
    write(unit / "ACCEPTANCE_MATRIX.md", """
# Interface acceptance matrix
| Interface | Required | Demo unit | Contract | Build | Ready for board | Board result | Waiver | Release/evidence |
|---|---:|---|---|---|---|---|---|---|
| UART | YES | uart_loopback/UART_DEMO_001 | CONFIRMED | BUILD_PASS | YES | BOARD_PASS | NONE | demos/uart_loopback/UART_DEMO_001/out/board-test/result.txt |
""")
    write(unit / "DEMO_DEPENDENCY_MATRIX.md", """
# Demo dependency matrix
| Canonical source/configuration | Asset class | Demo consumers | Product consumers | Change invalidates | Latest qualified identity |
|---|---|---|---|---|---|
| common/uart/uart_core.v | REUSABLE_CORE | uart_loopback | product | UART demo and product | rev-a |
""")
    write(unit / "MODE3_HANDOFF.md", """
# Mode 3 handoff
- State: `MODE3_READY`
- Official design root: `fpga`
- Product project: `product`
- Product top / part: `product_top` / `xc7a100tfgg484-2`
- Canonical build entry: `scripts/build_product.tcl`
- Canonical simulation entry: `NOT_APPLICABLE`
- Tool/IP versions: `Vivado 2021.1`
- Source identity: `rev-a`
- Board contract identity: `board-a`
- Acceptance matrix identity: `accept-a`
- Qualified release: `release/bitstream/product.bit`
""")

    image = unit / "release" / "bitstream" / "product.bit"
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes(b"qualified-product-image")
    digest = hashlib.sha256(image.read_bytes()).hexdigest().upper()
    write(unit / "release" / "RELEASE_MANIFEST.md", f"""
# Release manifest
| Artifact | SHA-256 | Part/top | Tool/IP | Source identity | Board/constraint revision | Intended behavior | Build state | Board state | Applicable hardware | Limitations |
|---|---|---|---|---|---|---|---|---|---|---|
| release/bitstream/product.bit | {digest} | xc7a100tfgg484-2/product_top | Vivado 2021.1 | rev-a | A | Product baseline | BUILD_PASS | BOARD_PASS | test-board A | Feature stub |
""")

    write(demo / "REQUIREMENTS.md", """
# Demo requirements
UART loopback must echo data with zero errors on test-board A.
""")
    write(demo / "ARCHITECTURE.md", """
# Demo architecture
The demo wraps the canonical UART core with a test-only echo top.
""")
    write(demo / "REUSE_MANIFEST.md", """
# Demo reuse manifest
| Artifact/source | Class | Canonical official path | Promoted identity | Product consumer | Demo evidence | Notes |
|---|---|---|---|---|---|---|
| uart_core.v | REUSABLE_CORE | common/uart/uart_core.v | rev-a | product | out/board-test/result.txt | canonical source |
| echo_top.v | TEST_ONLY | N/A | rev-a | NONE | out/board-test/result.txt | demo only |
""")
    write(demo / "STATUS.md", f"""
# Demo status
- State: `BOARD_PASS`
- Demo: `uart_loopback`
- Interface: `UART`
- Official source path: `demos/uart_loopback`
- Top / part: `uart_echo_top` / `xc7a100tfgg484-2`
- Tool/version: `Vivado 2021.1`
- Candidate image: `out/bitstream/candidate/uart.bit {digest}`
- Qualified image: `release/bitstream/uart.bit {digest}`
## Stage evidence
Build and board evidence are recorded below.
""")
    write(demo / "out" / "synth" / "result.txt", "BUILD_PASS")
    write(demo / "out" / "board-test" / "result.txt", "BOARD_PASS zero errors")
    return unit, design


def main() -> int:
    common_validator = load_script("validate-ai-work.py", "common_validator_test")
    demo_validator = load_script("validate-demo-work-package.py", "demo_validator_test")
    board_validator = load_script("validate-new-board-work-package.py", "board_validator_test")

    template_demo_errors, _, _ = demo_validator.validate(SKILL_DIR / "assets" / "demo-work-package")
    template_board_errors, _, _ = board_validator.validate(SKILL_DIR / "assets" / "new-board-work-package")
    if template_demo_errors or template_board_errors:
        raise AssertionError(f"template validation failed: {template_demo_errors} {template_board_errors}")

    with tempfile.TemporaryDirectory(prefix="fpga-cowork-mode4-") as temp:
        temp_root = Path(temp)
        ai_work = temp_root / "AI-work"
        for relative in ("guide", "annotations", "env", "features", "bringup", "scripts", "reports"):
            (ai_work / relative).mkdir(parents=True, exist_ok=True)
        write(ai_work / "README.md", "# AI collaboration workspace")
        write(ai_work / "LOG.md", "# Log\n- 2026-01-01: Initialized.")
        write(ai_work / "OPEN-QUESTIONS.md", "# Open questions\n| ID | Question |\n|---|---|\n| Q1 | None |")
        write(ai_work / ".gitignore", "*.log")
        common_errors, _ = common_validator.validate(ai_work)
        if common_errors:
            raise AssertionError(f"common skeleton validation failed: {common_errors}")

        unit, design = build_ready_fixture(temp_root)
        errors, warnings, state = board_validator.validate(unit, design, temp_root)
        if errors or warnings or state != "MODE3_READY":
            raise AssertionError(f"ready fixture failed: state={state} errors={errors} warnings={warnings}")

        dependency = unit / "DEMO_DEPENDENCY_MATRIX.md"
        dependency.write_text(
            dependency.read_text(encoding="utf-8").replace("REUSABLE_CORE", "TEST_ONLY"),
            encoding="utf-8",
        )
        errors, _, _ = board_validator.validate(unit, design, temp_root)
        if not any("TEST_ONLY" in error and "product consumer" in error for error in errors):
            raise AssertionError(f"forbidden product-consumer case was not rejected: {errors}")

    print("PASS: Mode 4 validator self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
