---
name: fpga-cowork
description: Read, prepare, annotate, and co-develop FPGA/RTL projects safely. Use when Codex needs to take over or inspect a Vivado/Quartus project, establish an `AI-work/` collaboration foundation, map and deep-read its main data paths, close-read or annotate RTL, document project-specific simulation behavior, or deliver a feature through RTL, verification, build, and board-debug evidence. Triggers include "读这个工程" "接手这个项目" "精读" "细读" "读某条通路" "注释这个文件" "搭建协作环境" "搭一下 AI-work" "准备闭环" "协作环境" "跑通这个工程" "开发新功能" "加一条通路" "实现这个功能" "做仿真复现" "整理交付" "上板验证" "ILA 调试".
---

# FPGA Co-work

Use this skill as a controlled collaboration workflow. It has **three user-facing modes**. The first mode is the common foundation for a new FPGA project; do not treat an existing but partial `AI-work/` directory as proof that the foundation is ready.

## Mode routing

| Mode | Use when | Required outcome | Read first |
|---|---|---|---|
| **Mode 1 — 工程接手与协作基础** | Taking over, reading, preparing, or repairing an FPGA project / `AI-work/`; request mentions project map, data paths, environment, closed loop, simulation, synthesis, bitstream, or ILA readiness. | A trusted, resumable foundation: project map, deep-reading notes for every identified main business data path, project-specific environment/SOP, baseline evidence, capability inventory, and readiness state. | `references/ai-work-bootstrap.md`, `references/reading-workflow.md`, `references/data-path-deep-reading.md`, `references/foundation-setup.md`, `references/simulation-environment.md`, `references/output-format.md` |
| **Mode 2 — 单文件阅读与注释** | User names a source file and asks to explain, read closely, annotate, comment, or compare it. | A source-preserving annotation plus its transitive instantiated user-RTL closure and an annotation manifest. | `references/single-file-close-reading.md` |
| **Mode 3 — 功能开发与板级调试** | User asks to add/change/fix/verify a concrete feature, synthesize, implement, generate a bitstream, debug board behavior, or hand off a change. | One staged unit under `AI-work/features/<feature>/<UNIT>/`, with requirements through as-built evidence. | `references/feature-development.md` |

Mode 1 repairs the road; Mode 3 drives on it. Mode 2 is a source-reading operation, not a shortcut around Mode 3 implementation controls.

## Global custody rule

All files created by AI belong under the project-root `AI-work/` tree. This includes scripts, testbenches, logs, journals, simulator outputs, reports, waveforms, CSV/VCD/WDB, bit/LTX copies, ILA captures, and generated documentation. The sole exception is an **explicitly authorized Mode 3 change** to an existing design source, constraint, IP, or project file in its original engineering location.

Do not create an AI artifact in the project root, a drive root, a temporary directory, or a tool default directory. Give every Vivado and simulator command an explicit `AI-work/` unit-local working directory, log, journal, and export path. If a tool nevertheless spills a newly created artifact elsewhere, archive it into the current `AI-work/` unit and record the source path and cause; do not delete or move pre-existing user artifacts.

Append one line to `AI-work/LOG.md` for every meaningful state transition and record unresolved facts in `AI-work/OPEN-QUESTIONS.md`.

## Mode 1 — 工程接手与协作基础

### Trigger and idempotence

Enter or repair Mode 1 when `AI-work/` is missing, incomplete, internally contradictory, stale relative to RTL/XDC/IP/tool/board changes, or lacks evidence for the requested baseline capability. A directory alone is not completion. Inspect `env/SETUP_STATUS.md` and its manifest first, then run only the invalidated stages.

Mode 1 creates a baseline that makes later cooperation safe. It is **not** feature development:

- Do not modify RTL, XDC, IP, block designs, project settings, or user build runs.
- Do not add ILA probes or generate a debug image.
- Do not write business registers, start a scan, or operate the user's instrument.
- Physical programming, JTAG connection, and a non-invasive existing-ILA inventory are optional and require explicit user authorization for that session. Tcl programming is permitted only after that authorization and must not trigger product behavior.

### Required foundation outputs

```text
AI-work/
  guide/FPGA_PROJECT_GUIDE.md
  guide/data-paths/<DL*>_DEEP_READ.md
  env/ENVIRONMENT.md
  env/HARDWARE.md
  env/SIMULATION.md                 # canonical SOP or a clear pointer to guide/VIVADO_SIM_SOP.md
  env/DEBUG_CAPABILITY.md
  env/SETUP_STATUS.md
  env/RULES.md
  env/SNAPSHOTS.md
  env/GLOSSARY.md
  scripts/
  reports/baseline/<baseline-id>/
```

The setup state records target profile (project/top/part/XDC/board/runs/bit/LTX), source/build fingerprint, exact commands, timestamps, log locations, result, failure cause, next action, and evidence links. Use explicit statuses such as `DISCOVERED`, `BASELINE_PROTECTED`, `TOOL_CHECKED`, `SIM_READY`/`SIM_BLOCKED`, `BUILD_READY`/`BUILD_BLOCKED`, `DEBUG_READY`/`DEBUG_UNAVAILABLE`, `BOARD_READY`/`READY_NO_BOARD`, `RULES_CONFIRMED`, and `READY`.

### Baseline closed loop

Run a minimal, project-specific baseline through **simulation smoke → synthesis → implementation → bitstream**, whenever the project/tool/license allows it. This proves the workflow only; it is not a functional regression or timing sign-off. Record each unavailable stage as `BLOCKED` with evidence instead of pretending it passed.

Protect the baseline before running anything: capture Git revision and dirty state, or source/XDC/IP hashes if Git is unavailable. Never run `git init`, `git add`, `git commit`, `git reset --hard`, overwrite `synth_1`/`impl_1`, or silently reuse a dirty user run. Use a separate AI-owned baseline run/output directory. If Vivado cannot isolate generated outputs in `AI-work/`, stop with `BUILD_ISOLATION_BLOCKED` rather than spilling output into the project or a drive root.

For simulation, record the actually verified project-specific command path, including known failed paths and their evidence. Do not generalize a workaround across projects or mutate the Vivado installation without explicit authorization and a restoration plan. See `references/simulation-environment.md`.

Inventory existing debug capability without changing it: qualified bit/LTX identity, ILA/VIO core names, clocks, depth, probes, expected JTAG target, and observed availability. Existing ILA cannot prove a missing measurement; record that gap for Mode 3.

### Mode 1 gate

Before Mode 3 begins, `SETUP_STATUS.md` and the baseline manifest must show:

- Project root, `.xpr`/top/part/constraints, source and build provenance, and dirty-baseline handling are recorded.
- `FPGA_PROJECT_GUIDE.md` and a deep-read guide exist for each identified main business data path, or the excluded path is justified.
- Simulation SOP identifies one canonical entry point and separates known-good, blocked, and unverified flows.
- Tool/IP/constraint inspection is evidence-backed; warning-level IP repository or license uncertainty is `DEGRADED`, never a clean pass.
- Every baseline stage is `PASS`, `BLOCKED`, or intentionally `NOT_RUN`, with logs under `AI-work/reports/baseline/`.
- Existing ILA/debug capability and board availability are recorded without claiming that a board is connected when it is not.
- `RULES.md` is explicit and confirmed; `scripts/validate-ai-work.py` and `scripts/validate-foundation.py` pass at the selected strictness.

## Mode 2 — 单文件阅读与注释

First trace the selected module's directly instantiated **user RTL** modules, then recursively trace their instantiated user RTL modules until a leaf, generated/IP, primitive, or third-party boundary. Annotate this transitive closure when annotation is requested. Do not edit generated/IP/third-party sources; record their interface contract and boundary instead. If one source is instantiated multiple times, annotate it once and list every instance site.

Before each edit, detect and record its encoding and newline convention (UTF-8/BOM, GBK/GB18030, CRLF/LF). Preserve both exactly; comments must use the file's existing language/style. Verify after editing that only comment text changed: ports, module names, logic, and functional bytes must be unchanged. Write `AI-work/annotations/<scope>_ANNOTATION_MANIFEST.md` with files, dependency closure, encoding/newline checks, instances, untouched boundaries, and diff rationale.

If analysis discovers a bug or needed behavior change, record it and enter Mode 3; never silently implement the change in Mode 2.

## Mode 3 — 功能开发与板级调试

Create one unit under `AI-work/features/<feature-slug>/<UNIT>/` before modifying design files. Keep requirements, architecture, implementation, RTL review, simulation, synthesis, implementation, bitstream, ILA, board evidence, and copies of generated assets inside that unit. The Global custody rule is a completion condition, not a suggestion.

Use the complete workflow in `references/feature-development.md`: requirements → architecture → RTL → simulation → synthesis → implementation/bitstream → board evidence → as-built handoff. Before a new debug build, review every ILA probe, width, clock domain, trigger, capture depth, expected event rate, and exact claim it can support. Independent clock-domain ILAs do not establish an exact cross-domain latency; use a common observation clock or a dedicated timestamp/handshake design when that claim is required.

### Existing-image board-debug branch

Use this light Mode 3 branch only when a current unit and a qualified existing bit/LTX pair already exist. It permits parameter application/readback, ILA/VIO capture, scope correlation, and diagnosis. It does not permit RTL/XDC/IP/project edits, new debug probes, simulation, implementation, or bitstream generation. Record bit/LTX identity, parameter manifest, capture plan, evidence, and conclusion in the existing unit. Missing probes or a changed image return to the complete Mode 3 workflow.

## Reference routing and discipline

- Bootstrap or repair: `references/ai-work-bootstrap.md`.
- Whole project map: `references/reading-workflow.md`, then `references/output-format.md`.
- Main data-path deep read: `references/data-path-deep-reading.md`; use `examples/dac-output-data-path-deep-reading.md` as the format example.
- Foundation: `references/foundation-setup.md`, then `references/simulation-environment.md`.
- Single-file closure annotation: `references/single-file-close-reading.md`.
- Feature work and board debug: `references/feature-development.md`; copy `assets/feature-work-package/` into the unit rather than editing the assets in place.

Never claim a check passed without command output or board evidence. Never expose credentials, license keys, or private network data in `AI-work/`. Do not overwrite or delete user work; stop and request direction if separation is impossible.
