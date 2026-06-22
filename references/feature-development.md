# Feature Development SOP

> Mode 5 目标：围绕一个具体 FPGA 功能，从需求对齐开始，经过架构方案、RTL 实施、仿真、综合/实现/bitstream、ILA/上板辅助验证和 as-built 回写，形成一个用户可审查、可复现、可继续接手的工作包。

Use this reference when the user asks to implement, modify, debug, verify, synthesize, board-debug, or hand off a concrete FPGA feature.

## 0. Boundary

Mode 5 is not "edit RTL quickly". It is a closed-loop development unit.

Prerequisites:

| Item | Requirement |
|---|---|
| Project context | Mode 1/2 exists, or do a minimal boundary pass first |
| Environment | Mode 4 completed enough to know toolchain, rollback, rules, and simulation constraints |
| User rules | `AI-work/env/RULES.md` explicitly confirmed |
| Work tracking | One unit under `AI-work/features/<feature-slug>/<UNIT>/` |

If requirements are unclear, write questions in `REQUIREMENTS.md` and ask the user. Do not start RTL.

## 1. Work Package Layout

Default layout:

```text
AI-work/features/
  <feature-slug>/
    <UNIT>/
      REQUIREMENTS.md
      ARCHITECTURE.md
      IMPLEMENTATION.md
      RTL_REVIEW.md              # required for broad/multi-file handoff

      sim/
        SIM_REPLAY.md
        run_manual.tcl
        run_gui.tcl
        run_batch.tcl            # only if this project can support it
        waves.wcfg               # only when waveform layout is saved

      synth/
        run_synth.tcl

      impl/
        run_impl.tcl
        run_bitstream.tcl

      ila/
        program.tcl
        capture_*.tcl
        export_*.tcl

      out/
        sim/
        regression/
        synth/
        impl/
        bitstream/
        ila/
        hw_debug/

      evidence/
      diagrams/
```

Naming:

| Item | Rule |
|---|---|
| `<feature-slug>` | Short lower-case feature name, e.g. `dl5_laser_sync` |
| `<UNIT>` | Use `DL5_UNIT_002` when tied to a data link; use a clear domain prefix for non-link work |
| New major requirement/architecture direction | Create the next unit; do not rewrite history |
| Extra reports | Allowed only when they carry distinct evidence and are linked from `IMPLEMENTATION.md` |

## 2. Stage 1 - Requirements

Output: `REQUIREMENTS.md`

Answer:

- What physical/business problem is the feature solving?
- What do the user's diagrams/screenshots actually mean?
- Which signals are physical IO and which are internal concepts?
- What are parameter meanings, units, ranges, step sizes, and legal boundaries?
- What existing parameters or paths are reused?
- What is explicitly out of scope?
- Which questions are confirmed, open, or intentionally ignored?

Good requirement work looks like the `DL5_UNIT_002` pattern:

- Reconstruct the real-world timing process.
- Resolve ambiguous names such as `Scan_X_Signal`.
- Decide whether `dwell_time` reuses an existing parameter.
- Record `Q1..Qn` discussion conclusions.

Gate:

- If a requirement affects RTL behavior and is not confirmed, stop and ask.
- Do not encode a guess into RTL without marking it as an assumption.

## 3. Stage 2 - Architecture

Output: `ARCHITECTURE.md`

Answer:

- What are the data path and trigger/control path?
- Where does the new feature enter the old design?
- What old behavior must remain unchanged?
- What state-machine changes are required?
- What CDC boundaries exist, and what synchronization strategy is used?
- How do FIFOs, DDR, BRAM, IP, and backpressure affect timing?
- What constraints or formulas must the user respect?
- What simulation, synthesis, implementation, and ILA checks prove the design?

For nontrivial changes, include:

| Required topic | Notes |
|---|---|
| Data/trigger/control separation | Avoid making FIFO water level define trigger timing unless intended |
| CDC table | Signal, source clock, destination clock, method, risk |
| Old-mode preservation | State exactly what should be identical when mode is off |
| Timing/FIFO analysis | Include formulas or measured constraints |
| Verification strategy | TC groups, key waveform groups, synth/ILA checks |

Gate:

- Complex RTL changes require a reviewed architecture plan before editing.
- Architecture must describe current intended RTL, not an obsolete alternative.

## 4. Stage 3 - RTL Implementation

Output: `IMPLEMENTATION.md`; add `RTL_REVIEW.md` for broad/multi-file changes or final user handoff.

`IMPLEMENTATION.md` should track:

- Implementation order.
- Per-module status.
- Exact changed modules/files.
- Elaboration/simulation/synthesis/implementation/bitstream status.
- Error/fix history.
- Commands and evidence paths.
- Open issues and decisions.

`RTL_REVIEW.md` should answer:

| File | Why changed | What changed | User should inspect | Risk |
|---|---|---|---|---|

Rules:

- After each RTL/project/constraint script edit, update `IMPLEMENTATION.md`.
- For multi-file changes, do not write "changed several RTL files"; list each file.
- If touching `.xdc`, BD, IP `.xci`, or project metadata, confirm this is permitted by `RULES.md`.

## 5. Stage 4 - Simulation

Outputs:

```text
sim/SIM_REPLAY.md
sim/run_manual.tcl
sim/run_gui.tcl
out/sim/
out/regression/
```

`SIM_REPLAY.md` must give the user:

- Project-level SOP link, e.g. `AI-work/env/SIMULATION.md` or `AI-work/guide/VIVADO_SIM_SOP.md`.
- Testbench path and simulation top.
- What each TC verifies.
- How to run in Vivado GUI.
- How to run in batch/PowerShell when supported.
- Which signals to add to the wave window.
- What PASS/FAIL means.
- Where AI-generated logs/results/waveforms live.
- What is not covered.

Evidence rules:

- Store logs and `result.txt` under `out/sim/` or `out/regression/`.
- Store `.wdb`/`.wcfg` when practical. If unavailable, explain why.
- The unit can reuse project-level simulation quirks; do not re-explain every environment issue in every unit.
- If a new simulation trick is discovered, first record it in `IMPLEMENTATION.md`, then feed it back into the project-level simulation SOP.

Gate:

- Do not claim simulation passed unless the user can review the evidence and replay instructions.

## 6. Stage 5 - Synthesis / Implementation / Bitstream

Outputs when used:

```text
synth/run_synth.tcl
impl/run_impl.tcl
impl/run_bitstream.tcl
out/synth/
out/impl/
out/bitstream/
```

Record in `IMPLEMENTATION.md`:

- Command.
- Log/report path.
- ERROR and CRITICAL WARNING count.
- WNS/TNS or build status when relevant.
- Resource changes.
- Whether bitstream was generated.
- Why a stage was not run, if skipped.

Gate:

- Do not write "synth passed" without log/report evidence.
- If timing/resource status is unknown, say so explicitly.

## 7. Stage 6 - ILA / Board Debug

Outputs when used:

```text
ila/program.tcl
ila/capture_*.tcl
ila/export_*.tcl
out/ila/
out/hw_debug/
```

Rules:

- Put ILA/VIO scripts in the unit's `ila/`.
- Export CSV/log data directly to `out/ila/` or `out/hw_debug/`.
- Record scenario, register setup, trigger condition, result file, and conclusion.
- Before Hardware Manager commands, make scripts `cd` into a unit-local work directory and print it in the log.
- Snapshot `D:/hw_ila_data_*` before Vivado Hardware Manager work; after the run, archive only newly-created D-root `hw_ila_data_*` spill directories into the unit's `out/ila/` or `out/hw_debug/` and record the move. Vivado 2021.1 can emit these placeholders during ILA refresh/upload/display even when CSV/VCD outputs use absolute unit-local paths.

Gate:

- Board conclusions must trace to ILA, scope, register readback, or user-observed evidence.

## 8. Stage 7 - As-Built Handoff

Outputs:

```text
AI-work/guide/data-paths/<DLx>_<name>_AS_BUILT.md
```

Rules:

- `features/` keeps requirements, plans, failures, debug history, and raw evidence.
- `guide/` keeps stable verified facts.
- Simulation-verified but not board-verified facts may be written as as-built only with a clear "board not verified" note.
- If the user rejects the requirement direction, keep the unit as history and do not promote it to final as-built.

## 9. Artifact Containment

All new runtime artifacts belong in the current unit or project-level AI-work runtime folders.

| Artifact | Destination |
|---|---|
| `vivado*.log`, `vivado*.jou` | `<UNIT>/out/<stage>/` |
| `xvlog.log`, `xelab.log`, `xsim.log` | `<UNIT>/out/sim/` or `out/regression/` |
| `xsim.dir`, `xvlog.pb` | Prefer `<UNIT>/out/sim/work/`; otherwise record and clean/move at handoff |
| `*.wdb`, `*.wcfg`, `*.vcd` | `<UNIT>/out/sim/` or `<UNIT>/sim/` for layout |
| synth/impl/bitstream logs | `<UNIT>/out/synth/`, `out/impl/`, `out/bitstream/` |
| `hw_ila_data_*`, ILA CSV | `<UNIT>/out/ila/` or `out/hw_debug/` |

Run `scripts/scan-artifact-spill.py` when available before finalizing. For a project that already has old scattered artifacts, create a timestamp marker at unit start and scan with `--since-file <marker>` so the gate checks new spill rather than historical mess.

## 10. State Sync Gate

Before final response, check:

- `REQUIREMENTS.md` matches the current feature scope.
- `ARCHITECTURE.md` describes current RTL, not an abandoned plan.
- `IMPLEMENTATION.md` top status and detailed sections agree.
- `SIM_REPLAY.md` TC count, script names, and evidence paths match files on disk.
- PASS / BUILD PASS / board conclusions are recorded with evidence paths.
- Related annotations are still valid or marked stale.
- Runtime artifacts are not scattered in D: root or the project root.
- Verified facts are promoted to as-built when appropriate.

If not, report:

```text
DOC STALE:
- stale document:
- latest evidence:
- required sync:

ARTIFACT SPILL:
- spilled artifact:
- target location:
- status:
```

## 11. Final Response Shape

Mode 5 final responses must include the real handoff entry points:

```text
需求入口：AI-work/features/<feature>/<UNIT>/REQUIREMENTS.md
架构入口：AI-work/features/<feature>/<UNIT>/ARCHITECTURE.md
实施进度：AI-work/features/<feature>/<UNIT>/IMPLEMENTATION.md
RTL 审查：AI-work/features/<feature>/<UNIT>/RTL_REVIEW.md（如有）
仿真复现：AI-work/features/<feature>/<UNIT>/sim/SIM_REPLAY.md
仿真证据：AI-work/features/<feature>/<UNIT>/out/sim/
综合证据：AI-work/features/<feature>/<UNIT>/out/synth/（如有）
实现/bitstream 证据：AI-work/features/<feature>/<UNIT>/out/impl/ 或 out/bitstream/（如有）
ILA/上板证据：AI-work/features/<feature>/<UNIT>/out/ila/ 或 out/hw_debug/（如有）
项目级仿真 SOP：AI-work/env/SIMULATION.md 或 AI-work/guide/VIVADO_SIM_SOP.md
仍待确认：
```

Avoid ending with only "已完成，仿真通过".
