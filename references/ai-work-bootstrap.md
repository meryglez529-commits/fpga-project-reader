# AI-work Bootstrap

`AI-work/` 是 fpga-cowork 的唯一协作产物根目录。每次触发任一模式时先确认它存在；缺失或骨架不完整就补齐，但不覆盖既有内容。

Mode 1 还会检查这个骨架是否已被真正填充、证据是否仍有效；仅有目录不表示工程已完成接手。

## 1. 确定工程根

按以下顺序判断：

1. 当前目录含 Vivado `*.xpr` 或 Quartus `*.qpf`；
2. 当前目录含创建工程的 Tcl（`create_project`）；
3. 当前目录或其父目录含 `*.srcs`、`*.sim`、`constrs_1` 等典型工程结构；
4. 仍不明确时，在 `OPEN-QUESTIONS.md` 记录，并以当前目录作为暂定根。

## 2. 最小骨架

```text
AI-work/
  README.md
  LOG.md
  OPEN-QUESTIONS.md
  .gitignore
  guide/
    data-paths/
    diagrams/
  annotations/
  env/
  features/
  scripts/
  reports/
    baseline/
```

空目录可用 `.gitkeep` 保留。不要在 `AI-work/` 复制工程源码；源文件始终留在原工程位置。

## 3. 目录约定

| 位置 | 内容 |
|---|---|
| `guide/` | Mode 1 工程地图、主通路精读、时钟/IP 清单和验证后的 as-built 文档 |
| `annotations/` | Mode 2 注释清单、依赖闭包、编码/换行和差异记录 |
| `env/` | Mode 1 的环境、硬件、仿真、能力、规则、快照、术语和状态 |
| `features/<feature>/<UNIT>/` | Mode 3 的唯一开发与板级调试工作包；含 `sim/`、`ila/`、`out/` 等 |
| `scripts/` | 项目级、可复现的基础检查/隔离构建/无副作用硬件盘点脚本 |
| `reports/baseline/<baseline-id>/` | Mode 1 的工具、仿真、综合、实现、bitstream、debug 证据 |

## 4. 顶层最小内容

`README.md` 说明这是协作目录及当前权威入口。`LOG.md` 每行记录一次有意义的状态变化。`OPEN-QUESTIONS.md` 记录来源、时间、状态和证据。`.gitignore` 至少忽略大体积或可再生的运行产物：

```gitignore
*.wdb
*.jou
*.log
*.pb
*.vcd
*.dcp
*.bit
xsim.dir/
.Xil/
hw_ila_data_*/
```

是否将小型报告、CSV 或脚本纳入版本控制，由项目规则决定；无论是否提交，它们都必须留在 `AI-work/`。

## 5. 跨模式规则

- Mode 1：填充 `guide/`、`env/`、`scripts/` 和 `reports/baseline/`，不改设计。
- Mode 2：只在用户要求注释时修改原始源码中的注释；所有说明和验证记录进入 `annotations/`。
- Mode 3：每个具体功能/调试问题先建立一个 feature unit；所有 AI 新建数据都写入该 unit。只有用户明确授权的设计源/约束/IP/工程改动可以留在原工程位置。

已有 `AI-work/` 时，先读 `LOG.md`、`OPEN-QUESTIONS.md` 和 `env/SETUP_STATUS.md`（若存在），增量更新，不删除或覆盖其它会话的文件。
