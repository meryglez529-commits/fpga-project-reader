# Output Format

Create a Markdown guide named like `FPGA_PROJECT_GUIDE.md` unless the user specifies another file.

## Required Structure

```markdown
# FPGA Project Guide — [project name]

## 目录

## 0. 总体结论
## 1. 工程入口与系统边界
## 2. 时钟与复位
## 3. 工程总体架构图
## 4. 模块层级关系
## 5. 主数据链路
### 5.1 主数据链路识别结论
### 5.2 数据链路 1 — [name]
### 5.3 数据链路 2 — [name]
### 5.x 其他链路或支撑链路
## 6. 控制通路
## 7. 存储与缓冲
## 8. 验证与上板
## 9. 需要深入阅读的关键文件
## 10. 待确认问题与风险
## 11. 下一步阅读路线
```

Do not predeclare how many main links exist. Add as many `5.x` subsections as the project actually needs.

## Required Tables

### 工程入口表

| 项目 | 结论 |
|---|---|
| 工程文件 | |
| 顶层模块 | |
| 顶层文件 | |
| 器件型号 | |
| 主要源码目录 | |
| 主要约束文件 | |
| 仿真入口 | |

### 系统边界表

| 接口类别 | 外部信号 | 方向 | 连接外设 | 主/支撑 | 服务的数据链路 |
|---|---|---|---|---|---|

### 时钟域表

| 时钟 | 来源 | 频率 | 覆盖模块 | 服务的数据链路 | CDC 风险 |
|---|---|---|---|---|---|

### 主数据链路表

| 链路编号 | 主链路依据 | 吞吐量估算 | 数据源 | 主要模块路径 | 数据终点 | 数据类型 | 备注 |
|---|---|---|---|---|---|---|---|

### 控制通路表

| 控制信号/状态机 | 来源类型 | 来源模块 | 作用位置 | 约束的数据链路 | 说明 |
|---|---|---|---|---|---|

### 存储缓冲表

| 存储结构 | 所在模块 | 服务的数据链路 | 解决的问题 |
|---|---|---|---|

### 验证资源表

| 资源 | 文件/模块 | 对应数据链路 | 用途 |
|---|---|---|---|

### 关键文件表

| 优先级 | 文件 | 需要重点看的内容 |
|---|---|---|

## Risk Handling

Use `> ⚠️ 待确认` for black boxes, missing sources, unclear clock frequencies, ambiguous business semantics, inferred sample rates, or endpoints inside unexpanded IP. Collect every such item in section 10.

Section 10 should separate confirmed evidence from residual uncertainty:

```markdown
## 10. 待确认问题与风险

本轮已从当前工程确认：

| 问题 | 结论 | 证据文件 | 可信度 |
|---|---|---|---|
| `ui_clk` 频率 | 200 MHz | `.../system.v:2137` | 高 |

> ⚠️ 待确认：...
```

Evidence files should include paths and line numbers when practical. If a fact is inferred from several files, say so explicitly and keep the confidence lower than a direct configuration or constraint.
