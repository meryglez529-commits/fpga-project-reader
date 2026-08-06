# Non-invasive inventory of existing debug cores after explicit user authorization.
# Usage: vivado -mode batch -source inspect-existing-ila.tcl -tclargs <AI-work-output-dir> USER_AUTHORIZED

if {[llength $argv] != 2 || [lindex $argv 1] ne "USER_AUTHORIZED"} {
    puts "FAIL: requires <AI-work-output-dir> USER_AUTHORIZED"
    exit 2
}
set out_dir [file normalize [lindex $argv 0]]
if {![regexp {(^|/)AI-work(/|$)} [string map {\\ /} $out_dir]]} { puts "FAIL: output must be under AI-work"; exit 2 }
file mkdir $out_dir
cd $out_dir
puts "INFO: Hardware Manager work directory: [pwd]"
proc safe_property {property object} {
    if {[catch {get_property $property $object} value]} { return "<unavailable>" }
    return $value
}
open_hw_manager
connect_hw_server
open_hw_target
set fp [open [file join $out_dir existing_ila_inventory.txt] w]
puts $fp "devices: [get_hw_devices]"
foreach ila [get_hw_ilas -quiet] {
    puts $fp "ILA: $ila"
    puts $fp "  clock: [safe_property INPUT_CLK_FREQUENCY $ila]"
    puts $fp "  depth: [safe_property DATA_DEPTH $ila]"
    foreach probe [get_hw_probes -quiet -of_objects $ila] {
        puts $fp "  probe: $probe width=[safe_property PORT_WIDTH $probe]"
    }
}
close $fp
close_hw_manager
puts "PASS: inventory exported; no capture, trigger, register write, or bitstream programming occurred"
