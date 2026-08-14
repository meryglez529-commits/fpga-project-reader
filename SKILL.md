---
name: fpga-cowork
description: Read, prepare, annotate, and co-develop FPGA/RTL projects safely, including new-board development from schematics and interface planning through reusable bring-up demos and a Mode-3-ready product baseline. Use when Codex needs to take over or inspect a Vivado/Quartus project, establish an `AI-work/` collaboration foundation, map and deep-read data paths, close-read or annotate RTL, develop a concrete feature, or bring up a new board from zero to one. Triggers include "读这个工程" "接手这个项目" "精读" "细读" "读某条通路" "注释这个文件" "搭建协作环境" "准备闭环" "跑通这个工程" "开发新功能" "做仿真复现" "整理交付" "上板验证" "ILA 调试" "新板卡开发" "从原理图开始" "从0到1" "最小demo" "接口bring-up".
---

# FPGA Co-work

Use this skill as a controlled collaboration workflow. It has **four user-facing modes**. Mode numbers route request types; they are not lifecycle step numbers. Mode 1 takes over an existing engineering project, while Mode 4 creates a new-board baseline from schematics and interface requirements.

## Mode routing

| Mode | Use when | Required outcome | Read first |
|---|---|---|---|
| **Mode 1 — 工程接手与协作基础** | Taking over, reading, preparing, or repairing an FPGA project / `AI-work/`; request mentions project map, data paths, environment, closed loop, simulation, synthesis, bitstream, or ILA readiness. | A trusted, resumable foundation: project map, deep-reading notes for every identified main business data path, project-specific environment/SOP, baseline evidence, capability inventory, and readiness state. | `references/ai-work-bootstrap.md`, `references/reading-workflow.md`, `references/data-path-deep-reading.md`, `references/foundation-setup.md`, `references/simulation-environment.md`, `references/output-format.md` |
| **Mode 2 — 单文件精读 / 注释** | User names a source file and asks to explain, read closely, annotate, comment, or compare it. | **Read-only request** (`解释` / `精读` / `比较`): evidence-backed explanation only; do not edit RTL. **Explicit annotation request** (`注释` / `添加注释` / `用 Mode 2 注释`): source-preserving comments for the selected source **and its full transitive active user-RTL instantiation closure**, plus an annotation manifest. | `references/single-file-close-reading.md` |
| **Mode 3 — 功能开发与板级调试** | User asks to add/change/fix/verify a concrete feature, synthesize, implement, generate a bitstream, debug board behavior, or hand off a change. | One staged unit under `AI-work/features/<feature>/<UNIT>/`, with requirements through as-built evidence. | `references/feature-development.md` |
| **Mode 4 — 新板卡开发与接口 Bring-up** | User has a new/planned board, schematics or interface requirements, and needs FPGA work from interface contract through minimum demos and a product baseline. | An official FPGA source tree plus one board bring-up unit containing interface contracts, required demos, acceptance/reuse/dependency evidence, a buildable product baseline, and a validated Mode 3 handoff. | `references/new-board-development.md`, `references/ai-work-bootstrap.md` |

Mode 1 repairs an existing road; Mode 4 builds the first road for a new board; Mode 3 drives feature work on either trusted baseline. Mode 2 is a source-reading operation, not a shortcut around Mode 3 implementation controls.

### Mode 2 request boundary (mandatory)

Classify the request before opening source files:

- **Read-only close reading**: Requests to explain, inspect, deep-read, or compare RTL do **not** authorize source edits. Trace only the hierarchy needed to support the explanation, identify active versus commented-out instances, and state the evidence boundary. Do not create an annotation manifest or claim annotation closure.
- **Explicit annotation**: Requests containing `注释`, `添加注释`, `comment the module`, or `用 Mode 2 注释` authorize comment-only edits. Resolve the selected module's full transitive **active user-RTL** instantiation closure before the first edit. Annotate every editable closure member exactly once; record IP, primitive, generated, encrypted, third-party, missing, ambiguous, and commented-out boundaries in one manifest. Annotating only the root is incomplete.

If the wording is ambiguous, ask whether the user wants read-only explanation or full closure annotation. Never infer annotation authority from a request to explain a file.

## Global custody rule

Use a dual-root model. Keep official engineering sources in the user-confirmed design root and keep AI collaboration/evidence in project-root `AI-work/`:

- Mode 4 may create official RTL, constraints, IP configuration, simulation sources, and project/build Tcl only after recording the authorized design root in `AI-work/env/RULES.md` and the bring-up status. Mode 3 may modify authorized official sources. Mode 1 remains read-only; Mode 2 edits comments only when explicitly requested.
- Put all AI analysis, manifests, scripts that orchestrate evidence, logs, journals, simulator outputs, reports, waveforms, CSV/VCD/WDB, build workspaces, generated projects/runs, bit/LTX evidence copies, ILA captures, and documentation under the active `AI-work/` unit.
- Treat `.Xil`, `.runs`, `.gen`, caches, and tool-generated projects as reproducible work, never as authoritative source. Prefer source-driven Tcl builds from the official design root into unit-local `work/` and `out/` paths.

Do not create an AI artifact in the project root, a drive root, a global temporary directory, or a tool default directory. Give every Vivado and simulator command an explicit `AI-work/` unit-local working directory, log, journal, and export path. If a tool nevertheless spills a newly created artifact elsewhere, archive it into the current unit and record the source path and cause; do not delete or move pre-existing user artifacts.

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

## Mode 2 — 单文件精读 / 注释

Choose one path using the mandatory request boundary above.

### Read-only close reading

Do not edit RTL. Trace the selected source and the minimum active hierarchy needed for an evidence-backed explanation; distinguish active instances from commented-out historical code and identify generated/IP/primitive/third-party boundaries when relevant. State that this is read-only and do not present it as an annotation closure.

### Explicit annotation closure

Before the first edit, trace the selected module's directly instantiated **active user RTL** modules, then recursively trace their instantiated active user RTL modules until a leaf, generated/IP, primitive, encrypted, third-party, missing, or ambiguous boundary. Annotate the full editable transitive closure; do not stop at the root. Do not edit generated/IP/third-party sources; record their interface contract and boundary instead. If one source is instantiated multiple times, annotate it once and list every instance site. Commented-out instances are historical context, not closure members.

For explicit annotation, before each edit detect and record its encoding and newline convention (UTF-8/BOM, GBK/GB18030, CRLF/LF). Preserve both exactly; comments must use the file's existing language/style. A source that can be decoded and re-encoded byte-for-byte as GB18030 is safe to annotate with GB18030, even if its historical text appears to contain mixed legacy encodings. Use GB18030 consistently for new comments in that file and retain its original BOM and line endings. Stop only when no single encoding can make a lossless byte round trip, or when the available writer cannot prove it preserves all non-comment bytes. Verify after editing that only comment text changed: ports, module names, logic, and functional bytes must be unchanged. Write `AI-work/annotations/<scope>_ANNOTATION_MANIFEST.md` with files, dependency closure, encoding/newline checks, instances, untouched boundaries, and diff rationale.

If analysis discovers a bug or needed behavior change, record it and enter Mode 3; never silently implement the change in Mode 2.

## Mode 3 — 功能开发与板级调试

Enter Mode 3 only when either Mode 1 is `READY` or a Mode 4 `MODE3_HANDOFF.md` is validated as `MODE3_READY`. Create one unit under `AI-work/features/<feature-slug>/<UNIT>/` before modifying design files. Keep requirements, architecture, implementation, RTL review, simulation, synthesis, implementation, bitstream, ILA, board evidence, and copies of generated assets inside that unit. The Global custody rule is a completion condition, not a suggestion.

Use the complete workflow in `references/feature-development.md`: requirements → architecture → RTL → simulation → synthesis → implementation/bitstream → board evidence → as-built handoff. When a Mode 4 handoff exists, read its demo dependency matrix before changing shared board constraints, clocks/resets, interface cores, or vendor configuration; mark affected demo evidence stale and rerun only the required regression scope. Never promote `TEST_ONLY`, `GENERATED`, or `OBSOLETE` demo assets into the product source tree.

### Existing-image board-debug branch

Use this light Mode 3 branch only when a current unit and a qualified existing bit/LTX pair already exist. It permits parameter application/readback, ILA/VIO capture, scope correlation, and diagnosis. It does not permit RTL/XDC/IP/project edits, new debug probes, simulation, implementation, or bitstream generation. Record bit/LTX identity, parameter manifest, capture plan, evidence, and conclusion in the existing unit. Missing probes or a changed image return to the complete Mode 3 workflow.

## Mode 4 — 新板卡开发与接口 Bring-up

Use Mode 4 for a planned or newly received board when no trusted product FPGA baseline exists. Establish the board/interface contract before creating constraints; build the required minimum demos independently; promote verified board facts and reusable interface cores into one canonical official source tree; then create a safe, buildable product baseline for Mode 3.

Create `AI-work/bringup/<board>/<BRINGUP_UNIT>/` by copying `assets/new-board-work-package/`, and create each required demo from `assets/demo-work-package/`. Follow `references/new-board-development.md`. A demo build pass and a board pass are different states. IBERT, PN checkers, traffic generators, loopback tops, and similar diagnostics remain `TEST_ONLY` unless their reusable submodule is explicitly promoted.

Normal board validation is in scope. Electrical faults in JTAG/configuration, power rails, soldering, connectors, or PCB nets are not a standard FPGA development stage: capture the first decisive evidence, set the demo to `FPGA_READY_HARDWARE_BLOCKED`, write a unit-local hardware handoff, and stop repetitive software-variable elimination.

Mode 4 completes only when required interfaces are board-qualified or explicitly waived, the product baseline builds, release artifacts are qualified and hashed, dependency/reuse mappings are synchronized, and `scripts/validate-new-board-work-package.py` reports `MODE3_READY`. Do not migrate or reorganize an existing project automatically; make migration a separately approved task.

## Reference routing and discipline

- Bootstrap or repair: `references/ai-work-bootstrap.md`.
- Whole project map: `references/reading-workflow.md`, then `references/output-format.md`.
- Main data-path deep read: `references/data-path-deep-reading.md`; use `examples/dac-output-data-path-deep-reading.md` as the format example.
- Foundation: `references/foundation-setup.md`, then `references/simulation-environment.md`.
- Single-file closure annotation: `references/single-file-close-reading.md`.
- Feature work and board debug: `references/feature-development.md`; copy `assets/feature-work-package/` into the unit rather than editing the assets in place.
- New-board development, multiple bring-up demos, product-baseline promotion, and Mode 3 handoff: `references/new-board-development.md`; copy `assets/new-board-work-package/` and `assets/demo-work-package/` rather than editing the assets in place.

Never claim a check passed without command output or board evidence. Never expose credentials, license keys, or private network data in `AI-work/`. Do not overwrite or delete user work; stop and request direction if separation is impossible.
