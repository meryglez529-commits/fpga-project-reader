#==============================================================================
# diff_report.tcl — Compare two checkpoints / runs for regressions
#
# Purpose:
#   After each closed-loop iteration, compare the new run's WNS/TNS/utilization
#   against a reference (typically the previous successful run, or the
#   baseline). Emit a markdown diff so the AI can detect silent regressions
#   such as "timing still met but TNS doubled" or "LUT silently +8%".
#
# Usage:
#   & "C:/Xilinx/Vivado/2021.1/bin/vivado.bat" -mode batch `
#       -source AI-work/scripts/diff_report.tcl `
#       -tclargs <baseline_dir> <current_dir> [<output_md>] `
#       -log    AI-work/sim_out/diff_report.log
#
#   <baseline_dir> and <current_dir> each contain:
#       metrics.txt           (key=value)
#       utilization_impl.rpt  (Vivado report_utilization output)
#
#   <output_md> defaults to AI-work/reports/diff.md
#==============================================================================

# --- knobs ------------------------------------------------------------------
set wns_alarm_ns        -0.1   ;# 退步超过此 ns 报警
set tns_alarm_ratio      1.5   ;# 退步超过 1.5 倍报警
set util_alarm_pct       3.0   ;# 资源占用单项涨 >3% 报警
# ----------------------------------------------------------------------------

proc info_line {m} { puts "INFO  : $m" }
proc fail_line {m} { puts "FAIL  : $m" }

# --- 1. 参数 ----------------------------------------------------------------
if {[llength $argv] < 2} {
    fail_line "usage: diff_report.tcl <baseline_dir> <current_dir> \[output_md\]"
    exit 2
}
set baseline_dir [lindex $argv 0]
set current_dir  [lindex $argv 1]
set output_md    [expr {[llength $argv] >= 3 ? [lindex $argv 2] : "AI-work/reports/diff.md"}]

foreach d [list $baseline_dir $current_dir] {
    if {![file isdirectory $d]} {
        fail_line "directory not found: $d"
        exit 2
    }
}

file mkdir [file dirname $output_md]

# --- 2. 解析 metrics.txt ----------------------------------------------------
proc read_metrics {dir} {
    set path "$dir/metrics.txt"
    array set m {wns_ns "" tns_ns "" whs_ns "" ths_ns ""}
    if {![file exists $path]} {
        return [array get m]
    }
    set fp [open $path r]
    while {[gets $fp line] >= 0} {
        if {[regexp {^([a-zA-Z_]+)=(.+)$} $line _ k v]} {
            set m($k) [string trim $v]
        }
    }
    close $fp
    return [array get m]
}

array set base [read_metrics $baseline_dir]
array set curr [read_metrics $current_dir]

# --- 3. 解析 utilization 关键行 --------------------------------------------
proc read_util_summary {dir} {
    set path "$dir/utilization_impl.rpt"
    array set u {}
    if {![file exists $path]} {
        set path "$dir/utilization_synth.rpt"
    }
    if {![file exists $path]} {
        return [array get u]
    }
    set fp [open $path r]
    while {[gets $fp line] >= 0} {
        # 抓 LUT/FF/BRAM/DSP 关键行（典型行形如 "| Slice LUTs    | 12345 |  ...  | 80.50 |"）
        if {[regexp {^\|\s*(Slice LUTs|Slice Registers|Block RAM Tile|DSPs)\s*\|\s*(\d+)\s*\|.*\|\s*([0-9.]+)\s*\|} \
                    $line _ name used pct]} {
            set u($name,used) $used
            set u($name,pct)  $pct
        }
    }
    close $fp
    return [array get u]
}

array set base_u [read_util_summary $baseline_dir]
array set curr_u [read_util_summary $current_dir]

# --- 4. 写 markdown ---------------------------------------------------------
set fp [open $output_md w]
puts $fp "# Diff Report"
puts $fp ""
puts $fp "Baseline: \`$baseline_dir\`"
puts $fp "Current : \`$current_dir\`"
puts $fp ""

# 时序
puts $fp "## Timing"
puts $fp ""
puts $fp "| 指标 | Baseline | Current | Δ | 报警 |"
puts $fp "|---|---|---|---|---|"

set timing_alarms 0
foreach k {wns_ns tns_ns whs_ns ths_ns} {
    set b $base($k)
    set c $curr($k)
    set delta "—"
    set alarm "—"
    if {$b ne "" && $c ne ""} {
        set delta [format "%.3f" [expr {$c - $b}]]
        if {$k eq "wns_ns" || $k eq "whs_ns"} {
            if {$c < $b + $wns_alarm_ns} {
                set alarm "⚠️ 退步"
                incr timing_alarms
            }
        } elseif {$k eq "tns_ns" || $k eq "ths_ns"} {
            if {$b != 0 && [expr {abs($c)}] > [expr {abs($b) * $tns_alarm_ratio}]} {
                set alarm "⚠️ 退步"
                incr timing_alarms
            }
        }
    }
    puts $fp "| $k | $b | $c | $delta | $alarm |"
}
puts $fp ""

# 资源
puts $fp "## Utilization"
puts $fp ""
puts $fp "| 资源 | Baseline used | Baseline % | Current used | Current % | Δ% | 报警 |"
puts $fp "|---|---|---|---|---|---|---|"

set util_alarms 0
foreach name {"Slice LUTs" "Slice Registers" "Block RAM Tile" "DSPs"} {
    set bu  ""
    set bp  ""
    set cu  ""
    set cp  ""
    if {[info exists base_u($name,used)]} { set bu $base_u($name,used); set bp $base_u($name,pct) }
    if {[info exists curr_u($name,used)]} { set cu $curr_u($name,used); set cp $curr_u($name,pct) }
    set d_pct "—"
    set alarm "—"
    if {$bp ne "" && $cp ne ""} {
        set d_pct [format "%.2f" [expr {$cp - $bp}]]
        if {[expr {$cp - $bp}] > $util_alarm_pct} {
            set alarm "⚠️ 上涨"
            incr util_alarms
        }
    }
    puts $fp "| $name | $bu | $bp | $cu | $cp | $d_pct | $alarm |"
}
puts $fp ""

# 总结
puts $fp "## Summary"
puts $fp ""
set total [expr {$timing_alarms + $util_alarms}]
if {$total == 0} {
    puts $fp "✅ 无回归告警。"
} else {
    puts $fp "⚠️ 共 $total 项告警：时序 $timing_alarms，资源 $util_alarms。"
    puts $fp ""
    puts $fp "建议在继续闭环前确认是改动引入的退步，还是噪声。"
}

close $fp
info_line "diff written: $output_md"

# 返回退出码：有告警退出 1，便于 CI 集成
if {$timing_alarms + $util_alarms > 0} {
    info_line "DIFF: ALARMS PRESENT"
    exit 1
} else {
    info_line "DIFF: OK"
    exit 0
}
