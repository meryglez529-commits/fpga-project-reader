#==============================================================================
# run_manual.tcl — Project-level manual xsim template
#
# Purpose:
#   Use this when Vivado `launch_simulation` or direct `xsim.exe` is unreliable.
#   Open the project in Vivado batch, run external xvlog/xelab as needed, then
#   run the simulation through Vivado's built-in Tcl `xsim` command.
#
# Copy into AI-work/scripts/ or AI-work/features/<feature>/<UNIT>/sim/ and
# customize project_xpr, tb_top, .prj contents, libraries, and result parsing.
#==============================================================================

set project_xpr "<PROJECT_XPR>"
set tb_top "<TB_TOP>"
set out_dir "AI-work/sim_out/manual_sim"
file mkdir $out_dir

proc info_line {msg} { puts "INFO: $msg" }
proc fail_line {msg} {
    puts "FAIL: $msg"
    set fp [open "$::out_dir/result.txt" w]
    puts $fp "FAIL: $msg"
    close $fp
    exit 1
}

if {![file exists $project_xpr]} {
    fail_line "project not found: $project_xpr"
}

open_project $project_xpr

foreach ip [get_ips -quiet] {
    catch {generate_target Simulation $ip -quiet}
}

set sim_work "$out_dir/work"
file mkdir $sim_work
cd $sim_work

set prj "${tb_top}.prj"
set fp [open $prj w]
puts $fp "# Customize this generated project file."
puts $fp "verilog xil_defaultlib \"<RTL_OR_IP_SIM_FILE.v>\""
puts $fp "verilog xil_defaultlib \"<TESTBENCH_FILE.v>\""
puts $fp "verilog xil_defaultlib \"<GLBL_FILE.v>\""
puts $fp "nosort"
close $fp

set vivado_bin [file dirname [info nameofexecutable]]

catch {exec [file join $vivado_bin xvlog] --relax -prj $prj -log "$out_dir/xvlog.log"} xvlog_result
set xvlog_text [read [open "$out_dir/xvlog.log" r]]
if {[string match "*ERROR*" $xvlog_text]} {
    fail_line "xvlog reported ERROR"
}

catch {exec [file join $vivado_bin xelab] --debug typical --relax --mt 2 \
    -L xil_defaultlib -L unisims_ver -L unimacro_ver -L secureip -L xpm \
    --snapshot ${tb_top}_behav xil_defaultlib.${tb_top} xil_defaultlib.glbl \
    -log "$out_dir/xelab.log"} xelab_result
set xelab_text [read [open "$out_dir/xelab.log" r]]
if {![string match "*Built simulation snapshot*" $xelab_text]} {
    fail_line "xelab did not build snapshot"
}

xsim ${tb_top}_behav -log "$out_dir/xsim.log"
run all

set xsim_text [read [open "$out_dir/xsim.log" r]]
if {[string match "*FAIL*" $xsim_text]} {
    fail_line "testbench reported FAIL"
}
if {![string match "*PASS*" $xsim_text]} {
    fail_line "testbench did not report PASS"
}

set fp [open "$out_dir/result.txt" w]
puts $fp "PASS"
close $fp
info_line "MANUAL SIM PASS"
exit 0
