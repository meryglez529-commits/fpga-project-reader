# Program a qualified existing image only after explicit per-session authorization.
# Usage: vivado -mode batch -source program-baseline.tcl -tclargs <bit> <ltx> <AI-work-output-dir> USER_AUTHORIZED
# This script never writes business registers or starts product behavior.

if {[llength $argv] != 4 || [lindex $argv 3] ne "USER_AUTHORIZED"} {
    puts "FAIL: requires <bit> <ltx> <AI-work-output-dir> USER_AUTHORIZED"
    exit 2
}
set bit [file normalize [lindex $argv 0]]
set ltx [file normalize [lindex $argv 1]]
set out_dir [file normalize [lindex $argv 2]]
if {![file exists $bit] || ![file exists $ltx]} { puts "FAIL: bit/LTX not found"; exit 2 }
if {![regexp {(^|/)AI-work(/|$)} [string map {\\ /} $out_dir]]} { puts "FAIL: output must be under AI-work"; exit 2 }
file mkdir $out_dir
cd $out_dir
puts "INFO: Hardware Manager work directory: [pwd]"
open_hw_manager
connect_hw_server
open_hw_target
set devices [get_hw_devices]
if {[llength $devices] != 1} { puts "FAIL: expected exactly one FPGA device, found [llength $devices]"; close_hw_manager; exit 2 }
set dev [lindex $devices 0]
set_property PROBES.FILE $ltx $dev
set_property PROGRAM.FILE $bit $dev
program_hw_devices $dev
refresh_hw_device $dev
set fp [open [file join $out_dir program_baseline.status.txt] w]
puts $fp "programmed_device=$dev"
puts $fp "bit=$bit"
puts $fp "ltx=$ltx"
puts $fp "note=no business registers or start commands issued"
close $fp
close_hw_manager
puts "PASS: programmed existing qualified image"
