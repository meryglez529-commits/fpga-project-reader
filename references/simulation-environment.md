# Simulation Environment SOP

> 目标：把“这个工程在这台机器上怎么跑仿真”记录成项目级事实。Mode 4 维护本文件；Mode 5 引用它并把新发现反哺回来。

Use this reference during Mode 4 and whenever a project has unusual simulator behavior, encrypted Tcl/IP, broken batch simulation, GUI-only flows, Webtalk stalls, manual IP sim file requirements, or toolchain-specific replay steps.

## 1. Output Location

Preferred output:

```text
AI-work/env/SIMULATION.md
```

If an existing project already has a substantial SOP, keep it and link it:

```text
AI-work/guide/VIVADO_SIM_SOP.md
```

But `AI-work/env/ENVIRONMENT.md` or `AI-work/env/SIMULATION.md` must point to the canonical simulation SOP.

## 2. Required Sections

`SIMULATION.md` should contain:

```markdown
# Simulation Environment

## 1. 当前结论
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

## 3. Required Facts

Record at least:

| Fact | Example |
|---|---|
| Vivado path/version | `D:/Xilinx/Vivado/2021.1/bin/vivado.bat`, 2021.1 |
| Simulator selection | xsim / ModelSim / Questa |
| Working batch path | e.g. Vivado batch opens project, `exec xvlog/xelab`, then uses Vivado Tcl `xsim` command |
| Broken paths | e.g. `launch_simulation` in batch, direct `xsim.exe`, GUI launch before Webtalk fix |
| Why broken | encrypted `init.tcl`, broken pipe, Webtalk stall, missing sim libraries |
| Required environment fix | e.g. rename `wbtcv.exe`, compile simlib, use shorter path |
| IP sim model policy | when to `generate_target Simulation [get_ips]`, which generated files must enter `.prj` |
| Log/result locations | project-level defaults and unit-level expectations |

## 4. Mode 4 Probe

Mode 4 does not need to prove every future feature testbench works, but it should probe enough to avoid blind feature work:

1. Confirm Vivado can open the project.
2. Confirm compile order resolves or record blockers.
3. Confirm at least one simulator path is known-good or explicitly blocked.
4. If no simulator path is known-good, write `SIMULATION BLOCKED` and do not let Mode 5 claim sim closure.

For difficult projects, create a tiny smoke test or reuse a known-good testbench. If a smoke test cannot be run because of encryption/IP/tool limits, explain why.

## 5. Mode 5 Relationship

Mode 5 unit docs should not duplicate the whole project-level SOP. They should link it:

```text
项目级仿真环境：AI-work/env/SIMULATION.md
```

or:

```text
项目级仿真环境：AI-work/guide/VIVADO_SIM_SOP.md
```

If Mode 5 discovers a new reusable trick:

1. Record the immediate issue/fix in the unit's `IMPLEMENTATION.md`.
2. Update the project-level SOP after it is verified.
3. Add a `LOG.md` entry.

## 6. Artifact Containment

The SOP should define where Vivado writes logs, journals, xsim work dirs, waveforms, and ILA exports.

Recommended rule:

- Project-level environment checks write to `AI-work/sim_out/` or `AI-work/reports/`.
- Feature-level runs write to `AI-work/features/<feature>/<UNIT>/out/<stage>/`.
- Do not leave new `vivado*.log`, `.jou`, `xsim.dir`, `xvlog.pb`, or `hw_ila_data_*` in D: root or the project root.

## 7. Validation

Run:

```powershell
python <skill>/scripts/validate-simulation-sop.py AI-work
```

The validator checks that a simulation SOP exists and records working paths, broken paths, environment constraints, reusable scripts/templates, and verification records.
