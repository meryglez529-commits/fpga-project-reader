# Reading Workflow

## Order

1. System boundary
2. Question ledger and evidence index
3. Main data link identification
4. Optional deep read of one selected data path
5. Clocks and reset
6. Control path
7. Storage and buffering
8. Verification and board bring-up

## Boundary Pass

Before reading implementation details:

1. List the project root.
2. Identify project entry files such as `.xpr`, `.qpf`, `.tcl`, Makefile, or project scripts.
3. Locate the top module and top source file.
4. Read only the top-level port declaration.
5. Group ports by clock/reset, data input, data output, storage, configuration/control, trigger/sync, and debug/board control.
6. Form initial hypotheses for main data links.

## Question Ledger First

Before reading implementation details or generated files, convert the first pass into narrow engineering questions.

Use this format in notes or directly in the guide's risk/evidence section:

| Question | Primary search | Evidence files | Status |
|---|---|---|---|
| What drives `ui_clk` and at what frequency? | `rg -n -C 3 "ui_clk|FREQ_HZ|mig_7series"` | `system.bd`, `system.v`, MIG `.xci` | confirmed / partial / unknown |
| Which module drives DAC data? | `rg -n -C 5 "DAX_DATA|DAY_DATA|dac_p"` | top RTL, scan modules | confirmed / partial / unknown |
| How does ADC data reach DDR? | `rg -n -C 5 "adc.*data|fdma|ui_clk"` | ADC modules, FDMA, BD wrapper | confirmed / partial / unknown |

For each question:

1. Search with `rg -n -C 3` to `-C 10`; avoid full-file reads.
2. Prefer the smallest authoritative file: top RTL for connectivity, `.xdc` for external clocks/pins, `.xci` for IP settings, `.bd` for BD structure, generated wrapper/synth files for frequency/interface annotations.
3. Record path, line number, fact, and confidence.
4. Only open a larger window if the first hit proves relevant.
5. Stop searching once the question is answered; move residual ambiguity to the risk section.

## Large File Discipline

Vivado/Quartus projects contain many generated files. Treat them as searchable evidence stores, not documents to read front to back.

Preferred first-pass files:

- Project metadata: `.xpr`, `.qpf`, `.tcl`, build scripts.
- Top RTL and wrappers: top module, BD wrapper, major subsystem top files.
- Constraints: active `.xdc`/`.sdc` for clocks, pins, generated clocks, false paths.
- IP configs: `.xci`, `.bd`, IP parameter TCL.

Read later and only by targeted query:

- `*.gen/`, `*.runs/`, `*.cache/`, `*.ip_user_files/`, simulator outputs, large generated XML/netlists.
- Vendor simulation models and generated encrypted/stub files.
- Historical imports or absolute paths unless resolving migration risk.

When a file appears binary, malformed, or encoding-damaged, do not dump it. Use `rg --text`, small `Select-String` windows, or find a parallel source copy.

## Main Data Link Evidence

Use these signals in priority order:

1. Engineering goal and business data semantics.
2. External real data ingress/egress ports.
3. Throughput estimate: width times frequency.
4. Module names such as `adc`, `dac`, `video`, `image`, `rx`, `tx`, `stream`, `packet`, `fifo`, `ddr`.
5. Signal names such as `data`, `valid`, `ready`, `last`, `sof`, `eof`, `wr_en`, `rd_en`.
6. FIFO/RAM/DDR direction: producer, consumer, and endpoint.

Ethernet, DDR, PCIe, and SFP may be main links or support links. Decide from business semantics, not interface name.

## Selected Data Path Deep Reading

After the main data links are identified, the user may ask to inspect one concrete path in detail. Use `references/data-path-deep-reading.md` for this second-stage workflow.

Deep reading answers:

- What is the data?
- Where does it come from and where does it end?
- How do width and meaning change?
- Which clock domains, FIFOs, CDC nodes, and buffers carry it?
- Which controls constrain this data path?
- How should it be verified in simulation, ILA, or board bring-up?

For output links, prefer sink-first reading on the first pass: start from the external endpoint or final output latch, derive the upstream data contract, then verify producers in the real production direction. For multi-source paths, find the unified mux/output contract before expanding source algorithms.

When producing a reusable handoff document, prefer the "code reading guide" shape from `references/data-path-deep-reading.md`: each pass names the file to open, search terms, relevant signals, what to ignore, local reading order, and exit questions. The DAC guide in `examples/dac-output-data-path-deep-reading.md` is the worked example.

## Clocks, Control, Storage

After main links are known:

- Clocks: explain which link segment each clock serves and where CDC occurs.
- Control: explain which data segment each control signal constrains.
- Storage: explain which link segment each FIFO/RAM/DDR/ROM/Flash structure serves and why it exists.

## Verification

Organize verification around links:

1. Data source to first buffer.
2. Last buffer to data endpoint.
3. Control entry and trigger behavior.
4. CDC nodes.
5. Shared-resource arbitration.
6. System-level closed loop.
7. Upgrade/debug/exception recovery.
