# Co-work Environment Setup SOP

> 目标：把一个已经被 Mode 1/Mode 2 读过的 FPGA 工程，转化为 Claude Code 可以**安全**进行闭环编辑、仿真、综合的协作环境。完成后用户可以放心地说"帮我改一下 X 模块"，AI 不会因为缺信息瞎搞。

这是 skill 的第四个 mode。它依赖 Stage 0 已经建好 `AI-work/`，并强烈建议先跑过 Mode 1，最好也跑过 Mode 2。

## 0. 核心原则

### 0.1 准备 > 行动

宁可在 setup 阶段多问几个问题，也不要在闭环改代码时才发现"DAC 颗粒型号不知道""license 不可用""文件编码不一致"。setup 阶段问的问题应该多到让用户略觉啰嗦，但每个问题都要落到 `env/*.md` 里成为可追溯的事实。

### 0.2 可回滚 > 可前进

第一件事是建立基线快照并**演练一次回滚**。没有回滚能力之前不动一行 RTL。

### 0.3 显式契约 > 隐含默契

`RULES.md` 是 AI 和用户之间的"协作合同"。哪些文件可以改、哪些必须问、闭环跑多久要刹车、判 pass/fail 用什么标准——全部写在文件里。**用户没有显式确认 RULES.md 之前，不开始任何改代码动作。**

### 0.4 工具链是事实，不是假设

不要假设 vivado 在 PATH 里、xsim 能跑、git 已初始化。每一项都跑一次、记录结果、写进 `ENVIRONMENT.md`。

## 1. SOP 总览（七步）

```text
Step 1  →  探测工具链与工程现状（自动）
Step 2  →  问用户必要问题（4~8 个，按工程实际情况裁剪）
Step 3  →  写 env/ 下的七份 .md
Step 4  →  从 skill 模板生成 AI-work/scripts/*.tcl
Step 5  →  建立/更新项目级仿真 SOP
Step 6  →  建立基线快照 + 回滚演练
Step 7  →  跑 check_env.tcl 一次，确认通畅
Step 8  →  把 RULES.md 给用户看，等明确确认
```

每一步完成后在 `LOG.md` 追加一条。

## 2. Step 1 — 探测

在不修改工程的前提下，自动收集以下信息：

| 项 | 怎么收集 | 落到哪 |
|---|---|---|
| Vivado 可执行路径 | `where vivado.bat`（PowerShell）或 `where.exe vivado.bat` | ENVIRONMENT.md |
| Vivado 版本 | `vivado -version`（如果路径已知） | ENVIRONMENT.md |
| 仿真器候选 | 检查 `where vsim`、`where questasim`、Vivado 自带 xsim | ENVIRONMENT.md |
| 仿真可用路径 | 探测 batch/GUI/xsim/ModelSim 路径，记录可用和不可用原因 | SIMULATION.md |
| 工程文件 | 扫 `.xpr`、`.tcl`（含 `create_project` 的） | ENVIRONMENT.md |
| 顶层模块 | 复用 Mode 1 结果，否则查 `set_property top` | ENVIRONMENT.md |
| 器件型号 | 查 `set_property part` 或 `.xpr` 第一行 part | HARDWARE.md |
| 板上器件 | 复用 Mode 1 结果（`ad9258_cfg.v`、`ad9747_cfg.v` 这类配置模块名是线索） | HARDWARE.md |
| 时钟与 IO | 扫 `.xdc` 找 `create_clock`、`set_property PACKAGE_PIN` | HARDWARE.md |
| IP 清单 | 扫 `*.xci`，提取 IPDEF 和 module_name | guide/IP-INVENTORY.md（若 Mode 1 没产出则补） |
| 文件编码 | 抽样 5 个 `.v` 文件，用 chardet 或 BOM 嗅探 | ENVIRONMENT.md |
| 换行符 | 抽样同样的文件看 `\r\n` vs `\n` | ENVIRONMENT.md |
| 磁盘空间 | `Get-PSDrive` 看工程所在盘 | ENVIRONMENT.md |
| Git 状态 | `git status` / `git log -1`，没有就标记需要初始化 | SNAPSHOTS.md |
| 工程路径长度 | 测当前路径字符数，>200 警告，>240 强警告 | ENVIRONMENT.md |

把不确定的条目暂时写 `> ⚠️ 待确认`，进入 Step 2 问用户。

## 3. Step 2 — 问用户

不要列死问题清单。**根据 Step 1 探测结果，缺什么问什么。** 推荐用 AskUserQuestion 一次性问 3~4 个最关键的，再追问。

### 必问的问题模板

按重要性排序，工程实际情况允许就跳过已知项：

1. **Vivado 路径**：如果 Step 1 探不到，问绝对路径。
2. **仿真器选择**：探到多个时让用户选；只探到 ModelSim 时确认它的 Xilinx 库是否已编译。
3. **基线方式**：git init + commit / 用现有 git 仓库 / 手动 Copy-Item 备份。
4. **当前调试焦点**：要改的模块或数据通路、要修的 bug、想加的功能、要验证的现象。这是 `FOCUS.md` 的核心内容。

### 推荐追问

5. **Pass/Fail 标准**："仿真怎么算通过？"——具体到信号、log 关键字、对比文件、波形断言。
6. **不能动的文件**：用户认为的"敏感"文件，不只是 IP 例程。
7. **闭环预算**：每天最多跑几次综合？单次仿真上限多久？
8. **代码风格**：命名、注释语言、缩进——可以让 AI 自己扫现有代码推断，但有歧义时问。
9. **硬件型号**：探不到的板上器件型号（颗粒、PHY、DAC/ADC 子型号）。
10. **已知 bug**：当前已知但还没修的所有问题，避免 AI 修一个触发另一个。

### 不该问的问题

- 已经能从工程里读出来的（顶层模块、器件型号、IP 清单）。
- 风格小事可以自己扫推断（缩进、注释颜色），扫不出再问。
- 一次问超过 4 个，会让用户烦躁。分批问。

## 4. Step 3 — 写 env/ 下的七份 .md

每份都有最小必备字段。下面是模板。

### 4.1 `env/ENVIRONMENT.md`

```markdown
# Environment

> 工具链快照。改了工具链（升级 Vivado、换仿真器）就更新这份文件。

## 操作系统与外壳

| 项 | 值 |
|---|---|
| OS | Windows 11 Pro 22631 |
| Shell | PowerShell 5.1 |
| 工程根路径 | `D:/.../fpga_prj` |
| 工程路径字符长度 | 142（<240，安全） |

## 工具链

| 工具 | 路径 | 版本 | 状态 |
|---|---|---|---|
| Vivado | `C:/Xilinx/Vivado/2021.1/bin/vivado.bat` | 2021.1 | OK |
| xsim | Vivado 自带 | 2021.1 | OK |
| ModelSim | `D:/modeltech64_10.6d/win64/vsim.exe` | 10.6d | 库未编译，暂不使用 |
| Git | `C:/Program Files/Git/cmd/git.exe` | 2.40.x | OK |
| D2 | `.tools/d2.exe` | v0.7.1 | 用于绘图 |

## 仿真器选择

当前选用：**xsim**（Vivado 自带，零配置）。

切换到 ModelSim 的前置条件：先用 `compile_simlib` 把 Xilinx 库编译到 `D:/modeltech64_10.6d/vivado_lib`，并验证 `fifo_generator` 这类受影响 IP 能跑通。

## 文件约定

| 项 | 值 |
|---|---|
| 源文件编码 | UTF-8（无 BOM） |
| 注释语言 | 中文（部分 Xilinx 例程为英文，保持原样） |
| 换行符 | CRLF |
| 缩进 | 4 空格（部分 Xilinx 例程用 Tab，保持原样） |

## 磁盘

| 盘 | 剩余空间 |
|---|---|
| D: | 187 GB（充足） |

## License

| IP | 类型 | 状态 |
|---|---|---|
| SGMII_TEMAC | 付费 | 已确认 license 可用（`check_env.tcl` 输出确认） |
| 其他 | 免费 | OK |
```

### 4.2 `env/HARDWARE.md`

```markdown
# Hardware

> 板子接口与片外器件清单。改了硬件（换板、换颗粒）就更新这份文件。

## FPGA

| 项 | 值 |
|---|---|
| 系列 | Kintex-7 |
| 型号 | xc7k325tffg676-2 |
| 封装 | FFG676 |
| 速度等级 | -2 |
| 板号 | <填或 ⚠️> |

## 片外器件

| 器件 | 用途 | 接口 | 控制模块/IP | 备注 |
|---|---|---|---|---|
| AD9258 | 双通道 14bit ADC | 并行 LVDS + SPI 配置 | `ad9258_cfg.v` + `adcdata_acq.v` | 采样率 ⚠️ 待确认 |
| AD9747 | 双通道 16bit DAC | 并行 + SPI | `ad9747_cfg.v` + `dac_output.v` | |
| AD9517 | 时钟分发 | SPI | `ad9517_cfg.v` | 输出多路差分时钟 |
| DDR3 | 主存 | MIG 7-Series AXI | `system.bd` 内 MIG + `ddr3_ctrl.v` + FDMA 读写 | 颗粒型号 ⚠️ 待确认 |
| Ethernet PHY | 千兆以太网 | SGMII（GTX）+ MDIO | `SGMII_PHY.xci` + `SGMII_TEMAC.xci` + `ephy_top.v` | PHY 芯片型号 ⚠️ |
| QSPI Flash | 配置 + 远程升级 | QSPI | `qspi_cfg.v` + `multiboot_cfg_new.v` | |

## 主时钟

| 时钟 | 频率 | 来源 | 服务的数据链路 |
|---|---|---|---|
| `sysclk` | <填> | 板上晶振 | 全局 |
| MIG `ui_clk` | ⚠️ 推测 200 MHz | MIG 内部 | DDR3 读写 |
| 其他 | | | |

## IO 关键约束位置

`AXI_DDR.srcs/constrs_1/new/fpga_pin.xdc`
```

### 4.3 `env/RULES.md`

这是协作合同。模板：

```markdown
# Rules

> 协作合同。AI 改代码前必须读这份文件。用户改了规则要在 LOG.md 记录。

## 文件改动权限

### 可以直接改

- `AXI_DDR.srcs/sources_1/new/*.v`
- `AXI_DDR.srcs/sources_1/imports/new/*.v`
- `AXI_DDR.srcs/sim_1/**/*.v`
- `AI-work/**`

### 改之前必须先告诉用户、得到口头同意

- `AXI_DDR.srcs/constrs_1/**/*.xdc`（约束改动影响时序、引脚、跨域路径）
- `AXI_DDR.srcs/sources_1/ip/**/*.xci`（IP 配置改动会触发重新综合）
- `AXI_DDR.srcs/sources_1/bd/**`（block design 影响系统结构）

### 只读，不允许改

- `AXI_DDR.srcs/sources_1/imports/imports/SGMII_*`（Xilinx 例程）
- `AXI_DDR.srcs/sources_1/imports/ethernet/SGMII_TEMAC_*`（同上）
- 任何 `*.gen/`、`*.runs/`、`*.cache/`（生成物）

## 闭环刹车

| 触发条件 | 动作 |
|---|---|
| 单次仿真 wall-time 超过 10 分钟 | 停下来报告，等用户决定 |
| 同一个测试失败连续 3 轮 | 停下来分析根因，不再机械改 |
| 单日综合次数超过 4 次 | 暂停综合，转仿真层验证 |
| 触及"必须先问"的文件 | 立即停下来问用户 |

## Pass/Fail 标准

### 仿真层

- testbench 必须 `$display("PASS")` 或 `$display("FAIL: <reason>")`
- 仿真退出码 0 = pass，非 0 = fail
- 关键信号 csv 导出，与 golden 文件比对（如果有）

### 综合层

- WNS ≥ 0 ns
- 无 critical warning
- 资源占用变化 < 5%（不允许悄悄涨）

### 上板层

不在闭环范围。AI 写脚本辅助，但下板验证由用户执行。

## 代码风格观察

- 模块名：snake_case（`adcdata_acq`、`fdma_controller_read`）
- 信号名：snake_case
- 注释：以中文为主，Xilinx 例程保持英文
- 缩进：4 空格（混入了部分 Tab，新写文件用 4 空格）
- 模块头：暂无固定模板

## 用户口头确认

- [ ] 用户已阅读本文件
- [ ] 用户已确认上述规则
- [ ] 确认时间：____________
- [ ] 后续修改需在 LOG.md 留痕
```

### 4.4 `env/FOCUS.md`

```markdown
# Focus

> 当前调试/改动的焦点。聚焦项目里**正在动**的部分，不是整体功能列表。
> 焦点变了就改这份文件，不要堆历史。历史挪到 LOG.md。

## 当前调试焦点

**功能描述**：<一句话说清楚正在调什么>

**涉及模块/通路**：
- `<file:line>`
- `<file>`

**当前现象**：
- 期望：
- 实际：
- 复现条件：

**用户已经尝试过**：
- 

**已知未修 bug**（避免 AI 触发）：
- 

**期望产出**：
- [ ] 仿真层验证通过
- [ ] 综合时序收敛
- [ ] 上板验证（用户执行）

**截止时间**（可选）：
```

### 4.5 `env/SNAPSHOTS.md`

```markdown
# Snapshots

> 基线快照与里程碑。回滚命令必须可执行。

## 基线（baseline）

| 项 | 值 |
|---|---|
| 时间 | <YYYY-MM-DD HH:MM> |
| 方式 | git / Copy-Item |
| 引用 | `git: <commit hash>` 或 `dir: AXI_DDR.srcs.baseline_YYYYMMDD` |
| 工程状态 | 综合通过 / 仿真通过 / 上板已验证 |

## 回滚命令

```powershell
# git 方式
git reset --hard <baseline-hash>

# 或备份目录方式
Remove-Item -Recurse AXI_DDR.srcs
Copy-Item -Recurse AXI_DDR.srcs.baseline_YYYYMMDD AXI_DDR.srcs
```

## 回滚演练

| 时间 | 改动 | 回滚命令 | 结果 |
|---|---|---|---|
| <填> | 在某无害文件加一行注释 | `git checkout -- <file>` | 还原成功，工程仍可打开 |

## 后续里程碑

每个稳定节点打 tag/备份，追加到下表：

| 时间 | tag/备份 | 说明 |
|---|---|---|
```

### 4.6 `env/GLOSSARY.md`

```markdown
# Glossary

> 工程内的缩写、自创术语、业务概念对照。新缩写出现就追加。

## 模块/接口缩写

| 缩写 | 全称/含义 | 出处 |
|---|---|---|
| FDMA | Frame DMA, 工程自定义的 AXI 突发读写控制器 | `fdma_controller_*.v` |
| LAN | 局域网/以太网相关 | `LAN_*.v` 一族 |
| EPHY | Ethernet PHY 配置/握手 | `ephy_top.v`、`vio_ephy.xci` |
| TEMAC | Tri-mode Ethernet MAC（Xilinx） | `SGMII_TEMAC.xci` |
| ARP | 地址解析协议 | `ARP_TOP.v`、`LAN_RX_ARP.v` |
| ICMP | Ping 协议 | `ICMP_TOP.v` |
| MIG | Memory Interface Generator（Xilinx DDR 控制器） | `system.bd` |
| QSPI | Quad SPI Flash 接口 | `qspi_cfg.v` |
| MULTIBOOT | Xilinx 远程升级方案 | `multiboot_cfg_new.v` |

## 业务术语

| 术语 | 含义 |
|---|---|
| 帧 | <一帧的物理含义，由用户提供> |
| 行重复 | <由用户提供> |
| 步进 | <由用户提供> |
| 采集/回放 | ADC/DAC 数据流的方向 |

## 信号约定

| 信号风格 | 约定 |
|---|---|
| `*_en` | 高电平有效使能 |
| `*_n` | 低电平有效（含复位） |
| `*_p/*_n` | 差分对 |
| `*_valid/*_ready` | AXI Stream 风格握手 |
| `*_wr_en/*_rd_en` | FIFO 接口 |
```

### 4.7 `env/SIMULATION.md`

这是项目级仿真环境 SOP。它记录“这个工程在这台机器上怎么跑仿真”，不是某个功能的 testbench 说明。

如果项目已经有成熟 SOP（例如 `AI-work/guide/VIVADO_SIM_SOP.md`），可以在这里链接它，但 `env/SIMULATION.md` 必须说明哪个文件是权威入口。

最小结构：

```markdown
# Simulation Environment

## 1. 当前结论

| 项 | 结论 |
|---|---|
| 推荐仿真器 | xsim / ModelSim / Questa |
| 推荐 batch 路径 | <可用路径或 BLOCKED> |
| 推荐 GUI 路径 | <可用路径或 BLOCKED> |
| 项目级详细 SOP | `AI-work/guide/VIVADO_SIM_SOP.md` / 本文件 |

## 2. 工具链与路径
## 3. 可用/不可用仿真路径
## 4. 特殊环境约束
## 5. Batch 仿真 SOP
## 6. GUI 仿真 SOP
## 7. IP simulation 文件生成与 prj 规则
## 8. 常见故障与处理
## 9. 可复用模板
## 10. 验证记录
```

要特别记录：

- 加密 `init.tcl`、IP 加密、license、公司网络、Webtalk、路径长度等会影响仿真的环境因素。
- 哪些命令已验证可用，哪些命令已验证不可用，以及原因。
- Mode 5 的 `sim/SIM_REPLAY.md` 应该引用这里，而不是重复环境坑。

## 5. Step 4 — 生成 scripts/

从 skill 的 `scripts/templates/` 复制以下模板到 `AI-work/scripts/`，**根据本工程实际情况修改**：

| 模板 | 必须改 | 用途 |
|---|---|---|
| `check_env.tcl` | xpr 路径、付费 IP 名 | 环境自检：开工程 + 列源文件 + 验 license + report_compile_order |
| `run_sim.tcl` | top tb 名、要导出的信号集 | xsim 一键编译+仿真+导 csv |
| `run_manual.tcl` | 复杂环境下手动 xvlog/xelab/xsim 流程 | 绕开 `launch_simulation` 或直接 `xsim.exe` 的环境坑 |
| `run_synth.tcl` | xpr 路径、报告输出位置 | 综合 + 抽 WNS/TNS/资源 |
| `export_csv.tcl` | 信号集合 | 把仿真波形指定信号导成 csv |
| `diff_report.tcl` | 两个 checkpoint 路径 | 资源/时序对比 |

复制后必须在脚本头部加一行注释，写明源模板版本和复制时间：

```tcl
# Generated from skill templates/check_env.tcl on <YYYY-MM-DD>
# Customized for project: AXI_DDR
```

## 6. Step 5 — 建立/更新项目级仿真 SOP

按 `references/simulation-environment.md` 执行。至少要判断：

- batch 仿真是否可用。
- GUI 仿真是否可用。
- 直接调用 `xsim.exe` 是否可用。
- IP 仿真模型是否需要 `generate_target Simulation`。
- 是否存在加密 Tcl/IP、Webtalk、路径长度、license、仿真库等限制。

如果复杂仿真暂时无法跑通，写清楚：

```text
SIMULATION BLOCKED:
- 已验证失败路径：
- 失败原因：
- 仍可使用的验证方式：
- Mode 5 需要避免宣称：
```

注意：`check_env.tcl` 只证明工程能打开、compile order 能解析；它不等于复杂 testbench 能跑通。

## 7. Step 6 — 基线快照 + 回滚演练

### 6.1 建立基线

按用户在 Step 2 的选择执行：

**git 方式（推荐）**：

```powershell
cd <project_root>
git status
# 如果未初始化
git init
git add -A
git commit -m "baseline: before AI-work co-work setup"
git tag baseline-pre-cowork
```

**备份方式（用户拒绝 git 时）**：

```powershell
$ts = Get-Date -Format "yyyyMMdd_HHmm"
Copy-Item -Recurse AXI_DDR.srcs "AXI_DDR.srcs.baseline_$ts"
```

### 6.2 回滚演练

**必须执行**。否则不算 setup 完成。

```powershell
# 1. 在某无害文件（比如 README）加一行
# 2. 检查 git status / 备份对照
# 3. 执行回滚命令
# 4. 验证：git status 干净 / 文件已还原
```

把演练过程写进 `SNAPSHOTS.md` 的"回滚演练"表。

## 8. Step 7 — 跑 check_env.tcl

```powershell
cd <project_root>
& "C:/Xilinx/Vivado/2021.1/bin/vivado.bat" -mode batch `
    -source AI-work/scripts/check_env.tcl `
    -tclargs <project_xpr_path> `
    -log AI-work/sim_out/check_env.log `
    -journal AI-work/sim_out/check_env.jou
```

确认日志中：

- [ ] 工程成功打开
- [ ] 顶层模块识别正确
- [ ] 所有 `.xci` 都能找到
- [ ] 付费 IP license 检查通过
- [ ] `report_compile_order` 没报缺文件

任何一项不通过，先解决再继续。

## 9. Step 8 — 把 RULES.md 给用户看，等明确确认

不要自己默认通过。**显式向用户展示 RULES.md 的关键条款**，并要求"是/可以/同意"这种明确回复。用户回复后：

1. 在 `RULES.md` 末尾的"用户口头确认"打勾，写入确认时间。
2. 在 `LOG.md` 追加一行：`<时间> | cowork-setup | RULES.md confirmed by user`。
3. 至此 Mode 4 完成。

之后任何 RTL 编辑、IP 改参数、综合发起都可以基于这份合同执行。

## 10. 验收

调用 `scripts/validate-ai-work.py`：

```powershell
python <skill_path>/scripts/validate-ai-work.py <project_root>/AI-work
python <skill_path>/scripts/validate-simulation-sop.py <project_root>/AI-work
```

期望输出 `PASS`。任何 `FAIL` 都要补齐对应字段后重新跑。

## 11. 不该做的事

- 不要在用户没确认 `RULES.md` 之前发起任何 RTL 修改。
- 不要在 setup 过程中"顺手"修工程的 bug——那是闭环阶段的工作，先把环境搭完。
- 不要把复杂仿真经验只写进某个 feature unit；可复用经验要回写项目级 `env/SIMULATION.md` 或指定的 `VIVADO_SIM_SOP.md`。
- 不要让新仿真/综合/ILA 产物散到 D 盘根目录或工程根目录；规则写进 `RULES.md`。
- 不要把硬件细节（DDR3 颗粒型号、PHY 子型号）凭推测写进 `HARDWARE.md`，标 `> ⚠️ 待确认` 然后留给用户填。
- 不要复用别的工程的 `HARDWARE.md`/`RULES.md`，每个工程都重新走一遍 SOP。
- 不要在 `RULES.md` 写"AI 自由发挥"这种空话——闭环刹车要可机械判定。
