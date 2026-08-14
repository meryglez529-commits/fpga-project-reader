# Mode 4 — 新板卡 FPGA 开发与接口 Bring-up

> 目标：从接口需求、原理图和器件资料建立可信的板卡契约，完成多个最小接口 Demo，把可复用资产提升到正式工程，并交付可由 Mode 3 直接接手的产品基线。

## 目录

1. 边界与授权
2. 双根目录和权威入口
3. 工作包结构
4. 状态模型
5. 阶段 0：输入与接口契约
6. 阶段 1：正式源码和板卡公共层
7. 阶段 2：Demo 规划与独立验证
8. 阶段 3：资产分类与提升
9. 阶段 4：产品工程基线
10. 阶段 5：依赖失效与回归
11. 阶段 6：板级验证与硬件移交
12. 阶段 7：Release 与 Mode 3 交接
13. 完成门槛与校验

## 1. 边界与授权

Use Mode 4 when a board is planned or newly received and no trusted product FPGA baseline exists. Inputs may be interface requirements, schematics, PCB pin exports, datasheets, BOM, timing budgets, or a partial vendor reference design.

Mode 4 covers:

- pre-layout FPGA feasibility and pin/bank/clock/transceiver review;
- post-layout source reconciliation and board contract freeze;
- official FPGA source-tree creation;
- independent minimum demos for required interfaces;
- simulation/build evidence and normal board-interface acceptance;
- promotion of verified board facts and reusable interface cores;
- creation of a safe, buildable product baseline and Mode 3 handoff.

Mode 4 does not absorb electrical hardware fault diagnosis. JTAG/configuration-chain faults, rail faults, soldering, connector, and PCB-net defects become `FPGA_READY_HARDWARE_BLOCKED` after the first decisive evidence and move to `hardware-handoff/`. Do not count that investigation as FPGA feature progress.

Before writing official sources, record in `AI-work/env/RULES.md` and `STATUS.md`:

- project root and authorized official design root;
- allowed RTL/XDC/IP/project/simulation write scope;
- target tool/version and board revision;
- whether programming and product-behavior actions are authorized;
- source-control state or hash-based provenance when Git is absent.

## 2. 双根目录和权威入口

Use two roots:

```text
<project-root>/
  <official-design-root>/            # default suggestion: fpga/
  AI-work/                            # collaboration, work, evidence
```

Suggested official design layout; adapt to an existing user convention rather than forcing this exact spelling:

```text
fpga/
  boards/<board>/
    constraints/
    clocks/
    ip/
    scripts/
  common/
    clock_reset/
    <interface-core>/
  demos/<demo>/
  product/
    rtl/
    constraints/
    ip/
    sim/
    scripts/
```

Official source includes authored RTL, XDC/SDC/QSF, IP configuration, simulation sources, and source-driven project/build Tcl. Put `.Xil`, `.runs`, `.gen`, generated projects, reports, logs, journals, checkpoints, bitstreams, and caches under the active `AI-work/` unit. A checked-in native project file is permitted only when the user explicitly selects that project style and its generated output paths remain isolated.

The board-level `STATUS.md` is the only overall status authority. Demo status files own only their demo. `README.md`, `LOG.md`, and other reports link to these authorities; they must not maintain competing current-state claims.

## 3. 工作包结构

Create the bring-up unit from `assets/new-board-work-package/`:

```text
AI-work/bringup/<board>/<BRINGUP_UNIT>/
  STATUS.md
  SOURCE_REGISTER.md
  BOARD_CONTRACT.md
  INTERFACE_MATRIX.md
  BRINGUP_PLAN.md
  ACCEPTANCE_MATRIX.md
  DEMO_DEPENDENCY_MATRIX.md
  MODE3_HANDOFF.md
  demos/<demo>/<DEMO_UNIT>/
  hardware-handoff/
  work/
  out/
  release/
    RELEASE_MANIFEST.md
```

Create each demo from `assets/demo-work-package/`. Do not require interfaces that are not selected in `INTERFACE_MATRIX.md`. Do not create empty, pretend-complete demo packages.

Keep source documents in place unless the user authorizes organization. Register every input in `SOURCE_REGISTER.md` with origin, revision/date, hash when practical, role, and confidence. AI-created PDF renders, OCR, extracted text, screenshots, and temporary files belong in the unit's `work/`, never project-root `tmp/` or a drive root.

## 4. 状态模型

Use one of these demo states:

```text
PLANNED
CONTRACT_READY
BUILD_PASS
READY_FOR_BOARD
BOARD_PASS
FPGA_READY_HARDWARE_BLOCKED
FAILED_FPGA
STALE
NOT_APPLICABLE
OBSOLETE
```

Use one of these board bring-up states:

```text
DISCOVERED
CONTRACT_READY
DEMOS_IN_PROGRESS
DEMO_BUILD_READY
INTERFACES_QUALIFIED
PRODUCT_BASELINE_READY
MODE3_READY
HARDWARE_BLOCKED
```

Never use an unqualified `PASS`. Separate simulation, synthesis, implementation, bitstream, ready-for-board, and board-pass claims. A required interface may be waived only by an explicit acceptance-matrix entry with approver/reason/date; a waiver is not a board pass.

## 5. 阶段 0：输入与接口契约

Outputs: `SOURCE_REGISTER.md`, `BOARD_CONTRACT.md`, `INTERFACE_MATRIX.md`.

For each interface record:

- purpose and required/optional status;
- external component and protocol/electrical standard;
- direction, width, rate, clocking, reset, voltage, bank, differential polarity;
- FPGA resource/site requirements such as clock-capable pins, byte lanes, SERDES, GT channel/quad, and reference clock;
- expected minimum demo and acceptance evidence;
- schematic/datasheet/netlist source and confidence;
- confirmed, inferred, conflicting, or open status.

Perform an FPGA-side review before schematic/PCB freeze when possible. Reconcile the final schematic/PCB pin export before creating a qualified constraint set. Do not infer a pin, bank voltage, reference frequency, configuration voltage, or differential polarity from a net name alone.

Gate: do not implement a demo whose FPGA behavior depends on an unresolved contract fact. Record the blocker instead of encoding a guess.

## 6. 阶段 1：正式源码和板卡公共层

Create one canonical board layer in the official design root. Demos and product must consume the same authoritative board constraints, clocks/resets, IP configuration, and reusable interface cores; do not copy them between projects.

Prefer composable constraint fragments such as base/configuration, clocks, ADC, SFP, UART, and DDR, while preserving one reviewed source of truth for every physical pin. Record the build entry, part, top, source set, and tool version for each project.

Generate tool projects and runs in unit-local `work/<project>/<run>/`. Export selected logs and reports to the matching demo `out/` directory. Generated files may be deleted/rebuilt by the user later; they are never the only holder of a required source or configuration.

## 7. 阶段 2：Demo 规划与独立验证

Select demos from the interface matrix. A typical risk-ordered sequence is:

```text
configuration-safe GPIO
→ board clocks/resets
→ low-speed control (UART/SPI/I2C)
→ ADC/LVDS or other source-synchronous interfaces
→ memory
→ transceivers/SFP
→ integrated interface smoke
```

Each demo answers one bounded question: whether its hardware interface and FPGA-side contract are usable. Keep the top minimal and safe. Avoid starting with the product architecture or coupling unrelated interfaces into the first test.

Each demo records:

- exact official sources and shared dependencies;
- intended behavior and safe output defaults;
- simulation applicability and replay, or justified `NOT_APPLICABLE`;
- synthesis/implementation/DRC/timing/bitstream evidence as applicable;
- candidate bitstream identity;
- board procedure, instruments/settings, observations, and pass/fail criteria;
- reuse classification in `REUSE_MANIFEST.md`.

Examples of test-only assets include IBERT IP, PN checker, memory traffic generator, UART echo top, LED divider, and loopback wrapper. Their reusable board constraints, clock/reset logic, interface PHY, or vendor configuration may be promoted separately.

## 8. 阶段 3：资产分类与提升

Classify every meaningful demo artifact:

| Class | Destination/meaning |
|---|---|
| `BOARD_FACT` | Promote verified pin/clock/bank/polarity/resource facts to the canonical board layer. |
| `REUSABLE_CORE` | Promote one canonical source to `common/` or the selected official shared path. |
| `TEST_ONLY` | Keep in the demo; never include it in product by convenience. |
| `VENDOR_CONFIG` | Keep the authored IP configuration in the official source tree; generated products remain work. |
| `GENERATED` | Keep only as reproducible work/evidence, never as authoritative source. |
| `OBSOLETE` | Preserve for traceability outside release and prevent downstream use. |

`REUSE_MANIFEST.md` records the source path, promoted destination, identity/hash, demo evidence, product consumer, and classification. Promote by referencing or moving to one canonical official source; do not leave independent edited copies in demo and product.

## 9. 阶段 4：产品工程基线

After required interface demos reach their approved gate, create a product baseline that instantiates the canonical board layer and promoted reusable interfaces. Business behavior may be a safe stub, loopback, or minimal pipeline, but the product baseline must not depend on demo-only tops/checkers/generators.

The baseline must record:

- official product path, top, part, source set, constraints, IP configs, and build command;
- safe behavior of unused or not-yet-developed outputs;
- required interfaces integrated versus intentionally stubbed;
- simulation/build/timing/DRC/bitstream status;
- source-control revision or source hash manifest;
- known limitations and explicit waivers.

`PRODUCT_BASELINE_READY` means the product project is reproducibly buildable. It does not mean product features are complete or every physical interface passed.

## 10. 阶段 5：依赖失效与回归

Maintain `DEMO_DEPENDENCY_MATRIX.md` from official source paths to demo and product consumers. At minimum apply these invalidation rules:

| Change | Invalidate/recheck |
|---|---|
| FPGA part, bank, common physical constraints | All affected demos and product builds |
| Shared clocks/resets | Every consumer in that clock/reset tree |
| Shared interface core or vendor configuration | Its demo and all product regressions using it |
| Demo-only top/checker/generator | That demo only |
| Product business logic only | Mode 3 feature regression; interface demos stay valid unless shared dependencies changed |
| Tool/IP version | Affected generation, simulation, build, and release identity |

Mode 3 must read this matrix before modifying a shared path. Mark affected demo states `STALE` before claiming a new product baseline. Rerun only the mapped scope; do not repeat every board demo without an invalidating change.

## 11. 阶段 6：板级验证与硬件移交

Physical programming or equipment operation requires explicit authorization for that session. Confirm the expected board revision and exact candidate image before use. Store normal board acceptance under the demo's `out/board-test/` and update `ACCEPTANCE_MATRIX.md`.

If evidence points to an electrical fault outside standard FPGA development:

1. preserve the first decisive log/measurement and exact image identity;
2. stop repetitive downloads or software-variable elimination that cannot distinguish causes;
3. set the demo to `FPGA_READY_HARDWARE_BLOCKED`;
4. write `hardware-handoff/<issue>.md` with symptom, reproduction boundary, FPGA-side exclusions, requested hardware checks, and safety notes;
5. keep FPGA build readiness separate from board availability.

Do not claim a board pass from implementation success, an open eye from link-up alone, or interface correctness from a schematic-only review.

## 12. 阶段 7：Release 与 Mode 3 交接

Use these artifact states:

```text
out/bitstream/candidate/    # built, not formally qualified
out/bitstream/obsolete/     # invalid/stale, traceability only
release/bitstream/          # explicitly qualified for the stated use
release/RELEASE_MANIFEST.md
```

Never rely on a warning inside a Markdown file to protect an invalid image that remains in a qualified location. A release manifest records file/hash, part, top, tool/IP version, source identity, board/constraint revision, intended behavior, build status, board status, applicable hardware revision, and known limitations.

`MODE3_HANDOFF.md` records:

- official product project path and canonical build/simulation entry;
- product top, part, tool/IP versions, source identity;
- board contract and acceptance-matrix identity;
- required demo states and waivers;
- shared board/core sources and demo dependency matrix;
- test-only and obsolete exclusions;
- qualified release identity;
- remaining feature work and non-FPGA blockers;
- declared state `MODE3_READY` only when the completion gate passes.

Mode 3 consumes this handoff directly; it does not rerun Mode 1 merely because the project is new. Mode 1 remains available later for independent takeover, audit, or foundation repair.

## 13. 完成门槛与校验

Mode 4 is complete only when:

- the authorized design root and board revision are recorded;
- source/register/contract/interface/acceptance/dependency documents agree;
- every required interface is `BOARD_PASS` or explicitly waived;
- reusable assets have one canonical official source and reuse manifests;
- the product baseline build is reproducible and `PRODUCT_BASELINE_READY`;
- no `TEST_ONLY`, `GENERATED`, or `OBSOLETE` asset is treated as product source;
- no obsolete image appears in release and every release artifact is hashed;
- hardware blockers are separated into handoff records;
- runtime artifacts remain inside the active `AI-work/` unit;
- `MODE3_HANDOFF.md` declares `MODE3_READY` and validation passes.

Run:

```text
python <skill>/scripts/validate-ai-work.py <project-root>/AI-work
python <skill>/scripts/validate-new-board-work-package.py <bringup-unit> --design-root <official-design-root> --project-root <project-root>
```

Run `validate-demo-work-package.py` for each required demo, or let the board validator invoke the same checks. Validation checks structure and cross-document state; it does not replace log, waveform, instrument, or board evidence review.
