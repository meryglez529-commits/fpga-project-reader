#==============================================================================
# run_sim.tcl — Closed-loop xsim run-once template
#
# Purpose:
#   Compile + elaborate + run + collect a deterministic pass/fail signal.
#   Designed for AI-driven closed-loop iteration: exit code 0 = PASS,
#   nonzero = FAIL, log lines machine-parseable.
#
# Usage (PowerShell, from project root):
#   & "C:/Xilinx/Vivado/2021.1/bin/vivado.bat" -mode batch `
#       -source AI-work/scripts/run_sim.tcl `
#       -tclargs <project.xpr> [<sim_set>] [<runtime>] `
#       -log    AI-work/sim_out/run_sim.log `
#       -journal AI-work/sim_out/run_sim.jou
#
# Customize before first use:
#   - `default_sim_set`  : usually `sim_1`
#   - `default_runtime`  : adjust per testbench
#   - `pass_token` / `fail_token`: testbench must $display these
#   - `csv_path`         : where signals are dumped (testbench writes it)
#   - `wdb_path`         : if you need to keep the waveform DB
#==============================================================================

# --- knobs ------------------------------------------------------------------
set default_sim_set  "sim_1"
set default_runtime  "1ms"
set pass_token       "PASS"
set fail_token       "FAIL"
set csv_path         "AI-work/sim_out/sim_result.csv"
set wdb_path         "AI-work/sim_out/sim.wdb"
set log_keep_lines   500       ;# 仅保留尾部 N 行做 pass/fail 判定
# ----------------------------------------------------------------------------

proc info_line {m} { puts "INFO  : $m" }
proc fail_line {m} { puts "FAIL  : $m" }

# --- 1. 参数 ----------------------------------------------------------------
if {[llength $argv] < 1} {
    fail_line "missing argument: <project.xpr>"
    exit 2
}
set xpr     [lindex $argv 0]
set sim_set [expr {[llength $argv] >= 2 ? [lindex $argv 1] : $default_sim_set}]
set runtime [expr {[llength $argv] >= 3 ? [lindex $argv 2] : $default_runtime}]

if {![file exists $xpr]} {
    fail_line "xpr not found: $xpr"
    exit 2
}
info_line "xpr=$xpr sim_set=$sim_set runtime=$runtime"

# --- 2. 准备输出目录 --------------------------------------------------------
file mkdir AI-work/sim_out
file mkdir AI-work/sim

# --- 3. 打开工程 ------------------------------------------------------------
open_project $xpr
current_sim_set [get_filesets $sim_set]
update_compile_order -fileset $sim_set

set tb_top [get_property top [get_filesets $sim_set]]
info_line "tb top: $tb_top"

# --- 4. 设置仿真时长（让 testbench 自己 $finish 也行，这里给一个上限） ------
set_property -name {xsim.simulate.runtime} -value $runtime -objects [get_filesets $sim_set]
set_property -name {xsim.simulate.log_all_signals} -value true -objects [get_filesets $sim_set]

# --- 5. 启动仿真 ------------------------------------------------------------
info_line "launching xsim ..."
if {[catch {launch_simulation -mode behavioral} err]} {
    fail_line "launch_simulation failed: $err"
    close_project
    exit 3
}

run $runtime

# --- 6. 收集波形数据库路径（xsim 默认在 sim 目录） --------------------------
set actual_wdb ""
foreach f [glob -nocomplain "*.sim/$sim_set/behav/xsim/*.wdb"] {
    set actual_wdb $f
    break
}
if {$actual_wdb ne ""} {
    file copy -force $actual_wdb $wdb_path
    info_line "wdb copied to $wdb_path"
}

close_sim
close_project

# --- 7. 解析 testbench 的 PASS/FAIL --------------------------------------
# Vivado 把 $display 的输出写到 .log（启动时的 -log 参数）。
# 我们让调用方传日志路径，这里默认从 AI-work/sim_out/run_sim.log 读。
set log_file "AI-work/sim_out/run_sim.log"
if {![file exists $log_file]} {
    fail_line "run_sim log not found: $log_file (forgot -log flag?)"
    exit 4
}

set lines {}
set fp [open $log_file r]
while {[gets $fp line] >= 0} {
    lappend lines $line
}
close $fp

set tail_start [expr {max(0, [llength $lines] - $log_keep_lines)}]
set tail [lrange $lines $tail_start end]

set saw_pass 0
set saw_fail 0
foreach l $tail {
    if {[string first $fail_token $l] >= 0} { incr saw_fail; puts "  >> $l" }
    if {[string first $pass_token $l] >= 0} { incr saw_pass; puts "  >> $l" }
}

if {$saw_fail > 0} {
    fail_line "testbench reported FAIL ($saw_fail occurrence(s))"
    exit 1
}
if {$saw_pass == 0} {
    fail_line "testbench did not emit '$pass_token' — undecided result. 检查 testbench 是否有 \$display(\"PASS\")。"
    exit 1
}

# --- 8. 检查 csv 是否生成 ----------------------------------------------------
if {[file exists $csv_path]} {
    info_line "result csv: $csv_path"
} else {
    info_line "no csv emitted (testbench did not write $csv_path; this is OK if not expected)"
}

info_line "SIMULATION PASS"
exit 0
