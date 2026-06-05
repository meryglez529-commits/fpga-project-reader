# <UNIT> 仿真复现说明

> 本文件给用户使用：如何复现仿真、打开波形、看每个 TC 的关键点。

项目级仿真环境 SOP：`AI-work/env/SIMULATION.md`（或项目指定的 `AI-work/guide/VIVADO_SIM_SOP.md`）

## 1. 本次仿真验证什么

<说明验证目标和边界。>

## 2. testbench 和 top

| 项 | 值 |
|---|---|
| 工程 | `<project.xpr>` |
| 仿真器 | Vivado XSim / ModelSim / Questa |
| testbench | `<path/to/tb.v>` |
| 仿真 top | `<tb_top>` |
| DUT | `<path/to/dut.v>` |

## 3. Vivado GUI 启动

```tcl
cd <PROJECT_ROOT_WITH_FORWARD_SLASHES>
open_project <PROJECT_XPR>
source AI-work/features/<feature-slug>/<UNIT>/sim/run_gui.tcl
```

## 4. Batch / PowerShell 重跑

```powershell
cd <PROJECT_ROOT_WITH_BACKSLASHES>
& "<VIVADO_BAT>" -mode batch -source AI-work\features\<feature-slug>\<UNIT>\sim\run_manual.tcl -log AI-work\features\<feature-slug>\<UNIT>\out\sim\vivado_run_manual.log -journal AI-work\features\<feature-slug>\<UNIT>\out\sim\vivado_run_manual.jou
```

## 5. 测试用例

| TC | 验证点 | 预期 | 证据 |
|---|---|---|---|
| TC1 | | | |

## 6. 重点信号

| 信号 | 你要确认什么 |
|---|---|
| `<signal>` | |

## 7. 通过标准

| 项 | 通过条件 |
|---|---|
| result | `out/sim/result.txt` 出现 `PASS` |
| log | `out/sim/xsim.log` 或指定日志没有非预期 ERROR |
| waveform | 关键窗口和边界符合第 5/6 节 |

## 8. AI 已生成的结果

| 产物 | 路径 | 说明 |
|---|---|---|
| result | `out/sim/result.txt` | |
| log | `out/sim/xsim.log` | |
| waveform | `out/sim/waveform.wdb` | 如未生成，写明原因 |

## 9. 未覆盖场景

| 场景 | 未覆盖原因 | 后续建议 |
|---|---|---|
| | | |
