# Mode 1 — 工程接手与协作基础

> 目标：把“接手工程”变为可验证、可恢复、且不伤害用户工程的共同起点。Mode 1 合并了旧的工程地图、主数据通路精读和协作环境搭建；它建立可协作的基线，不实施产品功能。

## 1. 边界与授权

Mode 1 的默认权限是只读工程、写入项目根下的 `AI-work/`，并运行不会改写用户工程的检查或隔离构建。它可以创建指南、脚本、报告、运行日志和基线清单；所有这些产物必须进入 `AI-work/`。

Mode 1 不得：

- 修改 RTL、XDC、IP、Block Design、工程设置或用户的 `synth_1`/`impl_1` run；
- 新增 ILA 探针、生成 debug bitstream，或把现有 bitstream 当作功能正确性证据；
- 写业务寄存器、启动扫描/采集/激光/电机等产品行为；
- 初始化、暂存、提交、重置或清理用户 Git 工作区；
- 因为工具默认路径方便，就把日志、`.jou`、`xsim.dir`、波形、CSV、bit/LTX 或 `hw_ila_data_*` 留在工程根、盘符根或临时目录。

**可选硬件动作**必须获得用户本次会话的明确授权：连接 JTAG、下载 bitstream、刷新设备或读取已有 ILA。即使已授权，Mode 1 也只允许无业务副作用的能力盘点；Tcl 只能下载/读取，不能自动配置业务寄存器或开始仪器运行。

## 2. 何时建立或修复

以下任意一项命中即进入 Mode 1（或只重跑失效阶段）：

1. 缺少 `AI-work/`，或缺少基础目录/`README.md`/`LOG.md`/`OPEN-QUESTIONS.md`；
2. 缺少本节的基础文档、状态清单或其内容仍是模板；
3. 文档、脚本和实际工程/命令/日志相互矛盾；
4. RTL、XDC、IP、顶层、工具版本、许可证、板卡/JTAG、bit/LTX 任一相关输入已变化；
5. 当前需求需要的能力（仿真、构建、已有 ILA、板卡）没有足够证据。

不要只因目录存在就跳过。先读 `env/SETUP_STATUS.md` 和最近的 `reports/baseline/<baseline-id>/foundation_manifest.json`，从最早失效的阶段恢复。

## 3. 必须形成的基础包

```text
AI-work/
  guide/FPGA_PROJECT_GUIDE.md
  guide/data-paths/<DL*>_DEEP_READ.md
  env/ENVIRONMENT.md
  env/HARDWARE.md
  env/SIMULATION.md                  # 或明确指向 guide/VIVADO_SIM_SOP.md
  env/DEBUG_CAPABILITY.md
  env/SETUP_STATUS.md
  env/RULES.md
  env/SNAPSHOTS.md
  env/GLOSSARY.md
  scripts/
  reports/baseline/<baseline-id>/
    foundation_manifest.json
    tool/ sim/ synth/ impl/ bitstream/ debug/
```

`SETUP_STATUS.md` 是人读入口；`foundation_manifest.json` 是机器可验入口。两者至少包含：

| 字段 | 要求 |
|---|---|
| `baseline_id` / 时间 | 每次基线唯一、可排序 |
| target profile | `.xpr`、顶层、part、XDC、目标板、run、bit/LTX 身份 |
| baseline protection | Git revision + dirty state，或 RTL/XDC/IP 哈希；标明 `CLEAN_BASELINE` 或 `DIRTY_BASELINE` |
| 每阶段 | 命令、工作目录、日志/报告、开始/结束、结果、失败原因、下一步 |
| 状态 | `DISCOVERED`、`BASELINE_PROTECTED`、`TOOL_CHECKED`、`SIM_READY`/`SIM_BLOCKED`、`BUILD_READY`/`BUILD_BLOCKED`、`DEBUG_READY`/`DEBUG_UNAVAILABLE`、`BOARD_READY`/`READY_NO_BOARD`、`RULES_CONFIRMED`、`READY` |
| 结论边界 | “流程可跑”与“功能/时序签核通过”必须分开 |

## 4. 执行顺序

### 4.1 定位工程并保护基线

1. 确认项目根、工程文件、顶层、器件、约束、源集合、IP/BD 和构建 run；不要根据目录名猜测。
2. 记录 Git `HEAD` 与 `status --short`；无 Git 时生成源、约束和 IP 的哈希清单。脏树仍可检查，但标记 `DIRTY_BASELINE`，绝不覆盖其 run。
3. 创建 `reports/baseline/<baseline-id>/` 与每阶段子目录。所有 `-log`、`-journal`、xsim 输出、报告、导出文件和工具临时目录都使用该基线路径。
4. 检查 Vivado/Hardware Manager 是否已有进程、锁或用户 GUI 会话。存在时不要抢占、关闭或复用其运行目录；记录为隔离风险并换用独立路径，做不到则 `BUILD_ISOLATION_BLOCKED`。

### 4.2 建立阅读理解

1. 按 `reading-workflow.md` 写 `FPGA_PROJECT_GUIDE.md`：工程根、顶层、时钟/复位、主要模块、接口、约束、IP、构建入口和未知项。
2. 从真实的业务数据流而非目录分类识别所有主通路；对每条主通路按 `data-path-deep-reading.md` 生成 `guide/data-paths/<DL*>_DEEP_READ.md`。无法深读的路径必须写清排除原因与后续入口。
3. 产生的理解文档须指向真实文件和实例，避免用推测填空。

### 4.3 工具、IP、约束与仿真能力

使用 `scripts/templates/check_env.tcl` 的定制副本或等价脚本，将输出写进本次 baseline 的 `tool/`。检查应区分：

- **PASS**：命令和证据明确完成；
- **DEGRADED**：工程可继续检查，但 IP repo、锁定 IP、许可证、约束或工具配置存在警告/未知；
- **FAIL**：项目无法打开、关键文件不可读、工具命令失败或输出隔离不成立。

`IPDEF`、`*.xci` 或一次 `report_ip_status` 并不能证明许可证可用。许可证是否真实可用只有在相应仿真/综合命令实际运行后才能结论化。把 IP repo 缺失、IP lock、license 未验证分别写入状态。

随后按 `simulation-environment.md` 探测并记录**该项目**的最小仿真 smoke。真实成功与失败都要记录命令、日志、版本、依赖、工作目录和输出位置。对于这台机器上已经验证的 Vivado 特殊经验，应按项目事实记录，例如 batch `launch_simulation` 的 broken pipe、通过 batch Vivado → Tcl 内部 `exec xvlog/xelab` → Vivado builtin `xsim` 的可用路径、直接 `xsim` 遇到加密 `init.tcl` 的限制及 GUI/Webtalk 行为。不要把它们当作其他工程的通用规律，也不要擅自改 Vivado 安装文件。

### 4.4 最小全流程基线

在隔离路径中尝试：

```text
simulation smoke → synthesis → implementation → bitstream
```

这条链仅证明命令、依赖、许可证和产物定位的**工作流**，不等于完整回归、板级验证、功能正确或时序签核。每步都必须写明确的 `PASS`、`BLOCKED` 或 `NOT_RUN`：

- `PASS`：保存命令、退出码、日志和关键报告/产物；
- `BLOCKED`：保存阻塞日志，说明是否需要用户选择、许可证、IP、仿真模型、板卡或外部输入；
- `NOT_RUN`：必须给出未运行原因，不能借此称作完成。

不能将 Vivado run 目录安全地重定向至 `AI-work/` 时，停止构建阶段并记录 `BUILD_ISOLATION_BLOCKED`。不得以覆盖工程既有 run 或向工程/盘符根输出作为替代方案。

可把 skill 的 `run-baseline-pipeline.ps1` 复制到项目的 `AI-work/scripts/` 后使用。调用者必须为仿真、综合、实现、bitstream 提供已审核的项目专用 Tcl，并显式传入项目、顶层、part；各 Tcl 接收 `<project.xpr> <stage-output-dir>`，只可写入第二个参数。脚本把每一步的 command/work/log/status/blocker/next action 写入 `foundation_manifest.json`。它不会替任何工程猜测仿真 top、IP 生成步骤或 build run 设置。

### 4.5 已有硬件与 ILA 能力盘点

没有硬件授权时，状态应为 `READY_NO_BOARD` 或 `DEBUG_UNAVAILABLE`，并不妨碍软件基线完成。获得授权后，使用仅盘点脚本并记录：目标链、器件、既有 bit/LTX 的 hash/时间、ILA/VIO 核名、采样时钟、深度、探针名/宽度和调试文件匹配性。

`inspect-existing-ila.tcl` 和 `program-baseline.tcl` 都要求命令行中明确包含 `USER_AUTHORIZED`；前者不触发 capture，后者只下载一对已确认的 bit/LTX，且不会写业务寄存器或开始设备工作。复制后仍要把日志和 status 文件放在当前 baseline 的 `debug/` 目录。

现有 ILA 的能力边界同样重要：缺少输入脚、输出脚、共同采样时钟、握手或时间戳时，必须明确“不能凭这组 probe 得出该结论”。跨时钟独立 ILA 的波形只支持事件相关性，不能声称精确端到端延迟；需要精确延迟时，把共同时钟观察或 timestamp/handshake 设计列为 Mode 3 要求。

## 5. 失效、恢复与完成

| 变化 | 至少失效的阶段 |
|---|---|
| RTL/XDC/IP/顶层/源集合 | 仿真、综合、实现、bitstream、调试能力结论 |
| 工具、许可证、IP repo | 工具检查、仿真、构建 |
| 板卡/JTAG、bit/LTX | debug/physical，只要源未变无需重跑构建 |
| 文档 | 对应文档和链接检查 |
| Mode 2 注释 | 编码/换行/差异清单检查；除非误改功能字节，否则不使构建失效 |

恢复时保留旧 baseline 和失败证据，创建新的 `<baseline-id>` 或在 manifest 中记录续跑关系。不可用的能力是有价值的结果，不能靠空文件、模板词或正则匹配伪装为就绪。

Mode 1 完成前，运行：

```text
python <skill>/scripts/validate-ai-work.py <project-root>/AI-work
python <skill>/scripts/validate-foundation.py <project-root>/AI-work
python <skill>/scripts/validate-simulation-sop.py <project-root>/AI-work
```

校验器检查的是真实结构、状态和 manifest/evidence 关系，不替代人工阅读日志。通过后更新 `SETUP_STATUS.md`、`LOG.md`、`OPEN-QUESTIONS.md`；用户确认 `RULES.md` 后才可转入 Mode 3。
