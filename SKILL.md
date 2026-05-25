---
name: fpga-project-reader
description: Read, analyze, annotate, document, and prepare an unfamiliar FPGA/RTL project for closed-loop collaboration. Use when Codex/Claude needs to inspect Vivado/Quartus/RTL repositories, identify top modules and main business data links, produce a whole-project FPGA_PROJECT_GUIDE, perform the second-stage deep read of one selected data path, perform the third-stage close read and beginner-oriented annotation of one RTL/source file, or perform the fourth-stage setup of an `AI-work/` co-work environment so Claude Code can run closed-loop sim/synth/edit cycles on the project. Triggers include "读这个工程""接手这个项目""精读""细读""读某条通路""注释这个文件""搭建协作环境""搭一下 AI-work""准备闭环""协作环境""跑通这个工程"。
---

# FPGA Project Reader

Use this skill to turn an unfamiliar FPGA project into a structured engineering guide **and** a ready-to-collaborate workspace. The core rule is: **identify the real business data links first, then explain clocks, control, buffers, and verification in relation to those links; then turn the understanding into an `AI-work/` workspace where closed-loop editing, simulation, and synthesis can run safely.**

## Operating Modes

This skill has four primary modes. Keep them distinct.

| Mode | When to use | Default output | Required references |
|---|---|---|---|
| Whole-project map | The user asks to read an unfamiliar FPGA project, identify top modules, classify data links, or create an FPGA project guide. | `AI-work/guide/FPGA_PROJECT_GUIDE.md` style architecture guide organized by real data links. | `references/reading-workflow.md`, then `references/output-format.md` |
| Selected-path deep read | The user asks to deep-read/精读/细读/读某条通路, revise a path-specific reading guide, or apply the skill's second stage to one named data link. | Path-specific **code reading guide** under `AI-work/guide/data-paths/`, not an architecture summary, unless the user explicitly asks for a summary. | `references/data-path-deep-reading.md` and `examples/dac-output-data-path-deep-reading.md` |
| Single-file close read and annotation | The user names one RTL/source file and asks to read it, explain it, add comments, make it beginner-readable, or guide them through the file. | The source file with concise Chinese reading comments, plus a pointer record in `AI-work/annotations/`. Comments must explain the module's data model and contracts, not line-by-line syntax. | `references/single-file-close-reading.md` |
| Co-work environment setup | The user asks to set up a collaboration workspace, prepare closed-loop sim/synth, "搭一下 AI-work", "搭建协作环境", "准备闭环", or otherwise enable Claude Code to safely edit/simulate/synthesize this project. | `AI-work/env/` with ENVIRONMENT.md, HARDWARE.md, RULES.md, FOCUS.md, SNAPSHOTS.md, GLOSSARY.md, plus TCL templates under `AI-work/scripts/` and one successful `check_env.tcl` run. | `references/cowork-environment-setup.md` |

If a selected-path deep read is requested before a whole-project map exists, do a minimal boundary pass first: identify the path source, sink, main contract, and likely intermediate files. Then produce the selected-path reading guide. Do not expand into a full project guide unless the user asks for it.

For single-file close reading, first place the file in its local path context: who drives its inputs, who consumes its outputs, and which business data link it belongs to. If the user asks to add comments, comment the file itself only after this context pass, and keep functional RTL unchanged.

For co-work environment setup, do not begin RTL edits, IP changes, or synthesis runs until the acceptance gate below passes and the user has explicitly confirmed `AI-work/env/RULES.md`.

## Stage 0: AI-work Bootstrap

**Every mode starts here.** Before doing whole-project mapping, deep reads, single-file annotation, or co-work setup, ensure the `AI-work/` workspace exists at the project root. This directory is the **single home for all skill outputs** so the original project tree stays clean.

Minimal bootstrap on first run of any mode:

1. Check whether `AI-work/` exists at the project root. If not, create the skeleton:

   ```text
   AI-work/
   ├── README.md              # one-paragraph explanation of what AI-work is and who writes here
   ├── LOG.md                 # append-only collaboration log
   ├── OPEN-QUESTIONS.md      # shared across all modes
   ├── .gitignore             # excludes sim_out/, reports/, *.wdb, *.jou, *.log
   ├── guide/                 # Mode 1+2 outputs
   │   ├── data-paths/
   │   └── diagrams/
   ├── annotations/           # Mode 3 outputs
   ├── env/                   # Mode 4 outputs
   ├── scripts/               # runnable TCL/python (copied from skill templates on demand)
   ├── sim/                   # testbenches written during co-work
   ├── sim_out/               # simulation outputs (gitignored)
   └── reports/               # synth/timing/DRC reports (gitignored)
   ```

2. Route current-mode output into the right subdirectory (see Operating Modes table).
3. Append a one-line entry to `LOG.md`: timestamp, mode invoked, top-level intent.
4. If `OPEN-QUESTIONS.md` does not exist, create it with an empty table; add unresolved questions to it as they appear in any mode.

See `references/ai-work-bootstrap.md` for the exact skeleton contents and the cross-mode protocol.

## Default Flow For An Unfamiliar Project

When the user hands over a new FPGA project without specifying a mode (e.g., "读这个工程", "接手这个项目", "跑通这个环境"), the default sequence is:

1. **Stage 0** — bootstrap `AI-work/` (silent, no confirmation needed).
2. **Mode 1 — Whole-project map.** At the end, ask: "要继续精读一条主数据通路吗？" Stop here if the user says no.
3. **Mode 2 — Selected-path deep read.** Default to the highest-throughput main link from Mode 1's result. At the end, ask: "要搭协作环境（AI-work co-work setup）吗？" Stop here if no.
4. **Mode 4 — Co-work environment setup.** Build `AI-work/env/`, generate scripts, run `check_env.tcl`, present `RULES.md` for confirmation. Stop here.
5. **Mode 3 — Single-file close read.** Only triggered by explicit user request on a named file; not part of the default flow.

The user may stop, skip, or jump at any boundary. Do not silently chain modes past a stage boundary without an explicit "继续" or equivalent.

## Quick Workflow

1. **Bootstrap `AI-work/` first.**
   On the first invocation of any mode, ensure `AI-work/` exists with the skeleton from `references/ai-work-bootstrap.md`. Append the current invocation to `AI-work/LOG.md`. Route all subsequent skill outputs into the matching `AI-work/` subdirectory.

2. **Find the boundary before RTL internals.**
   List the project root, identify project files (`.xpr`, `.qpf`, `.tcl`, Makefile), locate the top module, and read only the top-level port declaration first.

3. **Create a question ledger before opening large files.**
   Turn unknowns into narrow questions such as "what drives `ui_clk`?", "which module owns DAC data?", or "where does ADC data enter DDR?". Search for each question with `rg -n -C 3` or equivalent and read only the matching windows. Record file paths, line numbers, evidence, and confidence as you go. Park residual unknowns in `AI-work/OPEN-QUESTIONS.md`.

4. **Identify main data links.**
   Use project goal, external data ports, throughput, module names, stream signals, FIFO/DDR directions, and endpoint semantics. Do not classify Ethernet/DDR/SFP/PCIe as main links by name alone.

5. **Deep-read a selected data path when needed.**
   After main links are known, use `references/data-path-deep-reading.md` to zoom into one concrete path. When the user asks to "deep-read", "精读", "细读", "读某条通路", or validate this skill on one path, the default deliverable is a **path-specific code reading guide** placed in `AI-work/guide/data-paths/`, not an after-the-fact architecture summary, unless the user explicitly asks for a summary. Each main pass must tell the reader which file to open, what to search, which signals matter, what to ignore, how to read the local code, what they should be able to answer, and where to go next. Use `examples/dac-output-data-path-deep-reading.md` as the acceptance example for this guide style.

6. **Close-read and annotate a single file when needed.**
   When the user names one file and asks for comments or a guided read, use `references/single-file-close-reading.md`. Build a first-principles data model before writing comments: define the real-world object, the stream segment or frame boundary, packing units, storage units, and downstream contract. Comments should teach the reader how to think about the module, not merely label assignments. Record an entry in `AI-work/annotations/` pointing at the annotated file with a short rationale.
   For beginner-facing RTL comments, use the same shape as a good oral explanation: start with one plain sentence that explains what the module does, then answer "why this structure exists" before listing signal roles. If a comment would not help a novice understand the code faster, rewrite it.

7. **Set up the co-work environment when needed.**
   When the user asks to "搭建协作环境", "搭一下 AI-work", "准备闭环", or otherwise enable closed-loop editing, use `references/cowork-environment-setup.md`. Populate `AI-work/env/` with ENVIRONMENT.md, HARDWARE.md, RULES.md, FOCUS.md, SNAPSHOTS.md, GLOSSARY.md; instantiate TCL templates from `scripts/templates/` into `AI-work/scripts/`; run `check_env.tcl` once; perform a rollback drill; present `RULES.md` to the user for explicit confirmation. Do not begin RTL edits, IP changes, or synthesis runs until the acceptance gate passes.

8. **Use the right output shape.**
   For whole-project guides, use the structure in `references/output-format.md`. For a selected-path deep read, use the code-reading-guide shape in `references/data-path-deep-reading.md`. For the co-work environment, use the file templates in `references/cowork-environment-setup.md`. Always include required tables even when cells are `> ⚠️ 待确认`.

9. **Draw diagrams as source plus rendered SVG.**
   Prefer D2 for large architecture/data-link diagrams. Use Mermaid only for small local diagrams. Store sources in `AI-work/guide/diagrams/` and rendered images alongside them. See `references/diagram-guidelines.md`.

10. **Validate the result.**
    Check that every clock/control/storage item is tied to a data link, every uncertainty is collected in the risk section, and diagrams are readable at Markdown preview scale. For selected-path guides, run the mandatory deep-read acceptance gate below before finalizing. For single-file annotation, run the single-file acceptance gate below. For co-work environment, run the co-work acceptance gate below and `scripts/validate-ai-work.py` against `AI-work/`.

## Selected-Path Acceptance Gate

A selected-path deep-read guide is not acceptable if it only contains a path diagram, evidence tables, or module summaries. For every major pass that opens a source file, the guide must contain:

```text
本步目标
搜索入口
本模块相关信号
先忽略
代码阅读顺序
读完应能回答
下一步
```

Use a concise self-check before finalizing:

1. Count the major "open this file" passes. There should usually be at least five for a nontrivial FPGA path.
2. Verify every major pass has the seven required fields above.
3. Verify at least one table records data shape changes: signal/data name, width, meaning, valid condition, and transformation.
4. Verify CDC/buffer structures are tied to the selected path, with write clock, read clock, data width, write condition, and read condition.
5. Verify every branch or mux section explains how that branch returns to the selected path's unified contract.
6. Verify the final verification section is grouped into practical ILA/simulation signal sets.
7. If `scripts/validate-deep-reading-guide.py` is available, run it on the Markdown guide and revise until it passes or explicitly explain why the guide is intentionally summary-only.

## Co-work Environment Acceptance Gate

A co-work setup is not acceptable if it only creates folders and TCL templates. Before declaring the setup complete and before any RTL edits begin:

1. **`AI-work/env/ENVIRONMENT.md`** must record: Vivado executable absolute path, Vivado version (from `vivado -version`), simulator choice (xsim/ModelSim/Questa) and its install path, simulator compiled library path (if not xsim), OS, shell, file encoding convention used in the project (UTF-8/GBK), line-ending convention (CRLF/LF), and remaining free disk space at the project drive.
2. **`AI-work/env/HARDWARE.md`** must record: FPGA device family/package/speed grade, board identifier (if known), and one row per off-chip device that touches a main data link (ADC/DAC/clock-gen/DDR/PHY/Flash). Each row must include device part number, the IP or RTL module that controls it, and the interface (parallel/SPI/I2C/MDIO/QSPI/MGT/DDR). Unknown values are filled with `> ⚠️ 待确认` and copied into `OPEN-QUESTIONS.md`.
3. **`AI-work/env/RULES.md`** must record: read-only file globs (typically vendor example RTL and IP `.xci`), editable file globs (user-written modules), "ask-before-touching" globs (`.xdc`, BD, IP parameters), closed-loop brake conditions (max single-sim wall time, max retries on the same failure, max synth runs per day), pass/fail criteria for the current focus, code style observations (naming, indentation, comment language), and any team conventions (commit message prefix, branch policy).
4. **`AI-work/env/FOCUS.md`** must record: the specific module(s) or data path currently under debug, what "correct" looks like (signal-level or test-level), the current symptom or unknown, what the user has already tried, and the deadline or urgency if any. Known unfixed bugs are listed here.
5. **`AI-work/env/SNAPSHOTS.md`** must record: the baseline snapshot (git commit hash or backup directory path), its timestamp, and the exact rollback command. The rollback must have been **drilled once**: change one harmless file, restore, verify clean.
6. **`AI-work/env/GLOSSARY.md`** must record at minimum: every non-obvious abbreviation found in module/file names (FDMA, LAN, EPHY, TEMAC, SGMII, etc.), and every business term the user has used during setup (帧、行重复、步进、采集等).
7. **`AI-work/scripts/check_env.tcl`** must have been executed once successfully with the log preserved under `AI-work/sim_out/check_env.log`. The log must show: project opens, license available for paid IP, compile order resolves, no missing files.
8. The user has **explicitly confirmed** `RULES.md` before any RTL edits begin. Record the confirmation as a `LOG.md` entry.

If `scripts/validate-ai-work.py` is available, run it against the project's `AI-work/` directory and revise until it passes.

## Single-File Annotation Acceptance Gate

A single-file close read is not acceptable if comments only restate signal names or explain Verilog syntax. Before finalizing:

1. Identify the file's upstream producer, downstream consumer, and role in the business data link.
2. Define the reader's mental model before local code details: real-world quantity, stream/frame boundary, packing unit, storage unit, and valid/enable contract.
3. Explain how dimensions transform, such as position count vs. channel count, sample width vs. bus width, byte count vs. FDMA word count.
4. Check the comments against the "oral explanation test": could the same paragraph be said to a beginner at the desk and make them say "now I get it"? If not, simplify it into a one-sentence model plus a concrete example.
5. Replace or avoid unreadable legacy comments when possible; do not leave new guidance mixed with mojibake/乱码.
6. Add comments at section boundaries and non-obvious contracts, not on every line.
7. Do not change functional RTL unless the user explicitly asks for a fix.
8. Verify syntax-level structure after editing at minimum: module/endmodule counts, begin/end balance, and key assignments still present.

## References

- Read `references/ai-work-bootstrap.md` on the first invocation of any mode against a project that has no `AI-work/` directory.
- Read `references/reading-workflow.md` when starting or continuing project analysis.
- Read `references/data-path-deep-reading.md` when the user asks to deep-read one identified data path, produce a path-specific reading SOP, or turn a path into a step-by-step code reading guide.
- Read `references/single-file-close-reading.md` when the user names one source file and asks to read it, explain it, comment it, annotate it, or make it beginner-readable.
- Read `references/cowork-environment-setup.md` when the user asks to set up `AI-work/env/`, prepare closed-loop sim/synth, or otherwise enable Claude Code to safely edit and run this project.
- Read `references/output-format.md` when creating or revising the Markdown project guide.
- Read `references/diagram-guidelines.md` before creating or replacing diagrams.
- Use `examples/dac-output-data-path-deep-reading.md` as the canonical acceptance example for a path-specific code reading guide. Match its step-by-step "open this file" shape when the user asks for a deep read.
- Use `scripts/validate-deep-reading-guide.py` as a mechanical guardrail for selected-path reading guides; it catches the common failure where a guide becomes a conclusion summary and omits per-pass reading instructions.
- Use `scripts/validate-ai-work.py` as a mechanical guardrail for the co-work environment setup; it catches missing must-have files and unfilled acceptance fields.
- Use `scripts/templates/*.tcl` as the source of TCL templates (`check_env.tcl`, `run_sim.tcl`, `run_synth.tcl`, `export_csv.tcl`, `diff_report.tcl`). Copy them into `AI-work/scripts/` and customize per project; do not edit the templates in-place.

## Diagram Tool Preference

Use D2 for large diagrams because it preserves diagram source while producing crisp SVG. Store sources in `AI-work/guide/diagrams/*.d2` and rendered images in `AI-work/guide/diagrams/*.svg`. Use bus/port helper nodes to improve routing instead of removing real engineering nodes.

For small diagrams with six or fewer main nodes, Mermaid inside Markdown is acceptable if labels are short and the diagram is not visually dominant.

## Discipline

- Always route mode outputs into `AI-work/` per the bootstrap protocol. Do not scatter Markdown guides, diagrams, scripts, or notes across the project tree.
- Do not modify RTL during reading unless explicitly requested.
- Do not dive into an `always` block before locating the module on a main data link.
- Do not bulk-read generated Vivado/Quartus files. Query them for exact evidence only, then summarize.
- Prefer source files, project metadata, BD files, and IP `.xci` configs before generated netlists, run outputs, cache XML, or simulator libraries.
- Keep a compact evidence ledger while reading so confirmed facts do not need to be rediscovered.
- Do not let support infrastructure displace the business data path.
- Do not submit a selected-path deep read as a plain conclusion summary when the user needs a reusable reading guide.
- Do not annotate a single file by adding jargon labels. First teach the data model that makes the code necessary.
- Before finalizing a path-specific guide, check that every major pass has: goal, search entries, relevant signals, ignore list, local reading order, exit question, and next step. A "关键证据" table can support these fields, but cannot replace them.
- Do not begin RTL edits, IP changes, synthesis runs, or simulation iterations on behalf of the user until Mode 4 (co-work environment setup) has been completed and the user has confirmed `RULES.md`. A whole-project map alone does not authorize edits.
- Do not silently chain modes. Stop at each stage boundary in the default flow and ask for explicit "继续".
- Mark unsupported inferences as `> ⚠️ 待确认` and copy them into `AI-work/OPEN-QUESTIONS.md`.
