# AI-work Bootstrap

> 目标：当 `fpga-cowork` skill 第一次在一个工程上被触发时，先建立 `AI-work/` 目录，作为这个 skill 所有产出的统一收纳处。后续五个 mode 都把产出写到这里。

这一步是 Stage 0。它**不替代**任何一个 mode，但**每个 mode 启动前都要先确认 `AI-work/` 存在**。

## 0. 何时执行

每次 mode 触发时，先做这个判断：

| 判断 | 动作 |
|---|---|
| 工程根目录下没有 `AI-work/` | 创建骨架，写入 README/LOG/OPEN-QUESTIONS/.gitignore，再继续当前 mode |
| `AI-work/` 已存在 | 跳过骨架创建，直接把当前 mode 产出写到对应子目录，并在 `LOG.md` 追加一行 |
| `AI-work/` 存在但骨架不完整（缺 README/LOG 等） | 补齐缺失文件后再继续 |

不要询问用户是否建立 `AI-work/`。这是默认动作。

## 1. 工程根目录在哪

按以下顺序判断：

1. 当前工作目录中存在 `*.xpr` (Vivado) 或 `*.qpf` (Quartus) → 这一级就是工程根。
2. 当前工作目录中存在 `*.tcl` 重建脚本（含 `create_project` 命令）→ 这一级是工程根。
3. 当前工作目录中存在 `*.srcs/`、`*.sim/`、`constrs_1/` 等典型 Vivado 子目录 → 上一级是工程根；若上一级也没有更明确的工程文件，就用当前目录。
4. 都没有 → 在 `OPEN-QUESTIONS.md` 记录"工程根不明确"，把 `AI-work/` 建在当前目录。

## 2. 骨架结构

创建以下目录和文件。空目录用一个 `.gitkeep` 占位。

```text
AI-work/
├── README.md
├── LOG.md
├── OPEN-QUESTIONS.md
├── .gitignore
├── guide/
│   ├── .gitkeep
│   ├── data-paths/
│   │   └── .gitkeep
│   └── diagrams/
│       └── .gitkeep
├── annotations/
│   └── .gitkeep
├── env/
│   └── .gitkeep
├── features/
│   └── .gitkeep
├── scripts/
│   └── .gitkeep
├── sim/
│   └── .gitkeep
├── sim_out/
│   └── .gitkeep
└── reports/
    └── .gitkeep
```

## 3. 必备文件的最小内容

### 3.1 `AI-work/README.md`

```markdown
# AI-work

这是 `fpga-cowork` skill 为本工程建立的协作工作区。所有 skill 产出（工程地图、数据通路精读、单文件注释、协作环境、新功能开发证据）都收纳在这里，不污染原工程目录。

## 目录用途

| 子目录 | 谁写 | 装什么 |
|---|---|---|
| `guide/` | Mode 1 全工程地图 + Mode 2 数据通路精读 | `FPGA_PROJECT_GUIDE.md`、`IP-INVENTORY.md`、`CLOCKS.md`、`data-paths/*.md`、`diagrams/*.d2` 和渲染后的 `.svg` |
| `annotations/` | Mode 3 单文件注释 | 每次注释一份说明：注释了哪个文件、为什么、改了什么。源文件本体仍在工程目录原位 |
| `env/` | Mode 4 协作环境搭建 | `ENVIRONMENT.md`、`HARDWARE.md`、`RULES.md`、`FOCUS.md`、`SNAPSHOTS.md`、`GLOSSARY.md`、`SIMULATION.md` |
| `features/` | Mode 5 功能开发工作包 | 每个新增/修改功能一个 `<feature-slug>/<UNIT>/`，包含 `REQUIREMENTS.md`、`ARCHITECTURE.md`、`IMPLEMENTATION.md`、`sim/`、`synth/`、`impl/`、`ila/`、`out/` |
| `scripts/` | Mode 4 | 从 skill 模板复制并定制的项目级 `.tcl`/`.py`，可直接 `vivado -mode batch -source` 调用 |
| `sim/` | 闭环协作中 AI 写的 testbench | `*.v`、`.do` |
| `sim_out/` | Mode 4 运行产物 | 环境自检仿真 log、csv、wdb（不进 git） |
| `reports/` | Mode 4 运行产物 | 环境自检综合/时序/DRC 报告（不进 git） |

## 顶层文件

- `LOG.md`：协作日志，每次对话和每轮改动追加一行
- `OPEN-QUESTIONS.md`：五个 mode 共享的待解决问题清单

## 如何回滚

见 `env/SNAPSHOTS.md`。基线快照在 Mode 4 setup 时建立。
```

### 3.2 `AI-work/LOG.md`

```markdown
# AI-work Log

每次 skill 调用或重要改动追加一行。最新的写在最上面。

格式：`YYYY-MM-DD HH:MM | mode | 简述`

---

| 时间 | Mode | 简述 |
|---|---|---|
| <填写当前时间> | bootstrap | 创建 AI-work 骨架 |
```

### 3.3 `AI-work/OPEN-QUESTIONS.md`

```markdown
# Open Questions

五个 mode 共享的待解决问题。每条都标注来源 mode、提出时间、当前状态。

| 编号 | 提出时间 | 来源 mode | 问题 | 状态 | 解决依据 |
|---|---|---|---|---|---|
| Q1 | | | | open / in-progress / resolved | |

## 处理约定

- 任何 mode 在读取过程中遇到无法立即确认的事实，写一条带 `> ⚠️ 待确认` 的内容时，**必须**同时在这里追加一行。
- 状态从 open → resolved 时，留下解决依据（commit hash / 用户口头确认 / 仿真证据）。
- 长期 open 的问题（超过一周）在每周协作开始时复盘一次，决定继续追还是关掉。
```

### 3.4 `AI-work/.gitignore`

```gitignore
# AI-work runtime outputs — not source assets
sim_out/
reports/
*.wdb
*.jou
*.log
*.pb
*.vcd
xsim.dir/
.Xil/
vivado*.str
hw_ila_data_*/
```

`sim/`、`scripts/`、`env/`、`guide/`、`annotations/`、`features/*/*/*.md`、`features/*/*/sim/*.tcl`、`features/*/*/ila/*.tcl` 这些是协作资产，**进 git**。

`features/*/*/out/` 里哪些证据进 git 由项目规则决定：`result.txt`、小型 log、CSV 通常有价值；大型 `.wdb`、`.dcp`、`.bit` 通常不进 git，但路径和摘要必须写进 unit 文档。

## 4. Cross-mode 路由协议

每个 mode 必须把产出写到对应位置：

| Mode | 产出位置 |
|---|---|
| Whole-project map | `AI-work/guide/FPGA_PROJECT_GUIDE.md` 主文档 + `AI-work/guide/IP-INVENTORY.md` + `AI-work/guide/CLOCKS.md` + `AI-work/guide/diagrams/architecture.d2` 等 |
| Selected-path deep read | `AI-work/guide/data-paths/<path-slug>-deep-reading.md`，slug 用英文短横线（例如 `adc-to-ddr`、`dac-output`） |
| Single-file close read | 注释加在源文件原位（不在 AI-work 内复制源码），但在 `AI-work/annotations/<filename>.md` 里留一份说明 |
| Co-work setup | `AI-work/env/*.md` + `AI-work/scripts/*.tcl` + 项目级仿真 SOP |
| Feature development | `AI-work/features/<feature-slug>/<UNIT>/` 阶段式工作包；完成验证后把稳定事实回写 `AI-work/guide/data-paths/*_AS_BUILT.md` |

`OPEN-QUESTIONS.md` 在所有 mode 间共享，遇到不确定就追加。

## 5. 已存在 AI-work 时的处理

如果 `AI-work/` 已经存在（之前的 session 建立的）：

1. 不要覆盖。
2. 读 `LOG.md`、`OPEN-QUESTIONS.md` 恢复历史上下文。
3. 读 `env/FOCUS.md`（如果 Mode 4 跑过）恢复当前调试焦点。
4. 当前 mode 的产出**增量**写入对应目录，不删旧文件。
5. 在 `LOG.md` 追加一行说明本次 session 的工作。

## 6. 不该做的事

- 不要把 skill 产出散落在工程根目录或 `*.srcs/` 子目录里。
- 不要把新的仿真、综合、实现、bitstream、ILA 产物散落在 D 盘根目录或工程根目录；它们必须进入当前 unit 的 `out/` 或 Mode 4 的 `sim_out/`/`reports/`。
- 不要在 `AI-work/` 里复制工程源码副本（除非用户明确要求做隔离实验）。
- 不要把 `sim_out/`、`reports/`、`*.wdb`、`*.jou` 提交进 git。
- 不要在 `AI-work/` 里删除别的 mode 留下的文件。
- 不要把用户的私密信息（license、IP 加密 key、登录凭据）写进 `AI-work/`。
