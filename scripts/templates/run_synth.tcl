#==============================================================================
# run_synth.tcl — Closed-loop synthesis run + key metrics extraction
#
# Purpose:
#   Run synth_1 (and optionally impl_1 to write_bitstream), then extract
#   WNS / TNS / WHS / utilization into machine-parseable text reports under
#   AI-work/reports/. Designed for the AI to pick up metrics without parsing
#   Vivado GUI output.
#
# Usage:
#   & "C:/Xilinx/Vivado/2021.1/bin/vivado.bat" -mode batch `
#       -source AI-work/scripts/run_synth.tcl `
#       -tclargs <project.xpr> [synth|impl|bit] [<jobs>] `
#       -log    AI-work/sim_out/run_synth.log `
#       -journal AI-work/sim_out/run_synth.jou
#
# Modes:
#   synth  — synthesis only (default)
#   impl   — synth + place + route (no bit)
#   bit    — synth + impl + write_bitstream
#==============================================================================

# --- knobs ------------------------------------------------------------------
set default_jobs    4
set wns_pass_thresh 0.0       ;# WNS >= this => pass
set whs_pass_thresh 0.0       ;# WHS >= this => pass
set util_warn_lut   80.0      ;# warn if LUT > 80%
set util_warn_bram  80.0
set util_warn_dsp   80.0
# ----------------------------------------------------------------------------

proc info_line {m} { puts "INFO  : $m" }
proc warn_line {m} { puts "WARN  : $m" }
proc fail_line {m} { puts "FAIL  : $m" }

# --- 1. 参数 ----------------------------------------------------------------
if {[llength $argv] < 1} {
    fail_line "usage: run_synth.tcl <project.xpr> [synth|impl|bit] [jobs]"
    exit 2
}
set xpr   [lindex $argv 0]
set mode  [expr {[llength $argv] >= 2 ? [lindex $argv 1] : "synth"}]
set jobs  [expr {[llength $argv] >= 3 ? [lindex $argv 2] : $default_jobs}]

if {![file exists $xpr]} {
    fail_line "xpr not found: $xpr"
    exit 2
}
info_line "xpr=$xpr mode=$mode jobs=$jobs"

file mkdir AI-work/reports
file mkdir AI-work/sim_out

# --- 2. 打开工程 ------------------------------------------------------------
open_project $xpr

# --- 3. 跑综合 --------------------------------------------------------------
info_line "==== synth_1 ===="
reset_run synth_1
launch_runs synth_1 -jobs $jobs
wait_on_run synth_1
set synth_status [get_property STATUS [get_runs synth_1]]
info_line "synth_1 status: $synth_status"
if {[string first "ERROR" $synth_status] >= 0 || \
    [string first "Failed" $synth_status] >= 0} {
    fail_line "synthesis failed: $synth_status"
    close_project
    exit 1
}

# 资源占用（综合后）
open_run synth_1 -name synth_1
set util_rpt "AI-work/reports/utilization_synth.rpt"
report_utilization -file $util_rpt
info_line "utilization (post-synth) -> $util_rpt"

# --- 4. 跑实现（如果需要） --------------------------------------------------
set need_impl 0
set need_bit  0
switch -- $mode {
    "impl" { set need_impl 1 }
    "bit"  { set need_impl 1; set need_bit 1 }
}

if {$need_impl} {
    info_line "==== impl_1 ===="
    reset_run impl_1
    if {$need_bit} {
        launch_runs impl_1 -to_step write_bitstream -jobs $jobs
    } else {
        launch_runs impl_1 -jobs $jobs
    }
    wait_on_run impl_1
    set impl_status [get_property STATUS [get_runs impl_1]]
    info_line "impl_1 status: $impl_status"
    if {[string first "ERROR" $impl_status] >= 0 || \
        [string first "Failed" $impl_status] >= 0} {
        fail_line "implementation failed: $impl_status"
        close_project
        exit 1
    }

    open_run impl_1
    set timing_rpt   "AI-work/reports/timing_summary.rpt"
    set util_post    "AI-work/reports/utilization_impl.rpt"
    set drc_rpt      "AI-work/reports/drc.rpt"
    set methodology  "AI-work/reports/methodology.rpt"

    report_timing_summary -file $timing_rpt
    report_utilization    -file $util_post
    report_drc            -file $drc_rpt
    report_methodology    -file $methodology

    info_line "timing -> $timing_rpt"
    info_line "utilization (post-impl) -> $util_post"
    info_line "drc -> $drc_rpt"
    info_line "methodology -> $methodology"

    # WNS / TNS / WHS / THS
    set wns [get_property STATS.WNS [get_runs impl_1]]
    set tns [get_property STATS.TNS [get_runs impl_1]]
    set whs [get_property STATS.WHS [get_runs impl_1]]
    set ths [get_property STATS.THS [get_runs impl_1]]
    info_line [format "WNS=%s ns  TNS=%s ns  WHS=%s ns  THS=%s ns" $wns $tns $whs $ths]

    # 写一份机器友好的摘要
    set summary "AI-work/reports/metrics.txt"
    set fp [open $summary w]
    puts $fp "wns_ns=$wns"
    puts $fp "tns_ns=$tns"
    puts $fp "whs_ns=$whs"
    puts $fp "ths_ns=$ths"
    close $fp
    info_line "metrics summary -> $summary"

    # Pass/Fail
    set timing_pass 1
    if {$wns ne "" && [expr {$wns < $wns_pass_thresh}]} {
        warn_line "WNS $wns < $wns_pass_thresh ns"
        set timing_pass 0
    }
    if {$whs ne "" && [expr {$whs < $whs_pass_thresh}]} {
        warn_line "WHS $whs < $whs_pass_thresh ns"
        set timing_pass 0
    }
    if {!$timing_pass} {
        fail_line "TIMING NOT MET"
        close_project
        exit 1
    }
}

close_project
info_line "BUILD PASS"
exit 0
