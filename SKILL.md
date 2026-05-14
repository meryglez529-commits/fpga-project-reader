---
name: fpga-project-reader
description: Read, analyze, annotate, and document unfamiliar FPGA/RTL projects. Use when Codex needs to inspect Vivado/Quartus/RTL repositories, identify top modules and main business data links, produce a whole-project FPGA_PROJECT_GUIDE, perform the second-stage deep read of one selected data path, or perform the third-stage close read and beginner-oriented annotation of one RTL/source file.
---

# FPGA Project Reader

Use this skill to turn an unfamiliar FPGA project into a structured engineering guide. The core rule is: **identify the real business data links first, then explain clocks, control, buffers, and verification in relation to those links.**

## Operating Modes

This skill has three primary stages. Keep them distinct.

| Mode | When to use | Default output | Required references |
|---|---|---|---|
| Whole-project map | The user asks to read an unfamiliar FPGA project, identify top modules, classify data links, or create an FPGA project guide. | `FPGA_PROJECT_GUIDE.md` style architecture guide organized by real data links. | `references/reading-workflow.md`, then `references/output-format.md` |
| Selected-path deep read | The user asks to deep-read/精读/细读/读某条通路, revise a path-specific reading guide, or apply the skill's second stage to one named data link. | Path-specific **code reading guide**, not an architecture summary, unless the user explicitly asks for a summary. | `references/data-path-deep-reading.md` and `examples/dac-output-data-path-deep-reading.md` |
| Single-file close read and annotation | The user names one RTL/source file and asks to read it, explain it, add comments, make it beginner-readable, or guide them through the file. | A source file with concise Chinese reading comments plus a guided explanation. Comments must explain the module's data model and contracts, not line-by-line syntax. | `references/single-file-close-reading.md` |

If a selected-path deep read is requested before a whole-project map exists, do a minimal boundary pass first: identify the path source, sink, main contract, and likely intermediate files. Then produce the selected-path reading guide. Do not expand into a full project guide unless the user asks for it.

For single-file close reading, first place the file in its local path context: who drives its inputs, who consumes its outputs, and which business data link it belongs to. If the user asks to add comments, comment the file itself only after this context pass, and keep functional RTL unchanged.

## Quick Workflow

1. **Find the boundary before RTL internals.**
   List the project root, identify project files (`.xpr`, `.qpf`, `.tcl`, Makefile), locate the top module, and read only the top-level port declaration first.

2. **Create a question ledger before opening large files.**
   Turn unknowns into narrow questions such as "what drives `ui_clk`?", "which module owns DAC data?", or "where does ADC data enter DDR?". Search for each question with `rg -n -C 3` or equivalent and read only the matching windows. Record file paths, line numbers, evidence, and confidence as you go.

3. **Identify main data links.**
   Use project goal, external data ports, throughput, module names, stream signals, FIFO/DDR directions, and endpoint semantics. Do not classify Ethernet/DDR/SFP/PCIe as main links by name alone.

4. **Deep-read a selected data path when needed.**
   After main links are known, use `references/data-path-deep-reading.md` to zoom into one concrete path. When the user asks to "deep-read", "精读", "细读", "读某条通路", or validate this skill on one path, the default deliverable is a **path-specific code reading guide**, not an after-the-fact architecture summary, unless the user explicitly asks for a summary. Each main pass must tell the reader which file to open, what to search, which signals matter, what to ignore, how to read the local code, what they should be able to answer, and where to go next. Use `examples/dac-output-data-path-deep-reading.md` as the acceptance example for this guide style.

5. **Close-read and annotate a single file when needed.**
   When the user names one file and asks for comments or a guided read, use `references/single-file-close-reading.md`. Build a first-principles data model before writing comments: define the real-world object, the stream segment or frame boundary, packing units, storage units, and downstream contract. Comments should teach the reader how to think about the module, not merely label assignments.
   For beginner-facing RTL comments, use the same shape as a good oral explanation: start with one plain sentence that explains what the module does, then answer "why this structure exists" before listing signal roles. If a comment would not help a novice understand the code faster, rewrite it.

6. **Use the right output shape.**
   For whole-project guides, use the structure in `references/output-format.md`. For a selected-path deep read, use the code-reading-guide shape in `references/data-path-deep-reading.md`. Always include required tables even when cells are `> ⚠️ 待确认`.

7. **Draw diagrams as source plus rendered SVG.**
   Prefer D2 for large architecture/data-link diagrams. Use Mermaid only for small local diagrams. See `references/diagram-guidelines.md`.

8. **Validate the result.**
   Check that every clock/control/storage item is tied to a data link, every uncertainty is collected in the risk section, and diagrams are readable at Markdown preview scale. For selected-path guides, run the mandatory deep-read acceptance gate below before finalizing. For single-file annotation, run the single-file acceptance gate below.

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

- Read `references/reading-workflow.md` when starting or continuing project analysis.
- Read `references/data-path-deep-reading.md` when the user asks to deep-read one identified data path, produce a path-specific reading SOP, or turn a path into a step-by-step code reading guide.
- Read `references/single-file-close-reading.md` when the user names one source file and asks to read it, explain it, comment it, annotate it, or make it beginner-readable.
- Read `references/output-format.md` when creating or revising the Markdown guide.
- Read `references/diagram-guidelines.md` before creating or replacing diagrams.
- Use `examples/dac-output-data-path-deep-reading.md` as the canonical acceptance example for a path-specific code reading guide. Match its step-by-step "open this file" shape when the user asks for a deep read.
- Use `scripts/validate-deep-reading-guide.py` as a mechanical guardrail for selected-path reading guides; it catches the common failure where a guide becomes a conclusion summary and omits per-pass reading instructions.

## Diagram Tool Preference

Use D2 for large diagrams because it preserves diagram source while producing crisp SVG. Store sources in `docs/diagrams/*.d2` and rendered images in `docs/images/*.svg`. Use bus/port helper nodes to improve routing instead of removing real engineering nodes.

For small diagrams with six or fewer main nodes, Mermaid inside Markdown is acceptable if labels are short and the diagram is not visually dominant.

## Discipline

- Do not modify RTL during reading unless explicitly requested.
- Do not dive into an `always` block before locating the module on a main data link.
- Do not bulk-read generated Vivado/Quartus files. Query them for exact evidence only, then summarize.
- Prefer source files, project metadata, BD files, and IP `.xci` configs before generated netlists, run outputs, cache XML, or simulator libraries.
- Keep a compact evidence ledger while reading so confirmed facts do not need to be rediscovered.
- Do not let support infrastructure displace the business data path.
- Do not submit a selected-path deep read as a plain conclusion summary when the user needs a reusable reading guide.
- Do not annotate a single file by adding jargon labels. First teach the data model that makes the code necessary.
- Before finalizing a path-specific guide, check that every major pass has: goal, search entries, relevant signals, ignore list, local reading order, exit question, and next step. A "关键证据" table can support these fields, but cannot replace them.
- Mark unsupported inferences as `> ⚠️ 待确认`.
