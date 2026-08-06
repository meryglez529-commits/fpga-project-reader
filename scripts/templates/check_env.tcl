#==============================================================================
# check_env.tcl -- Mode 1 non-destructive environment inspection
#
# Usage:
#   vivado -mode batch -source AI-work/scripts/check_env.tcl -tclargs \
#       <project.xpr> <absolute-AI-work-baseline-tool-output-dir> \
#       -log <same-dir>/vivado_check_env.log -journal <same-dir>/vivado_check_env.jou
#
# The output directory must be under project-root/AI-work/. This script opens
# the project read-only and writes reports only to that directory. It does not
# prove a license is usable: synthesis/simulation execution is the evidence.
#==============================================================================

proc info_line {msg} { puts "INFO  : $msg" }
proc warn_line {msg} { puts "WARN  : $msg" }
proc fail_line {msg} { puts "FAIL  : $msg" }

if {[llength $argv] != 2} {
    fail_line "usage: <project.xpr> <absolute-AI-work-baseline-tool-output-dir>"
    exit 2
}

set xpr [file normalize [lindex $argv 0]]
set out_dir [file normalize [lindex $argv 1]]
set fail_count 0
set warn_count 0

if {![file exists $xpr]} {
    fail_line "project not found: $xpr"
    exit 2
}

# Use forward slashes after normalization so this check works on Windows Tcl.
set normalized_out [string map {\\ /} $out_dir]
if {![regexp {(^|/)AI-work(/|$)} $normalized_out]} {
    fail_line "refusing output outside AI-work: $out_dir"
    exit 2
}
file mkdir $out_dir

proc add_warn {msg} {
    global warn_count
    incr warn_count
    warn_line $msg
}
proc add_fail {msg} {
    global fail_count
    incr fail_count
    fail_line $msg
}
proc write_summary {path status failures warnings notes} {
    set fp [open $path w]
    puts $fp "status=$status"
    puts $fp "failures=$failures"
    puts $fp "warnings=$warnings"
    foreach note $notes { puts $fp "note=$note" }
    close $fp
}

set notes [list "xpr=$xpr" "output=$out_dir"]
info_line "opening read-only project: $xpr"
if {[catch {open_project -read_only $xpr} err]} {
    add_fail "open_project failed: $err"
    write_summary [file join $out_dir check_env.summary.txt] FAIL $fail_count $warn_count $notes
    exit 1
}

lappend notes "vivado=[version -short]"
lappend notes "project=[current_project]"
info_line "Vivado [version -short]; project [current_project]"
set part [get_property part [current_project]]
lappend notes "part=$part"
info_line "part: $part"

set top [get_property top [current_fileset]]
if {$top eq ""} {
    add_fail "top module is not set in current fileset"
} else {
    lappend notes "top=$top"
    info_line "top: $top"
}

set missing 0
foreach f [get_files] {
    if {![file exists $f]} {
        add_warn "referenced file missing on disk: $f"
        incr missing
    }
}
if {$missing > 0} { add_fail "$missing referenced file(s) are missing" }

if {[catch {update_compile_order -fileset sources_1} err]} {
    add_fail "update_compile_order failed: $err"
} else {
    report_compile_order -fileset sources_1 -used_in synthesis -file [file join $out_dir compile_order.rpt]
}

set xdc_files [get_files -quiet -filter {FILE_TYPE == XDC}]
if {[llength $xdc_files] == 0} {
    add_warn "no XDC file reported by the project"
}
set xdc_fp [open [file join $out_dir constraints.txt] w]
foreach xdc $xdc_files { puts $xdc_fp $xdc }
close $xdc_fp

set ip_repos [get_property ip_repo_paths [current_project]]
set repo_fp [open [file join $out_dir ip_repositories.txt] w]
foreach repo $ip_repos {
    puts $repo_fp $repo
    if {![file isdirectory $repo]} { add_warn "configured IP repository is missing: $repo" }
}
close $repo_fp

set ip_list [get_ips -quiet]
foreach ip $ip_list {
    if {[get_property IS_LOCKED $ip]} { add_warn "IP locked: $ip" }
    if {[get_property IPDEF $ip] eq ""} { add_warn "IPDEF unavailable: $ip" }
}
if {[catch {report_ip_status -file [file join $out_dir ip_status.rpt]} err]} {
    add_warn "report_ip_status failed: $err"
}
add_warn "license is not proven by this inspection; run the relevant simulation/synthesis stage"

close_project
if {$fail_count > 0} {
    set status FAIL
} elseif {$warn_count > 0} {
    set status DEGRADED
} else {
    set status PASS
}
write_summary [file join $out_dir check_env.summary.txt] $status $fail_count $warn_count $notes
puts "RESULT: $status (failures=$fail_count warnings=$warn_count)"
if {$fail_count > 0} { exit 1 }
exit 0
