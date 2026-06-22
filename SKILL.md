---
name: fpga-cowork
description: Read, map, annotate, prepare, and co-develop FPGA/RTL projects. Use when Codex needs to inspect Vivado/Quartus projects, identify top modules and main business data links, create an FPGA_PROJECT_GUIDE, deep-read one selected data path, close-read or annotate one RTL/source file, set up an `AI-work/` collaboration environment, document project-specific Vivado simulation constraints, or develop a new FPGA feature through requirements, architecture, RTL, simulation, synthesis/implementation/bitstream, ILA/board-debug evidence, and as-built handoff. Triggers include "读这个工程""接手这个项目""精读""细读""读某条通路""注释这个文件""搭建协作环境""搭一下 AI-work""准备闭环""协作环境""跑通这个工程""开发新功能""加一条通路""实现这个功能""做仿真复现""整理交付""上板验证""ILA 调试"。
---

# FPGA Cowork

Use this skill to make an unfamiliar FPGA project understandable and safe to collaborate on. The core rule is:

**Find the real business data links first. Keep stable facts in `guide/`. Keep new-feature process, evidence, logs, scripts, and debug history in `features/`.**

## Operating Modes

| Mode | When to use | Default output | Required references |
|---|---|---|---|
| Mode 1 - Whole-project map | User asks to read or take over an unfamiliar FPGA project, identify top modules, classify data links, or create a guide. | `AI-work/guide/FPGA_PROJECT_GUIDE.md` organized by real data links. | `references/reading-workflow.md`, `references/output-format.md` |
| Mode 2 - Selected-path deep read | User asks to deep-read/精读/细读 one named data link. | Path-specific code-reading guide under `AI-work/guide/data-paths/`. | `references/data-path-deep-reading.md`, `examples/dac-output-data-path-deep-reading.md` |
| Mode 3 - Single-file close read / annotation | User names one RTL/source file and asks to read, explain, annotate, comment, or compare it. | Source-file comments when requested, plus a pointer/diff record in `AI-work/annotations/`. | `references/single-file-close-reading.md` |
| Mode 4 - Co-work environment setup | User asks to set up `AI-work`, prepare safe closed-loop sim/synth, "跑通环境", or document toolchain constraints. | `AI-work/env/*.md`, project-level simulation SOP, scripts under `AI-work/scripts/`, successful environment check, confirmed `RULES.md`. | `references/cowork-environment-setup.md`, `references/simulation-environment.md` |
| Mode 5 - Feature development | User asks to implement, change, verify, synthesize, board-debug, or hand off a concrete feature. | One staged work package under `AI-work/features/<feature-slug>/<UNIT>/`: `REQUIREMENTS.md`, `ARCHITECTURE.md`, `IMPLEMENTATION.md`, `sim/SIM_REPLAY.md`, evidence under `out/`, and as-built guide update when verified. | `references/feature-development.md` |

Mode 4 repairs the road. Mode 5 drives on it. Do not begin RTL edits, IP changes, simulation iterations, synthesis, implementation, bitstream, or board-debug automation until Mode 4 is complete, `RULES.md` is confirmed, and the work is tracked by a Mode 5 unit.

## Stage 0: AI-work Bootstrap

Every mode starts by ensuring `AI-work/` exists at the project root. If it is missing or incomplete, create or repair the skeleton from `references/ai-work-bootstrap.md`.

Minimal skeleton:

```text
AI-work/
├── README.md
├── LOG.md
├── OPEN-QUESTIONS.md
├── .gitignore
├── guide/
│   ├── data-paths/
│   └── diagrams/
├── annotations/
├── env/
├── features/
├── scripts/
├── sim/
├── sim_out/
└── reports/
```

Append one line to `AI-work/LOG.md` for every skill invocation or meaningful state transition. Add unresolved facts to `OPEN-QUESTIONS.md`.

## Default Flow

When the user hands over a new project without specifying a mode:

1. Stage 0 - bootstrap `AI-work/`.
2. Mode 1 - create the whole-project map. Stop and ask whether to deep-read one main path.
3. Mode 2 - deep-read the selected/highest-throughput main path. Stop and ask whether to set up the co-work environment.
4. Mode 4 - set up environment, simulation SOP, scripts, rollback, and `RULES.md`; wait for explicit user confirmation.
5. Mode 5 - only after an explicit feature/change request.
6. Mode 3 - only when the user names a file for close reading or annotation.

Do not silently chain past a stage boundary without explicit user intent such as "继续".

## Cross-Mode Boundaries

- `guide/` stores stable facts: whole-project maps, deep-reading guides, as-built data-link facts, diagrams.
- `features/` stores process: requirements, architecture alternatives, implementation progress, tests, logs, scripts, synth/impl/bitstream/ILA evidence.
- `env/` stores project-level collaboration facts: toolchain, hardware, rules, rollback, focus, glossary, simulation SOP.
- `annotations/` stores single-file reading/commenting records. If a later feature changes that file, the feature package must note whether the annotation became stale.

Do not use one document as both a plan and a verified fact record.

## Quick Workflow

1. **Boundary before internals.** Locate project files, top module, top ports, constraints, BD/IP, and source roots before reading `always` blocks.
2. **Question ledger first.** Convert unknowns into narrow searches using `rg -n -C 3` to `-C 10`; record evidence paths, line numbers, confidence, and residual risk.
3. **Identify main data links by semantics.** Ethernet, DDR, PCIe, SFP, and QSPI may be support or main links; decide from business data, throughput, endpoints, and module contracts.
4. **Tie clocks/control/storage to links.** Explain clocks, resets, CDC, FIFOs, DDR, control registers, and debug resources in relation to the data link they constrain.
5. **Use the right output shape.** Whole-project guide, selected-path reading guide, single-file annotation, environment setup, and feature work package are different deliverables.
6. **Keep runtime artifacts contained.** New `vivado*.log`, `.jou`, `xsim.dir`, `xvlog.pb`, `.wdb`, CSV, reports, bitstream logs, and `hw_ila_data_*` belong in the current `AI-work/` location, not D: root or the project root.

## Mode-Specific Gate Summary

### Mode 1 Gate

- Main data links are identified by business semantics.
- Tables from `references/output-format.md` are present.
- Generated or runtime files are treated as evidence stores, not source.
- Feature/package index points to active `AI-work/features/*` units if they exist.
- All unsupported inferences are marked `> ⚠️ 待确认` and copied to `OPEN-QUESTIONS.md`.

### Mode 2 Gate

A selected-path deep read is not acceptable as a plain summary. Each major "open this file" pass must include:

```text
本步目标
搜索入口
本模块相关信号
先忽略
代码阅读顺序
读完应能回答
下一步
```

Run `scripts/validate-deep-reading-guide.py` when available. Mode 2 can propose sim/ILA signal groups, but execution and evidence belong to Mode 5.

### Mode 3 Gate

- Identify upstream producer, downstream consumer, role in the business link, data model, dimensions, packing units, and valid/enable contract before commenting.
- Add teaching comments at section boundaries and non-obvious contracts, not line-by-line syntax.
- Do not change functional RTL unless the user explicitly asks for a fix; switch to Mode 5 for fixes.
- Record the file, rationale, and version/diff note in `AI-work/annotations/`.

### Mode 4 Gate

Before declaring environment setup complete:

- `ENVIRONMENT.md`, `HARDWARE.md`, `RULES.md`, `FOCUS.md`, `SNAPSHOTS.md`, `GLOSSARY.md`, and `SIMULATION.md` (or an explicitly linked project-level `VIVADO_SIM_SOP.md`) exist and contain real project facts.
- Baseline and rollback command are recorded; rollback is drilled once.
- Scripts are generated/customized under `AI-work/scripts/`.
- `check_env.tcl` is run once or the blocker is explicitly documented.
- Project-level simulation SOP states which batch/GUI paths work, which fail, and why.
- User explicitly confirms `RULES.md`; log the confirmation.
- Run `scripts/validate-ai-work.py` and `scripts/validate-simulation-sop.py` when available.

### Mode 5 Gate

A feature unit is not acceptable if it only says "done" or "PASS". The unit must track the feature through stages:

```text
<UNIT>/
├── REQUIREMENTS.md
├── ARCHITECTURE.md
├── IMPLEMENTATION.md
├── RTL_REVIEW.md              # required for broad/multi-file changes
├── sim/
│   ├── SIM_REPLAY.md
│   ├── run_manual.tcl
│   └── run_gui.tcl
├── synth/                     # if synthesis is part of this unit
├── impl/                      # if implementation/bitstream is part of this unit
├── ila/                       # if board/ILA debug is part of this unit
└── out/
    ├── sim/
    ├── regression/
    ├── synth/
    ├── impl/
    ├── bitstream/
    ├── ila/
    └── hw_debug/
```

Required stage checks:

- Requirements are confirmed before RTL work begins.
- Architecture explains data path, trigger/control path, CDC, FIFO/storage, old-behavior preservation, constraints, and verification strategy.
- Implementation records changed modules, status, errors, fixes, commands, and evidence paths.
- Simulation replay gives concrete GUI/batch commands, testbench/top, TC explanations, key waveform signals, pass/fail criteria, and generated logs/results.
- Synth/impl/bitstream/ILA evidence is stored under `out/` when performed.
- ILA/board-debug scripts live in the current unit `ila/`; captures and exports go directly to `out/ila/` or `out/hw_debug/`.
- Before any Vivado Hardware Manager or ILA command (`open_hw_manager`, `refresh_hw_device`, `run_hw_ila`, `upload_hw_ila_data`, `display_hw_ila_data`, `write_hw_ila_data`), the Tcl script must resolve the project root from `[info script]`, create a unit-local work directory such as `out/ila/vivado_hw_work` or `out/hw_debug/vivado_hw_work`, `cd` into it, and print that directory in the log. Also snapshot `D:/hw_ila_data_*` before the run and archive any newly-created D-root spill directories into the current unit. Vivado 2021.1 Hardware Manager can create `hw_ila_data_*` placeholders under `D:\` during refresh/upload/display even when final CSV/VCD paths are absolute. When the project provides a guarded Vivado launcher such as `AI-work/scripts/run_vivado_ila_guarded.ps1`, use that launcher instead of calling `vivado.bat -mode batch -source ...` directly.
- Runtime artifacts are not left scattered in D: root or the project root.
- Verified facts are copied/summarized into `guide/data-paths/*_AS_BUILT.md`; plans and failed attempts stay in `features/`.
- Run `scripts/validate-feature-work-package.py` and `scripts/scan-artifact-spill.py` when available.

## References

- Read `references/ai-work-bootstrap.md` when bootstrapping or repairing `AI-work/`.
- Read `references/reading-workflow.md` for Mode 1.
- Read `references/output-format.md` for `FPGA_PROJECT_GUIDE.md`.
- Read `references/data-path-deep-reading.md` for Mode 2.
- Read `references/single-file-close-reading.md` for Mode 3.
- Read `references/cowork-environment-setup.md` and `references/simulation-environment.md` for Mode 4.
- Read `references/feature-development.md` for Mode 5.
- Read `references/diagram-guidelines.md` before creating or replacing diagrams.
- Use `examples/dac-output-data-path-deep-reading.md` as the canonical Mode 2 code-reading guide example.
- Use `assets/feature-work-package/` as the Mode 5 template source; copy templates into a unit and customize them. Do not edit assets in place.
- Use `scripts/templates/*.tcl` as project-level Tcl template sources; copy and customize per project or unit.

## Discipline

- Do not modify RTL during Mode 1/2/3 reading unless the user explicitly asks for a fix, in which case switch to Mode 5.
- Do not bulk-read generated Vivado/Quartus files. Query exact evidence windows.
- Prefer source files, constraints, BD/IP metadata, and project scripts before generated netlists, cache XML, run outputs, or simulator libraries.
- Do not scatter Markdown guides, diagrams, scripts, logs, reports, or ILA data outside `AI-work/`.
- Do not claim simulation/synthesis/board verification is complete unless evidence is stored and the user can reproduce or review it from the unit package.
- Mark unsupported inferences as `> ⚠️ 待确认` and copy them into `OPEN-QUESTIONS.md`.
