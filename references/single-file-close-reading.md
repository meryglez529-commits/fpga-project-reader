# Single-File Close Reading and Annotation

Use this reference when the user names one RTL/source file and asks to read it, explain it, add comments, annotate it, or make it beginner-readable.

This mode may also produce a single-file version/diff reading note, such as comparing an old backup with the active file. It still does not authorize functional RTL edits unless the user explicitly asks for a fix and Mode 5 is active.

## Goal

Turn one source file into a readable teaching surface without changing behavior. The best comments help the reader build the right mental model before reading assignments and state machines.

## Teaching-First Rule

For beginner-facing RTL comments, prefer the explanation that would work in a live conversation.

Every major comment block should start with a plain sentence:

```text
<module/block> does one thing: <real-world job>.
```

Then answer `why` before `what`:

1. Why does this block exist?
2. What real-world objects are moving through it?
3. What are the units?
4. Which signals are just counters, addresses, enables, or temporary buffers?

Avoid comments that are technically correct but not useful to a novice, such as only naming the state machine or listing signal meanings. If the user would still ask "but why is it like this?", the comment is not finished.

## Workflow

1. **Locate the file in the data link.**
   Search for the module instantiation and for its key outputs. Identify upstream producer, downstream consumer, clock domain, reset, and whether the module is on the main business data path or a side-control path.

2. **State the real-world object.**
   Before describing signals, define what the module is really operating on:
   - a scan position, pixel, sample, lane, packet, burst, frame, command, or table entry;
   - whether the data is a continuous stream, a counted stream segment, or a stored block;
   - which signal creates the logical boundary, such as trigger, count limit, `last`, frame length, or address wrap.

3. **Separate dimensions.**
   FPGA files often mix several dimensions in one expression. Name them explicitly:
   - position count vs. channel count;
   - sample width vs. bus width;
   - byte count vs. word count;
   - valid data vs. padded/aligned data;
   - stream order vs. storage order.

4. **Explain packing from first principles.**
   If the module changes width or storage units, write the formula in comments:
   - how many real-world items fit in one bus beat;
   - how many bus beats form one storage word or packet;
   - why alignment or padding is needed;
   - what a partially used lane means.

5. **Comment section contracts, not syntax.**
   Add comments before module-level contracts, major always blocks, state machines, FIFO/CDC boundaries, packing/reordering logic, length calculations, and non-obvious magic constants. Avoid comments that merely restate the code, such as "assigns A to B".

6. **Use the oral explanation test.**
   Before editing the file, write or mentally rehearse a short explanation that would make the user understand the block in conversation. Convert that explanation into comments. Prefer "fdma_read_div reads historical frames from DDR and aligns them with the current frame" over "read DDR data and output average data".

7. **Prefer beginner-readable Chinese when the user is Chinese.**
   Use short paragraphs and concrete examples. It is fine to use terms like `64bit 包`, `128bit word`, `位置 i`, and `通道 ch` when the comment defines them locally.

8. **Clean comment readability.**
   If legacy comments are mojibake/乱码 and you can safely replace them, remove or replace them so the new guide is not interrupted. When file encoding is fragile, preserve functional bytes and edit carefully.

9. **Validate after editing.**
   At minimum verify:
   - `module`/`endmodule` counts are unchanged and sensible;
   - `begin`/`end` counts are balanced for the edited file;
   - key assignments and port names still exist;
   - searches for obvious mojibake in comments do not hit newly introduced guidance.

10. **Bridge to Mode 5 when needed.**
    If close reading reveals a bug, missing feature, stale annotation, or required behavior change, record the finding in `AI-work/annotations/` and recommend a Mode 5 work package. Do not silently fix behavior inside Mode 3.

## Comment Shape

Use a small numbered reading scaffold for complex files:

```verilog
//------------------------------------------------------------------------------
// 0. 读这个模块，先记住一句话
//
// <module> 做的事只有一件：
//   <plain-language real-world job>.
//
// 为什么要这样做？
//   <the design pressure: real-time stream, alignment, burst access, averaging, etc.>
//
// 先把单位记牢：
//   <unit A> = <concrete size>.
//   <unit B> = <concrete size>.
//------------------------------------------------------------------------------
```

Then place section comments before the major blocks:

```verilog
//------------------------------------------------------------------------------
// 2. <block name>: 这几个信号分别回答什么问题
//
// <signal A>：
//   <plain role, such as "next DDR byte address", not just "read address">。
//
// <signal B>：
//   <plain role plus unit>.
//
// 换一种说法：
//   <concrete example with small numbers>.
//------------------------------------------------------------------------------
```

Prefer comments that name the reader's likely confusion:

```verilog
// f1~f9 不是 ADC 通道，而是历史帧槽。
// 当前帧不进这些 FIFO，它通过 frame_data 实时参与平均。
```

## Good Annotation Pattern

For an ADC frame-length module, prefer comments like:

```verilog
// image_point_fdma 表示一帧里有多少个空间位置，通道数不改变位置数量；
// 通道数只改变“每个位置要携带几个 16bit 测量值”。
//
// adcdata_get 已经把这些 16bit 值打包成 64bit 流：
//   单通道：1 个 64bit 包 = 4 个连续位置。
//   双通道：1 个 64bit 包 = 2 个连续位置，每个位置 2 个通道值。
//   三/四通道：1 个 64bit 包 = 1 个位置，占 4 个 16bit 槽位。
```

This is better than:

```verilog
// calculate single_frame_rom
// channel selects shift amount
```

because it teaches the dimensions that make the shift amount inevitable.

For a DDR readback/average module, prefer comments like:

```verilog
// fdma_read_div 做的事只有一件：
//   从 DDR 读回历史帧，再把历史帧和正在流过来的当前帧对齐，送去平均。
//
// frame_num=N 表示 N 帧平均。
// 当前帧已经从 frame_data/frame_data_en 实时进来了，不需要从 DDR 读。
// DDR 只保存历史帧，所以 DDR 槽数 = N-1。
//
// f1~f9 不是 ADC 通道，而是最多 9 个历史帧槽的临时缓存。
```

This is better than:

```verilog
// read DDR data
// nine frame FIFO
// average output
```

because it explains the design reason: DDR returns historical frames serially, while the average block needs historical frames and the current frame aligned on the same beat.

## Final Explanation to User

After editing, summarize:

- what mental model the comments now establish;
- which likely beginner confusions the comments now answer;
- which file and sections were changed;
- what validation was run;
- whether functional RTL was untouched.

## Annotation Record Shape

Write a small record under `AI-work/annotations/`:

```markdown
# <file> close read / annotation

| 项 | 内容 |
|---|---|
| 源文件 | |
| 模块 | |
| 所属数据链路 | |
| 上游 | |
| 下游 | |
| 本次类型 | 教学注释 / 单文件解释 / 新旧 diff |
| 是否改功能 RTL | 否 / 是（若是，必须转 Mode 5） |
| 对应版本/时间 | |

## 一句话模型
## 本次改了什么注释或读出了什么差异
## 可能影响后续 Mode 5 的点
```
