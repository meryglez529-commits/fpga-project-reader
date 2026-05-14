# DAC 输出链路代码阅读指导手册

这份文档的目标不是替你总结 RTL，而是带你打开真实代码，一步一步读懂 DAC 通路。读的时候请把文档和源码并排放：文档告诉你“现在看哪个文件、搜什么关键字、哪些信号是主线、哪些先不要管”。

## 0. 使用方法

这份手册按成熟 FPGA 工程师读输出链路的顺序写。第一遍不要从寄存器源头开始，因为 `command_monitor_new` 里混有 ADC、图像、RTM、升级、状态回读等大量非 DAC 主线内容。第一遍先从最终 DAC 管脚和最后一级输出锁存开始，拿到上游必须满足的数据合同，然后再回头看谁在生产这个合同。

推荐阅读顺序如下：

| Pass | 打开文件 | 本轮只解决的问题 |
|---:|---|---|
| 1 | `ETH_TOP.v` | DAC 主输出到底是哪几个管脚？内部真正要追的 X/Y 数据名是什么？ |
| 2 | `scan_top.v` | 顶层 `DAX_DATA/DAY_DATA` 从哪个子模块出来？主点流从哪里进来？ |
| 3 | `dac_output.v` | DAC 数据在哪个时钟域锁存？34-bit 数据包怎么拆成 X/Y？ |
| 4 | `gen_data_mux.v` | 谁在写 `para_config_data[33:0]`？普通扫描/加工/单点怎么汇流？ |
| 5 | `image_gen_top.v`、`parameter_dacdata_gen.v` | 普通扫描如何生成 `scan_data[33:0]`？ |
| 6 | `mill_gen_top.v`、`mill_controller.v` | 加工路径如何生成 `mill_data[32:0]`？ |
| 7 | `command_monitor_new.v` | 上位机寄存器如何变成扫描参数和 `spot_data`？ |
| 8 | FIFO IP、`ad9747_cfg.v` | CDC、blanker、DAC 芯片配置这些支撑项是否合理？ |

读每个模块时都按同一个节奏：

1. 先看“本步目标”，不要试图读完整文件。
2. 按“搜索入口”在源码里定位。
3. 对照“本模块 DAC 相关信号”表，只看表里的信号。
4. 按“代码阅读顺序”读局部代码。
5. 用“读完应能回答”检查自己是否读通。
6. 再进入“下一步”指定的模块。

## 1. 先建立最小心智模型

DAC 主通路最终做的事很简单：

```text
FPGA 生成一串 X/Y 数字点
  -> 在 dac_dco 域锁存
  -> 顶层做互补映射
  -> dac_p1d/dac_p2d 输出到 AD9747
```

这条链路里最重要的三个名字是：

| 名字 | 先怎么理解 |
|---|---|
| `DAX_DATA` | FPGA 内部 X 方向 DAC 点 |
| `DAY_DATA` | FPGA 内部 Y 方向 DAC 点 |
| `para_config_data[33:0]` | 上游写给输出 FIFO 的 34-bit 主数据包 |

34-bit 主数据包是：

```text
para_config_data[33:0] = {frame_end, adc_tri, DAX_DATA[15:0], DAY_DATA[15:0]}
```

先记住位段：

| 位段 | 含义 |
|---|---|
| `[33]` | `frame_end`，帧结束标记 |
| `[32]` | `adc_tri`，有效采样/束闸相关标记 |
| `[31:16]` | X 方向 DAC 点 |
| `[15:0]` | Y 方向 DAC 点 |

真实数据生产方向是：

```text
command_monitor_new 参数
  -> image_gen_top/parameter_dacdata_gen 或 mill_gen_top 或 spot_data
  -> gen_data_mux 汇流
  -> para_config_data[33:0]
  -> scan_top
  -> dac_output
  -> DAX_DATA/DAY_DATA
  -> dac_p1d/dac_p2d
```

但第一次打开代码的阅读方向建议反过来：

```text
dac_p1d/dac_p2d
  <- DAX_DATA/DAY_DATA
  <- scan_top
  <- dac_output
  <- para_config_data[33:0]
  <- gen_data_mux
  <- 具体来源和寄存器
```

## 2. 第一步：打开 `ETH_TOP.v`

文件：`fpga_prj/AXI_DDR.srcs/sources_1/new/ETH_TOP.v`

本步目标：确认主 DAC 输出边界，找出内部真正要追的 X/Y 信号。

搜索入口：

```text
dac_p1d
dac_p2d
DAX_DATA
DAY_DATA
scan_top U6
gen_data_mux U13
command_monitor_new U4
ad9747_cfg
```

本模块 DAC 相关信号：

| 类别 | 信号/实例 | 你要理解的作用 |
|---|---|---|
| 外部 DAC 数据口 | `dac_p1d[15:0]`、`dac_p2d[15:0]` | AD9747 主并行数据从这里出 FPGA |
| 外部 DAC 时钟 | `dac_dco` | 输出锁存侧时钟，后面要确认数据在这个域更新 |
| 内部 X/Y 点 | `DAX_DATA`、`DAY_DATA` | 顶层内部真正要追的 DAC 点 |
| 顶层输出映射 | `assign dac_p1d = 65535 - DAX_DATA`、`assign dac_p2d = 65535 - DAY_DATA` | 出 FPGA 前做互补映射 |
| 输出链路实例 | `scan_top U6` | `DAX_DATA/DAY_DATA` 从这里返回顶层 |
| 主点流来源实例 | `gen_data_mux U13` | 产生 `para_config_wr_en/para_config_data`，送给 `scan_top` |
| 参数源实例 | `command_monitor_new U4` | 上位机写寄存器后的 DAC 参数从这里出来 |
| DAC 配置实例 | `ad9747_cfg U1` | 配置 AD9747 SPI/复位/增益，不承载主点流 |

先忽略：

| 先忽略 | 原因 |
|---|---|
| `adc*`、`adcdata_config*`、DDR、`fdma*` | ADC 图像回传链路，不是 DAC 主输出 |
| `sfp_*`、RTM、Aurora 相关 | 高速触发/回传支撑，不直接生成 `dac_p1d/p2d` |
| `fram_cfg`、`offset_dac_cfg` | 校准/偏置支撑，不是 AD9747 主点流 |
| `multiboot*`、QSPI | 远程升级 |
| `ad9747_cfg` 的 SPI 细节 | 先只知道它配置芯片，不传 X/Y 点 |

代码阅读顺序：

1. 先看顶层端口里的 `dac_p1d/dac_p2d/dac_dco`。
2. 搜 `DAX_DATA/DAY_DATA`，看它们怎样赋给 `dac_p1d/dac_p2d`。
3. 搜 `scan_top U6`，确认 `DAX_DATA/DAY_DATA` 是 `scan_top` 的输出。
4. 在 `scan_top U6` 附近看 `fifo_wr_en/fifo_wr_data` 接到谁。
5. 搜 `gen_data_mux U13`，确认 `para_config_wr_en/para_config_data` 来自 mux。
6. 只扫一眼 `command_monitor_new U4` 输出了哪些 DAC 参数，不要在这里展开寄存器。

读完应能回答：

```text
AD9747 主数据来自 dac_p1d/dac_p2d。
dac_p1d/p2d 由 DAX_DATA/DAY_DATA 互补映射得到。
DAX_DATA/DAY_DATA 来自 scan_top，scan_top 的主点流来自 gen_data_mux。
```

下一步：打开 `scan_top.v`，确认 `DAX_DATA/DAY_DATA` 在哪里产生。

## 3. 第二步：打开 `scan_top.v`

文件：`fpga_prj/AXI_DDR.srcs/sources_1/new/scan_top.v`

本步目标：确认 `scan_top` 只是包装层，真正的输出锁存和 CDC 在 `dac_output`。

搜索入口：

```text
module scan_top
fifo_wr_en
fifo_wr_data
DAX_DATA
DAY_DATA
dac_output N2
rstn_r2
mill_state_adj
```

本模块 DAC 相关信号：

| 类别 | 信号 | 你要理解的作用 |
|---|---|---|
| 写侧时钟/复位 | `eth_clk`、`eth_rstn` | `scan_top` 外层和写侧控制在 `eth_clk` 域 |
| 输出侧时钟 | `dac_dco` | 传给 `dac_output`，后面在这个域锁存 DAC 点 |
| 主点流输入 | `fifo_wr_en`、`fifo_wr_data[33:0]` | 从 `gen_data_mux` 进来的 34-bit 点流 |
| FIFO 反压输出 | `fifo_prog_full_out`、`fifo_wr_busy_out` | 返回上游，告诉上游 FIFO 快满或写复位忙 |
| DAC 点输出 | `DAX_DATA`、`DAY_DATA` | 接回 `ETH_TOP`，最终驱动 `dac_p1d/p2d` |
| 同步辅助输出 | `adc_tri`、`frame_end_sig`、`blanker_sig` | 和 DAC 点同步的采样/帧尾/束闸辅助 |
| 扫描启动复位 | `scan_state_r0`、`rstn_r0`、`rstn_cnt`、`rstn_r2` | `scan_state` 启动时给下游 FIFO/输出链路一个复位窗口 |
| 加工状态保持 | `mill_state_adj` | `mill_state==0` 时保持上一次非零加工状态 |
| 子模块 | `dac_output N2` | 真正做 FIFO、跨时钟和 `DA1/DA2` 锁存 |

先忽略：

| 先忽略 | 原因 |
|---|---|
| 注释掉的旧复位逻辑 | 当前有效逻辑是后面的 `rstn_cnt` 版本 |
| 历史 DAC/校准接口注释 | 当前没有接入主点流 |
| `fifo_rd_en` 相关注释 | 现在读使能在 `dac_output` 内部产生 |

代码阅读顺序：

1. 看端口，确认 `fifo_wr_data[33:0]` 进来，`DAX_DATA/DAY_DATA` 出去。
2. 看 `rstn_r2` 生成逻辑，知道扫描启动时下游会被延迟释放。
3. 看 `mill_state_adj`，知道加工状态不是简单透传。
4. 看 `dac_output N2` 例化：`DA1_DATA -> DAX_DATA`，`DA2_DATA -> DAY_DATA`。
5. 看 `para_config_wr_en/data` 如何由 `fifo_wr_en/data` 传给 `dac_output`。

读完应能回答：

```text
scan_top 本身不生成 X/Y 波形。
它把 gen_data_mux 的 34-bit 点流送进 dac_output，再把 dac_output 的 DA1/DA2 接成 DAX/DAY。
```

下一步：打开 `dac_output.v`，确认最后一级输出锁存和 34-bit 拆包。

## 4. 第三步：打开 `dac_output.v`

文件：`fpga_prj/AXI_DDR.srcs/sources_1/new/dac_output.v`

本步目标：这是 DAC 主通路最重要的模块。你要确认三件事：34-bit 数据包怎么跨时钟、怎么拆成 X/Y、FIFO 空时输出怎么处理。

搜索入口：

```text
DA1_DATA
DA2_DATA
para_config_data
para_config_dout
fifo_generator_4
para_config_rd_en
scan_mode_sync
sync_fifo_9bit
fifo_generator_2
blanker_sig
```

本模块 DAC 相关信号：

| 类别 | 信号 | 你要理解的作用 |
|---|---|---|
| 写侧输入 | `ui_clk`、`para_config_wr_en`、`para_config_data[33:0]` | 上游在 `eth_clk` 域写入 34-bit 点 |
| 读侧时钟 | `dac_dco` | DAC 点在这个时钟域读出并锁存 |
| 主 FIFO | `fifo_generator_4` | 34-bit 主点流从 `eth_clk` 跨到 `dac_dco` |
| FIFO 输出 | `para_config_dout[33:0]` | 跨域后的数据包 |
| 读使能 | `para_config_rd_en`、`para_config_rd_en_r` | 控制何时从 FIFO 读一个点，以及下一拍何时拆包 |
| 空/满/忙 | `para_config_prog_full`、`para_config_prog_empty`、`para_config_wr_rst_busy`、`para_config_rd_rst_busy` | 上下游反压和复位忙状态 |
| 输出锁存 | `DA1_DATA`、`DA2_DATA` | 最终送回 `scan_top` 的 X/Y DAC 点 |
| 同步标记 | `adc_tri`、`frame_end_sig` | 从 bit `[32]`、`[33]` 拆出来的同步信息 |
| 控制跨域 | `sync_fifo_9bit`、`scan_mode_sync`、`mill_mode_sync`、`dac_rstn` | mode/reset 从 `eth_clk` 带到 `dac_dco` |
| blanker 支路 | `fifo_generator_2`、`middle_sig`、`blanker_sig` | 与点流同步的束闸辅助，不改变 X/Y 数值 |

先忽略：

| 先忽略 | 原因 |
|---|---|
| ILA probe 扩展细节 | 只是调试观察点 |
| blanker 延迟计数细节 | 第一遍先把 X/Y 数值链读通 |
| `adc_tri` 上升/下降沿派生逻辑 | 属于束闸时序细节，不是 DAC 数值 |

代码阅读顺序：

1. 看 `fifo_generator_4` 例化，确认 `.wr_clk(ui_clk)`、`.rd_clk(dac_dco)`、`.din(para_config_data)`、`.dout(para_config_dout)`。
2. 看 `para_config_rd_en` 生成逻辑，确认只有 mode 允许且 FIFO 非空时才读。
3. 看 `para_config_rd_en_r` 那个 always，确认下一拍拆包：

   ```text
   frame_end_sig_sync <= para_config_dout[33]
   adc_tri_sync       <= para_config_dout[32]
   DA1_DATA           <= para_config_dout[31:16]
   DA2_DATA           <= para_config_dout[15:0]
   ```

4. 看 FIFO 空时 `DA1_DATA <= DA1_DATA`、`DA2_DATA <= DA2_DATA`，确认没新点时保持旧 DAC 值。
5. 最后再扫 `sync_fifo_9bit` 和 `fifo_generator_2`，知道它们分别服务 mode/reset 和 blanker。

读完应能回答：

```text
上游必须写 para_config_wr_en + para_config_data[33:0]。
bit[31:16] 最终变成 DA1/DAX，bit[15:0] 最终变成 DA2/DAY。
最后一级 X/Y 数据在 dac_dco 域更新。
```

下一步：打开 `gen_data_mux.v`，找谁在写 `para_config_data[33:0]`。

## 5. 第四步：打开 `gen_data_mux.v`

文件：`fpga_prj/AXI_DDR.srcs/sources_1/new/gen_data_mux.v`

本步目标：确认普通扫描、加工扫描、单点三路数据如何汇成同一条 `para_config_data[33:0]`。

搜索入口：

```text
scan_data
mill_data
spot_data
para_config_data
para_config_wr_en
para_prog_full
para_wr_rst_busy
scan_mode
mill_state_adj
image_gen_top
mill_gen_top
```

本模块 DAC 相关信号：

| 类别 | 信号 | 你要理解的作用 |
|---|---|---|
| 普通扫描输入 | `scan_data_wr_en`、`scan_data[33:0]` | 来自 `image_gen_top/parameter_dacdata_gen` 的普通扫描点 |
| 加工输入 | `mill_data_wr_en`、`mill_data[32:0]` | 来自 `mill_gen_top` 的加工图元点 |
| 单点输入 | `spot_data[31:0]` | `scan_mode==2` 时直接作为 `{DAX,DAY}` |
| 主输出 | `para_config_wr_en`、`para_config_data[33:0]` | 输出给 `scan_top/dac_output` 的唯一主点流 |
| 下游反压 | `para_prog_full`、`para_wr_rst_busy` | 下游 FIFO 快满/写复位忙时，不能继续写 |
| 模式选择 | `scan_mode`、`mill_state_adj` | 决定当前选普通扫描、加工还是单点 |
| blanker 汇流 | `blk_mid_sig_o`、`blk_mid_sig_mill`、`blk_mid_sig`、`start_dly`、`end_dly` | 与点流同步的束闸辅助 |
| 支路实例 | `image_gen_top_inst`、`mill_gen_top_inst` | 普通扫描和加工扫描的点来源 |

先忽略：

| 先忽略 | 原因 |
|---|---|
| `image_gen_top` 内部状态机 | 下一步单独读 |
| `mill_gen_top` 每种图元算法 | 加工支路后面单独读 |
| `mill_progress` | 状态回报，不改变 DAC 数值 |

代码阅读顺序：

1. 先看内部 wire：`scan_data[33:0]`、`mill_data[32:0]`、`spot_data[31:0]`。
2. 看 `image_gen_top_inst` 输出 `scan_data_wr_en/scan_data`。
3. 看 `mill_gen_top_inst` 输出 `mill_data_wr_en/mill_data`。
4. 最后看主 always 的四个分支：

   ```text
   scan_mode == 2
     -> para_config_data = {1'b0, spot_data}

   scan_mode[0] || scan_mode[1] || scan_mode == 5
     -> para_config_data = scan_data

   scan_mode[3] && mill_state_adj != 2 && mill_state_adj != 3
     -> para_config_data = mill_data

   else
     -> para_config_data = {2'd0, scan_data[31:0]}
   ```

5. 看每个分支的 `para_config_wr_en` 是否受对应支路 `wr_en` 或 FIFO 反压影响。

读完应能回答：

```text
gen_data_mux 是主点流唯一汇流点。
不管普通扫描、加工还是单点，最后都必须变成 para_config_wr_en + para_config_data[33:0]。
```

下一步：如果你关心普通扫描，进入 `image_gen_top.v` 和 `parameter_dacdata_gen.v`；如果你关心加工，跳到第 7 章。

## 6. 第五步：普通扫描支路

普通扫描路径是：

```text
gen_data_mux
  -> image_gen_top
  -> parameter_dacdata_gen
  -> scan_data[33:0]
  -> gen_data_mux
```

### 6.1 打开 `image_gen_top.v`

文件：`fpga_prj/AXI_DDR.srcs/sources_1/new/image_gen_top.v`

本步目标：确认 `image_gen_top` 只是普通扫描包装层，真正产点在 `parameter_dacdata_gen`。

搜索入口：

```text
module image_gen_top
parameter_dacdata_gen N1
dac_sample
dacx_strat_level
dacy_strat_level
triangle_scan
single_frame_mode
rstn_r2
para_config_data
```

本模块 DAC 相关信号：

| 类别 | 信号 | 你要理解的作用 |
|---|---|---|
| 普通扫描参数 | `dac_sample`、`image_row`、`image_row_cut` | 控制点节拍和行数 |
| X 参数 | `dacx_strat_level`、`dacx_end_level`、`dacx_step`、`dacx_tk_point`、`dacx_recovery_time` | 传给点生成器，决定 X 波形 |
| Y 参数 | `dacy_strat_level`、`dacy_end_level`、`dacy_step` | 传给点生成器，决定 Y 行进 |
| 模式解释 | `triangle_scan = scan_mode[4]`、`single_frame_mode = scan_mode[1:0]==2'b11` | 转成点生成器需要的普通扫描模式 |
| 启动复位 | `scan_state_r0`、`rstn_r0`、`rstn_r1`、`rstn_r2` | `scan_state` 启动后重新释放点生成器 |
| 子模块 | `parameter_dacdata_gen N1` | 真正生成 `DAX/DAY/adc_tri/frame_end` |
| 输出回 mux | `para_config_wr_en`、`para_config_data`、`blk_mid_sig` | 普通扫描输出给 `gen_data_mux` |

先忽略：

| 先忽略 | 原因 |
|---|---|
| VIO/调试注释 | 不影响主链路 |
| `start_dly_test/end_dly_test` 一类调试残留 | 当前不是主点流 |

代码阅读顺序：

1. 看端口，确认输入都是普通扫描参数，输出是 `para_config_wr_en/para_config_data`。
2. 看 `triangle_scan`、`single_frame_mode` 两个 assign。
3. 看 `rstn_r2` 复位延时。
4. 看 `parameter_dacdata_gen N1` 例化，确认参数全部传进去。

特别注意：

```text
image_gen_top.v 端口把 para_config_data 声明成 [32:0]，
parameter_dacdata_gen.v 输出是 [33:0]。
这可能截断 frame_end bit，需要综合 warning 或仿真确认。
```

读完应能回答：

```text
image_gen_top 不直接计算 X/Y 点，它把普通扫描参数和模式包装后交给 parameter_dacdata_gen。
```

下一步：打开 `parameter_dacdata_gen.v`。

### 6.2 打开 `parameter_dacdata_gen.v`

文件：`fpga_prj/AXI_DDR.srcs/sources_1/new/parameter_dacdata_gen.v`

本步目标：确认普通扫描如何从参数变成一串 `{frame_end, adc_tri, DAX, DAY}`。

搜索入口：

```text
para_config_data
dax_level
day_level
DAX_DATA
DAY_DATA
adc_tri
frame_end_sig
para_config_wr_en
current_state
16'h8000
```

本模块 DAC 相关信号：

| 类别 | 信号 | 你要理解的作用 |
|---|---|---|
| 输入参数 | `dac_sample`、X/Y 起止、X/Y step、行列、裁剪窗口 | 决定普通扫描点怎么走 |
| 内部定点电平 | `dax_level[63:0]`、`day_level[63:0]` | 真正累加/回扫/行进的是 64-bit 定点值 |
| 输出 DAC 值 | `DAX_DATA = dax_level[63:48]`、`DAY_DATA = day_level[63:48]` | 取高 16 位作为 DAC 点 |
| 同步标记 | `adc_tri`、`frame_end_sig` | 打包进 bit `[32]`、`[33]` |
| 主输出包 | `para_config_data = {frame_end_sig, adc_tri, DAX_DATA, DAY_DATA}` | 普通扫描支路回到 34-bit 合同 |
| 写使能 | `para_config_wr_en` | 表示当前状态写出一个点 |
| 下游反压 | `para_config_prog_full`、`para_config_wr_rst_busy` | FIFO 不可写时停止产点 |
| 状态机 | `current_state` | 控制初始化、回扫、有效扫描、行进、帧等待 |
| blanker 辅助 | `blk_mid_sig` | 和 DAC 点同步的束闸辅助，不是 X/Y 数值 |

先忽略：

| 先忽略 | 原因 |
|---|---|
| `div_gen_*` IP 细节 | 第一遍只需知道它们给 step/cycle/fall step |
| 完整状态机每个分支 | 第一遍先抓会写 `DAX/DAY` 的状态 |
| ILA probe | 调试观察点 |

代码阅读顺序：

1. 先看 `assign para_config_data = {frame_end_sig, adc_tri, DAX_DATA, DAY_DATA}`。
2. 看 `dax_level/day_level` 和 `DAX_DATA/DAY_DATA` 的关系。
3. 找 `para_config_prog_full==0 && para_config_wr_rst_busy==0` 的分支，确认只有下游可写时才 `para_config_wr_en <= 1`。
4. 初读只抓这些状态：

   | 状态 | 初读含义 |
   |---|---|
   | `0/1` | 初始化 X/Y 起始电平 |
   | `2` | X 回扫/等待段，`adc_tri=0` |
   | `3` | 有效扫描点，可能 `adc_tri=1` |
   | `4~10` | X/Y 行进、重复、隔行、剩余行处理 |
   | `11` | 帧等待，`frame_end_sig=1` |
   | `16` | 单帧结束后输出中点 `16'h8000` |

读完应能回答：

```text
普通扫描支路最终也生产同一个 34-bit 主数据包。
DAX/DAY 来自 64-bit 定点电平的高 16 位。
```

下一步：回到 `gen_data_mux`，确认 `scan_mode` 何时选择 `scan_data`。

## 7. 第六步：加工和单点支路

### 7.1 打开 `mill_gen_top.v` 和 `mill_controller.v`

文件：

```text
fpga_prj/AXI_DDR.srcs/sources_1/new/mill_gen_top.v
fpga_prj/AXI_DDR.srcs/sources_1/new/mill_controller.v
```

本步目标：确认加工图元最后也会变成 `{adc_tri,DAX,DAY}`，并回到 `gen_data_mux` 的 `mill_data`。

搜索入口：

```text
module mill_gen_top
mill_controller
pattern_data
pattern_data_valid
pattern_mode
mill_state
mill_mode
mill_submode
para_config_wr_en
para_config_data
line_config_data
rectangle_config_data
trapeze_config_data
ring_config_data
```

本模块 DAC 相关信号：

| 类别 | 信号 | 你要理解的作用 |
|---|---|---|
| 图元输入 | `pattern_data[223:0]`、`pattern_data_valid`、`pattern_number`、`pattern_mode` | 加工图元和加工方式从这里进入 |
| 加工控制 | `mill_state`、`mill_start/stop/pause/continue` | 控制加工启停暂停 |
| 图元缓存 | `blk_mem_pattern_data` | 图元参数先写 RAM，再按地址读出 |
| 模式选择 | `mill_mode`、`mill_submode` | 决定线、截面、梯形、圆环等子算法 |
| 子算法输出 | `line_config_data`、`rectangle_config_data`、`clean_config_data`、`trapeze_config_data`、`ring_config_data` | 各图元算法最终都输出 33-bit 点包 |
| 汇总输出 | `para_config_wr_en`、`para_config_data[32:0]` | 加工支路回到 `gen_data_mux` 的 `mill_data` |
| 辅助输出 | `blk_mid_sig`、`mill_progress` | blanker/进度支撑，不是主 X/Y 数值 |

先忽略：

| 先忽略 | 原因 |
|---|---|
| 每种图元内部插点算法 | 第一遍只确认最终输出 `{adc_tri,DAX,DAY}` |
| bitmap 注释块 | 当前主路径不是它 |
| `mill_progress` 展开细节 | 状态回报，不改变 DAC 点值 |

代码阅读顺序：

1. 在 `mill_gen_top` 看端口：输出是 `para_config_wr_en` 和 `para_config_data[32:0]`。
2. 找 `mill_controller` 例化，确认它汇总各图元算法。
3. 在 `mill_controller` 搜 `case(mill_mode)`。
4. 只看各分支如何选择：

   ```text
   mill_mode == 1 -> line_config_data
   mill_mode == 2 -> rectangle/clean config data
   mill_mode == 3 -> trapeze_config_data
   mill_mode == 4 -> ring_config_data
   ```

5. 回到 `gen_data_mux`，看 `scan_mode[3]` 分支如何把 `mill_data` 补成 34-bit 主点流。

读完应能回答：

```text
加工支路不是另一条 DAC 出口。
它只是另一种点生成来源，最后仍然回到 gen_data_mux -> para_config_data[33:0]。
```

下一步：读 7.2 单点支路，确认 `spot_data` 如何回到同一条主点流合同。

### 7.2 单点支路：`spot_data`

单点支路跨两个文件读：

| 文件 | 看什么 |
|---|---|
| `command_monitor_new.v` | `spot_data <= wr_reg_data[31:0]`，地址 `0x003A` |
| `gen_data_mux.v` | `scan_mode[3:0]==2` 时 `para_config_data <= {1'b0, spot_data}` |

本支路 DAC 相关信号：

| 信号 | 含义 |
|---|---|
| `spot_data[31:16]` | 单点 X/DAX |
| `spot_data[15:0]` | 单点 Y/DAY |
| `{1'b0, spot_data}` | 补成 33-bit 后进入 34-bit `para_config_data`，控制高位为 0 |
| `scan_mode[3:0]==2` | 选择单点输出 |
| `para_prog_full` | FIFO 满时停止写单点 |

读完应能回答：

```text
单点不跑普通扫描状态机，也不跑加工图元算法。
它是上位机直接写一个 {DAX,DAY}，由 gen_data_mux 写进同一条 DAC FIFO。
```

## 8. 第七步：最后打开 `command_monitor_new.v`

文件：`fpga_prj/AXI_DDR.srcs/sources_1/new/command_monitor_new.v`

本步目标：只读会影响 DAC 点流的寄存器和参数。这里是参数源，不是最终输出链路。

搜索入口：

```text
wr_reg_addr
dac_sample
dacx_strat_level
dacx_end_level
dacy_strat_level
dacy_end_level
dacx_step
dacy_step
scan_mode
scan_state
mill_state
row_repeat
row_m
row_n
spot_data
start_dly
end_dly
blank_en
left_cut
right_cut
up_cut
down_cut
step_module
```

本模块 DAC 相关信号：

| 类别 | 信号 | 你要理解的作用 |
|---|---|---|
| 写入口 | `wr_reg_valid`、`wr_reg_addr`、`wr_reg_data` | 上位机参数写入入口 |
| 点节拍 | `dac_sample` | 一个 DAC 点保持/重复多少节拍 |
| X 范围 | `dacx_strat_level`、`dacx_end_level`、`dacx_tk_point`、`dacx_recovery_time` | 普通扫描 X 方向范围和回扫 |
| X step | `dacx_step_flag`、`dacx_step`、`step_module dax_step_module` | 起止电平和点数计算出 64-bit 定点步进 |
| Y 范围 | `dacy_strat_level`、`dacy_end_level`、`image_row/image_column` | 普通扫描 Y 方向范围和行列 |
| Y step | `dacy_step_flag`、`dacy_step`、`step_module day_step_module` | Y 方向 64-bit 定点步进 |
| 模式/启停 | `scan_mode`、`scan_state`、`mill_state` | 决定 `gen_data_mux` 选哪一路 |
| 行控制 | `row_repeat`、`row_m`、`row_n` | 行重复和隔行扫描 |
| 裁剪窗口 | `left_cut/right_cut/up_cut/down_cut`、`left_level/right_level/up_level/down_level` | 影响 `adc_tri` 有效窗口和扫描边界 |
| 单点 | `spot_data` | 单点模式直接进入 `gen_data_mux` |
| blanker | `start_dly`、`end_dly`、`blank_en` | 束闸时序辅助，不改变 `DAX/DAY` |
| DAC 配置支撑 | `dacx_gain`、`dacy_gain` | 给 AD9747 配置/增益支撑，不是主点流 |

先忽略：

| 先忽略 | 原因 |
|---|---|
| `adc_len_single`、`adc_channel`、`adc_sample`、ADC gain | ADC 采集链路 |
| `image_bc_*`、contrast/brightness/gamma | 图像处理 |
| RTM、packet loss、PC packet num | 回传/状态统计 |
| `remote_rstn`、heartbeat、version | 控制维护 |
| 读寄存器回包的大部分 `rd_reg_data` | 第一遍只需写参数如何影响 DAC |

DAC 相关寄存器先按这个顺序看：

| 地址 | 字段/信号 | 影响 |
|---|---|---|
| `0x0009` | `scan_mode`、`scan_state`、`mill_state` | 先决定走普通扫描、加工、单点还是停止 |
| `0x0002` | `dac_sample` | 点节拍 |
| `0x0005` | `dacx_strat_level/end_level` | X 起止 |
| `0x0006` | `dacx_tk_point`、`dacx_recovery_time` | X 点数和回扫，触发 `dacx_step_flag` |
| `0x0007` | `dacy_strat_level/end_level` | Y 起止，触发 `dacy_step_flag` |
| `0x0004` | `image_row/image_column` | 图像/扫描尺寸，也影响 Y step 和裁剪尺寸 |
| `0x0013` | `row_repeat` | 行重复 |
| `0x0014` | `row_m/row_n` | 隔行扫描 |
| `0x0015` | `start_dly/end_dly/blank_en` | blanker 辅助时序 |
| `0x003A` | `spot_data` | 单点 `{DAX,DAY}` |
| `0x0071/0x0072` | `left/right/up/down_cut` | 裁剪窗口，进一步算 `left/right/up/down_level` |

代码阅读顺序：

1. 先看端口里的 DAC 参数输出，不看全部端口。
2. 搜 `case (wr_reg_addr)`，只读上表这些地址。
3. 搜 `step_module`，确认 `dacx_step/dacy_step` 从起止电平和点数/行数计算出来。
4. 搜 `left_level/right_level/up_level/down_level`，确认裁剪窗口如何变成 64-bit level。
5. 最后回到 `gen_data_mux`，把 `scan_mode/spot_data` 和 mux 分支对应起来。

读完应能回答：

```text
command_monitor_new 解释了上位机参数如何影响点生成。
但它不是 DAC 输出点流的最后一级，也不是 CDC 所在位置。
```

下一步：进入第 9 章支撑模块，最后确认 FIFO/CDC 位宽和 AD9747 配置链。

## 9. 第八步：支撑模块，最后再看

主链路读通后，再看 FIFO IP 和 `ad9747_cfg`。它们很重要，但它们不是“谁生成 DAX/DAY”的答案。放到最后看，是为了防止支撑逻辑抢走主线注意力。

### 9.1 FIFO IP stub/XCI

相关文件：

```text
fpga_prj/AXI_DDR.ip_user_files/ip/fifo_generator_4/fifo_generator_4_stub.v
fpga_prj/AXI_DDR.ip_user_files/ip/fifo_generator_2/fifo_generator_2_stub.v
fpga_prj/AXI_DDR.ip_user_files/ip/sync_fifo_9bit/sync_fifo_9bit_stub.v
```

本步目标：确认位宽、时钟方向、反压信号，而不是研究 FIFO 内部实现。

搜索入口：

```text
fifo_generator_4
fifo_generator_2
sync_fifo_9bit
din
dout
wr_clk
rd_clk
prog_full
prog_empty
wr_rst_busy
rd_rst_busy
```

本模块 DAC 相关信号：

| IP | 位宽 | 写时钟 | 读时钟 | 在 DAC 通路里的作用 |
|---|---:|---|---|---|
| `fifo_generator_4` | 34 | `eth_clk/ui_clk` | `dac_dco` | 主 DAC 点流 CDC，传 `{frame_end, adc_tri, DAX, DAY}` |
| `sync_fifo_9bit` | 9 | `eth_clk/ui_clk` | `dac_dco` | mode/reset 控制 CDC，得到 `scan_mode_sync/mill_mode_sync/dac_rstn` |
| `fifo_generator_2` | 130 | `eth_clk/ui_clk` | `dac_dco` | blanker 辅助时序 CDC，和主点流同写同读 |

先忽略：

| 先忽略 | 原因 |
|---|---|
| FIFO netlist 或仿真库 | 第一遍只需要 stub/XCI 的端口和配置 |
| FIFO 内部存储实现 | Vivado IP 黑盒，不是 RTL 阅读重点 |

代码阅读顺序：

1. 先看 `fifo_generator_4_stub.v`，确认 `din/dout` 都是 `[33:0]`。
2. 回到 `dac_output.v`，确认 `fifo_generator_4` 的写侧是 `ui_clk`，读侧是 `dac_dco`。
3. 看 `sync_fifo_9bit_stub.v`，确认控制位宽是 9 bit。
4. 看 `fifo_generator_2_stub.v`，确认 blanker 辅助流是 130 bit。
5. 回到 `dac_output.v`，确认主 FIFO 和 blanker FIFO 同写同读，但复位条件并不完全一样。

读完应能回答：

```text
DAC 主点流真正跨时钟的是 fifo_generator_4。
sync_fifo_9bit 只跨控制，fifo_generator_2 只跨 blanker 辅助信息。
```

### 9.2 `ad9747_cfg.v`

文件：`fpga_prj/AXI_DDR.srcs/sources_1/new/ad9747_cfg.v`

本步目标：确认它是 AD9747 配置模块，不是主 DAC 点流模块。

搜索入口：

```text
module ad9747_cfg
dacx_gain
dacy_gain
dac_sclk
dac_sdio
dac_csb
dac_sdo
dac_reset
```

本模块 DAC 相关信号：

| 类别 | 信号 | 你要理解的作用 |
|---|---|---|
| 配置输入 | `dacx_gain`、`dacy_gain` | 来自 `command_monitor_new` 的增益配置位 |
| SPI 输入 | `dac_sdo` | AD9747 SPI 回读/输入 |
| SPI 输出 | `dac_sclk`、`dac_sdio`、`dac_csb` | 配置 AD9747 寄存器 |
| 复位 | `dac_reset` | 当前代码里直接 `assign dac_reset=1'b0` |
| 配置 ROM | `wrrom*` | AD9747 软复位、数据格式、DAC1/DAC2 电流等配置字 |

先忽略：

| 先忽略 | 原因 |
|---|---|
| `data_reg/csn_reg/cntr` 的完整移位时序 | 第一遍只需要知道它发 SPI 配置 |
| `wrrom*` 每个 bit 的芯片手册含义 | 需要 AD9747 datasheet，和主数据链分开看 |

代码阅读顺序：

1. 看端口，确认没有 `DAX_DATA/DAY_DATA`，也没有 `dac_p1d/dac_p2d`。
2. 看 `dac_sclk/dac_sdio/dac_csb` 的 assign，确认是 SPI 配置链。
3. 看 `dacx_gain/dacy_gain` 如何影响配置字选择。
4. 回到 `ETH_TOP`，确认 `ad9747_cfg U1` 只接配置脚，不接主并行数据脚。

读完应能回答：

```text
ad9747_cfg 配置 DAC 芯片，但不承载主 DAC 点流。
主点流仍然是 dac_output -> DAX/DAY -> dac_p1d/p2d。
```

## 10. 上板或仿真时看哪些信号

如果你要确认链路是否跑通，按下面几组看，不要一次性塞满 ILA。

### 10.1 出口组

| 信号 | 目的 |
|---|---|
| `dac_dco` | 确认 DAC 输出时钟存在 |
| `DAX_DATA`、`DAY_DATA` | FPGA 内部 X/Y 点是否变化 |
| `dac_p1d`、`dac_p2d` | 顶层互补映射后是否输出 |

### 10.2 FIFO/CDC 组

| 信号 | 目的 |
|---|---|
| `para_config_wr_en` | 上游是否写点 |
| `para_config_data[33:0]` | 写入的点包是否正确 |
| `para_config_prog_full`、`para_config_wr_rst_busy` | 是否被下游反压卡住 |
| `para_config_rd_en`、`para_config_rd_en_r` | `dac_dco` 域是否在读点 |
| `para_config_dout[33:0]` | 跨域后点包是否正确 |
| `para_config_prog_empty`、`para_config_rd_rst_busy` | 是否 FIFO 空或读复位忙 |

### 10.3 输出锁存组

| 信号 | 目的 |
|---|---|
| `DA1_DATA`、`DA2_DATA` | `dac_output` 最后一级锁存值 |
| `adc_tri`、`frame_end_sig` | 同步标记是否按包拆出 |
| `scan_mode_sync`、`mill_mode_sync` | mode 是否已经跨到 `dac_dco` 域 |

### 10.4 来源选择组

| 信号 | 目的 |
|---|---|
| `scan_mode`、`mill_state_adj` | mux 分支选择是否符合预期 |
| `scan_data_wr_en`、`scan_data` | 普通扫描是否产点 |
| `mill_data_wr_en`、`mill_data` | 加工路径是否产点 |
| `spot_data` | 单点模式输入是否正确 |
| `gen_data_mux.para_config_wr_en/data` | mux 输出是否正确 |

现有 RTL 中 `dac_output` 已实例化 `ila_dr_test`，probe 包含 `dac_rstn`、`scan_mode_sync`、`mill_mode_sync`、`para_config_rd_en_r`、`adc_tri_sync`、`adc_tri`、`DA1_DATA`、`DA2_DATA`，可以作为第一组硬件观察点。

## 11. 待确认和风险点

1. `image_gen_top.v` 的 `para_config_data` 端口声明为 `[32:0]`，但 `parameter_dacdata_gen.v` 输出 `[33:0]`，`gen_data_mux.v` 又按 `[33:0] scan_data` 使用。普通扫描路径的 `frame_end_sig` bit 可能被截断或产生端口宽度 warning。
2. AD9747 实际更新率不能只从 RTL 判断，需要结合 `dac_dco` 板级来源、AD9517 输出连接和实测时钟。
3. `sync_fifo_9bit` 的 full/empty 未参与控制，mode/reset 连续跨域在启停瞬间是否稳定，需要仿真或 ILA 确认。
4. `fifo_generator_2` blanker 辅助 FIFO 和主 FIFO 独立，虽然同写同读，但复位条件与主 FIFO 不完全相同，需要确认 reset/scan_state 重新启动后是否仍对齐。
5. `0x0015` 同时把 `start_dly` 和 `end_dly` 写成同一个 16-bit 值，如果协议期望独立 start/end 延迟，需要查上位机协议或历史版本。
6. 当前顶层没有发现离子束路径直接替换 AD9747 主 DAC 的 `DAX_DATA/DAY_DATA`，离子束是否复用该输出仍需原理图或协议确认。

## 12. 关键证据索引

| 证据 | 文件位置 |
|---|---|
| 顶层 DAC 端口 | `fpga_prj/AXI_DDR.srcs/sources_1/new/ETH_TOP.v:63` |
| 顶层 `DAX/DAY -> dac_p1d/p2d` 互补映射 | `fpga_prj/AXI_DDR.srcs/sources_1/new/ETH_TOP.v:765` |
| `scan_top U6` 输出 `DAX/DAY` | `fpga_prj/AXI_DDR.srcs/sources_1/new/ETH_TOP.v:771` |
| `gen_data_mux U13` | `fpga_prj/AXI_DDR.srcs/sources_1/new/ETH_TOP.v:816` |
| `scan_top` 端口与 `dac_output N2` | `fpga_prj/AXI_DDR.srcs/sources_1/new/scan_top.v:1`、`:88` |
| `dac_output` 主 FIFO 和拆包 | `fpga_prj/AXI_DDR.srcs/sources_1/new/dac_output.v:66`、`:140` |
| `gen_data_mux` 三路选择 | `fpga_prj/AXI_DDR.srcs/sources_1/new/gen_data_mux.v:143` |
| `image_gen_top -> parameter_dacdata_gen` | `fpga_prj/AXI_DDR.srcs/sources_1/new/image_gen_top.v:78` |
| 普通扫描 34-bit 打包 | `fpga_prj/AXI_DDR.srcs/sources_1/new/parameter_dacdata_gen.v:100` |
| `mill_controller` 加工数据选择 | `fpga_prj/AXI_DDR.srcs/sources_1/new/mill_controller.v:500` |
| DAC 相关寄存器写地址 | `fpga_prj/AXI_DDR.srcs/sources_1/new/command_monitor_new.v:371` |
| step 计算 | `fpga_prj/AXI_DDR.srcs/sources_1/new/command_monitor_new.v:722` |
| FIFO 主点流/blanker/control 位宽 | `fpga_prj/AXI_DDR.ip_user_files/ip/fifo_generator_4/fifo_generator_4_stub.v:17`、`fpga_prj/AXI_DDR.ip_user_files/ip/fifo_generator_2/fifo_generator_2_stub.v:17`、`fpga_prj/AXI_DDR.ip_user_files/ip/sync_fifo_9bit/sync_fifo_9bit_stub.v:17` |
| `ad9747_cfg` 配置端口 | `fpga_prj/AXI_DDR.srcs/sources_1/new/ad9747_cfg.v:21` |
