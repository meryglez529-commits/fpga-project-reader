#==============================================================================
# export_csv.tcl — Export selected signals from xsim WDB to CSV
#
# Purpose:
#   Convert a captured xsim waveform database into CSV that the AI can read
#   without opening the GUI. Use for post-mortem of a failed run, or for
#   regression comparison against a golden CSV.
#
# Notes:
#   xsim does NOT have a native single-shot "wdb -> csv" conversion. The
#   reliable approach is one of:
#     (a) testbench writes CSV via $fwrite during simulation (preferred).
#     (b) post-process VCD with a small parser (this script's path).
#     (c) export from the GUI manually.
#
#   This template implements option (b): re-open the WDB headlessly,
#   dump a VCD subset, then convert VCD -> CSV by streaming.
#
# Usage:
#   xsim --gui or xsim --tclbatch ... is needed to dump VCD from WDB.
#   Recommended: drive your testbench to write CSV directly (option a).
#
#   This script is provided as a fallback. For most projects you should
#   instead add to your testbench:
#
#     integer fp;
#     initial begin
#         fp = $fopen("AI-work/sim_out/sim_result.csv", "w");
#         $fwrite(fp, "time,signal_a,signal_b,expect,pass\n");
#     end
#     always @(posedge clk) begin
#         if (sample_en)
#             $fwrite(fp, "%0t,%h,%h,%h,%s\n",
#                     $time, signal_a, signal_b, expect_val,
#                     (signal_a === expect_val) ? "PASS" : "FAIL");
#     end
#==============================================================================

# --- knobs ------------------------------------------------------------------
set wdb_path     "AI-work/sim_out/sim.wdb"
set vcd_path     "AI-work/sim_out/sim.vcd"
set csv_path     "AI-work/sim_out/sim_export.csv"

# 要导出的信号路径列表（按 testbench 实际层次填写）
set signals_to_dump {
    /tb_top/dut/clk
    /tb_top/dut/rst_n
    /tb_top/dut/data_valid
    /tb_top/dut/data_out
}
# ----------------------------------------------------------------------------

proc info_line {m} { puts "INFO  : $m" }
proc fail_line {m} { puts "FAIL  : $m" }

if {![file exists $wdb_path]} {
    fail_line "wdb not found: $wdb_path"
    fail_line "提示：优先让 testbench 自己写 CSV（见本脚本头部注释 option a），"
    fail_line "      比从 wdb 反推 CSV 高效十倍。"
    exit 2
}

# --- 1. 重新打开 wdb 并 dump VCD --------------------------------------------
info_line "opening wdb: $wdb_path"
open_wave_database $wdb_path

open_vcd $vcd_path
foreach s $signals_to_dump {
    if {[catch {log_vcd $s} err]} {
        fail_line "log_vcd failed for $s: $err"
    }
}
flush_vcd
close_vcd
close_wave_database
info_line "vcd written: $vcd_path"

# --- 2. VCD -> CSV 简易转换 -------------------------------------------------
# xsim 的 wdb 内置 VCD 后是 4-state（0/1/x/z）。这里做最小转换：
#   - 时间戳一行一条（仅在任何被监视信号变化时输出）
#   - 列顺序与 signals_to_dump 一致
#   - 用 16 进制表示总线，单 bit 用 0/1/x/z 原值
info_line "converting vcd -> csv"

set fp_in  [open $vcd_path r]
set fp_out [open $csv_path w]

# 写表头
set header "time"
foreach s $signals_to_dump { append header ",[file tail $s]" }
puts $fp_out $header

# 解析 VCD：构建 id -> name 映射，跟踪当前值
array set id2name {}
array set value   {}
set current_time  0
set time_unit     "ns"

# 简化：读到 $var 行学映射，读到 #N 行刷时间戳，读到 b... id 或 0/1/x/z id 行更新值
while {[gets $fp_in line] >= 0} {
    set line [string trim $line]
    if {[regexp {^\$var\s+\S+\s+\d+\s+(\S+)\s+(\S+)} $line _ id name]} {
        set id2name($id) $name
        set value($id) "x"
        continue
    }
    if {[regexp {^#(\d+)} $line _ t]} {
        # 在每个时间步开始前，先冲一行（如果是首次则跳过）
        if {$current_time != 0 || $t != 0} {
            set row "$current_time"
            foreach s $signals_to_dump {
                set sname [file tail $s]
                set v "x"
                foreach id [array names id2name] {
                    if {$id2name($id) eq $sname} { set v $value($id); break }
                }
                append row ",$v"
            }
            puts $fp_out $row
        }
        set current_time $t
        continue
    }
    # 标量变化：值 + id（无空格）
    if {[regexp {^([01xzXZ])(\S+)$} $line _ v id]} {
        if {[info exists id2name($id)]} { set value($id) $v }
        continue
    }
    # 矢量变化：bN..N <space> id
    if {[regexp {^b([01xzXZ]+)\s+(\S+)$} $line _ bits id]} {
        # 转 16 进制
        set hex ""
        set bits_padded $bits
        # 左填 0 到 4 的整数倍
        set pad [expr {(4 - [string length $bits_padded] % 4) % 4}]
        set bits_padded [string repeat 0 $pad]$bits_padded
        for {set i 0} {$i < [string length $bits_padded]} {incr i 4} {
            set nib [string range $bits_padded $i [expr {$i+3}]]
            if {[regexp {[xX]} $nib]} {
                append hex "x"
            } elseif {[regexp {[zZ]} $nib]} {
                append hex "z"
            } else {
                append hex [format %X [scan $nib %b]]
            }
        }
        if {[info exists id2name($id)]} { set value($id) "0x$hex" }
        continue
    }
}

# 输出最后一个时间步
set row "$current_time"
foreach s $signals_to_dump {
    set sname [file tail $s]
    set v "x"
    foreach id [array names id2name] {
        if {$id2name($id) eq $sname} { set v $value($id); break }
    }
    append row ",$v"
}
puts $fp_out $row

close $fp_in
close $fp_out

info_line "csv written: $csv_path"
info_line "EXPORT PASS"
exit 0
