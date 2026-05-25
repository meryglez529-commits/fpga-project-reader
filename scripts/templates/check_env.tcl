#==============================================================================
# check_env.tcl — Co-work environment self-check
#
# Purpose:
#   Open the project once, confirm tooling, license, and source integrity.
#   Run this BEFORE any closed-loop edit/sim/synth iteration begins.
#
# Usage (PowerShell):
#   & "C:/Xilinx/Vivado/2021.1/bin/vivado.bat" -mode batch `
#       -source AI-work/scripts/check_env.tcl `
#       -tclargs <project.xpr> `
#       -log    AI-work/sim_out/check_env.log `
#       -journal AI-work/sim_out/check_env.jou
#
# Customize:
#   - Set the `licensed_ips` list to the paid IP cores in this project.
#   - Set `min_free_disk_gb` to your local policy.
#==============================================================================

# --- knobs you may want to adjust per project -------------------------------
set licensed_ips     {SGMII_TEMAC SGMII_PHY}   ;# ⚠️ 改成本工程的付费 IP module 名
set min_free_disk_gb 10                          ;# 综合期间至少要的磁盘
set max_path_chars   240                         ;# Windows 长路径警戒线
# ----------------------------------------------------------------------------

proc info_line {msg} { puts "INFO  : $msg" }
proc warn_line {msg} { puts "WARN  : $msg" }
proc fail_line {msg} { puts "FAIL  : $msg" }

set fail_count 0
proc bump_fail {} { global fail_count; incr fail_count }

# --- 1. 参数检查 -------------------------------------------------------------
if {[llength $argv] < 1} {
    fail_line "missing argument: <project.xpr>"
    bump_fail
    return
}
set xpr [lindex $argv 0]
if {![file exists $xpr]} {
    fail_line "xpr not found: $xpr"
    bump_fail
    return
}
info_line "xpr: $xpr"

# --- 2. 路径长度检查（Windows）---------------------------------------------
set abs_xpr [file normalize $xpr]
set path_len [string length $abs_xpr]
if {$path_len > $max_path_chars} {
    warn_line "project path is $path_len chars (>$max_path_chars). Vivado may fail on long paths."
} else {
    info_line "project path length: $path_len chars (OK)"
}

# --- 3. 磁盘空间检查（粗略） ------------------------------------------------
set drive [string range $abs_xpr 0 1]
catch {
    set free_bytes [exec powershell -NoProfile -Command \
        "(Get-PSDrive ${drive}).Free"]
    set free_gb [expr {$free_bytes / 1024.0 / 1024.0 / 1024.0}]
    if {$free_gb < $min_free_disk_gb} {
        warn_line [format "drive %s free space %.1f GB < %d GB threshold" \
                          $drive $free_gb $min_free_disk_gb]
    } else {
        info_line [format "drive %s free space %.1f GB (OK)" $drive $free_gb]
    }
}

# --- 4. 打开工程 -------------------------------------------------------------
info_line "opening project ..."
if {[catch {open_project $xpr} err]} {
    fail_line "open_project failed: $err"
    bump_fail
    return
}
info_line "vivado version: [version -short]"
info_line "project: [current_project]"
info_line "part: [get_property part [current_project]]"

# --- 5. 顶层与文件 -----------------------------------------------------------
set top [get_property top [current_fileset]]
if {$top eq ""} {
    fail_line "top module not set"
    bump_fail
} else {
    info_line "top module: $top"
}

set total_files [llength [get_files]]
info_line "total source files in fileset: $total_files"

# 检查文件实际存在
set missing 0
foreach f [get_files] {
    if {![file exists $f]} {
        warn_line "file referenced but not on disk: $f"
        incr missing
    }
}
if {$missing > 0} {
    fail_line "$missing referenced source file(s) missing on disk"
    bump_fail
} else {
    info_line "all referenced source files present"
}

# --- 6. IP 清单与状态 -------------------------------------------------------
set ip_list [get_ips]
info_line "ip count: [llength $ip_list]"
foreach ip $ip_list {
    set status [get_property IS_LOCKED $ip]
    set ipdef  [get_property IPDEF      $ip]
    if {$status} {
        warn_line "IP locked (needs upgrade): $ip ($ipdef)"
    }
}

# --- 7. License 检查（针对付费 IP） ----------------------------------------
foreach lic_ip $licensed_ips {
    set hits [get_ips -quiet $lic_ip]
    if {[llength $hits] == 0} {
        info_line "licensed-ip skipped (not present): $lic_ip"
        continue
    }
    # 用 report_property 看 IP 是否能正常读到 IPDEF（间接代表 license 没炸）
    set ipdef [get_property IPDEF [lindex $hits 0]]
    if {$ipdef eq ""} {
        fail_line "licensed IP not resolvable, possible license issue: $lic_ip"
        bump_fail
    } else {
        info_line "licensed IP OK: $lic_ip ($ipdef)"
    }
}

# 显式查 license 特性（部分 license 在 update_compile_order 时才报错）
if {[catch {update_compile_order -fileset sources_1} err]} {
    fail_line "update_compile_order failed: $err"
    bump_fail
} else {
    info_line "update_compile_order OK"
}

# --- 8. Compile order ------------------------------------------------------
info_line "==== compile order (top first) ===="
foreach f [get_files -compile_order sources -used_in synthesis] {
    puts "  $f"
}

# --- 9. 约束文件 -----------------------------------------------------------
set xdc_files [get_files -filter {FILE_TYPE == XDC}]
info_line "xdc files: [llength $xdc_files]"
foreach f $xdc_files {
    info_line "  $f"
}

# --- 10. 收尾 --------------------------------------------------------------
close_project

if {$fail_count > 0} {
    puts ""
    fail_line "check_env finished with $fail_count failure(s). 修复后再继续 setup。"
    exit 1
} else {
    puts ""
    info_line "check_env PASS. 工程可被 AI 安全打开，可进入闭环准备。"
    exit 0
}
