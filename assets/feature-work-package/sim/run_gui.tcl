#==============================================================================
# Mode 5 GUI simulation template
#
# Copy into AI-work/features/<feature>/<UNIT>/sim/run_gui.tcl and customize.
# Intended for Vivado Tcl Console. Use project-level SIMULATION.md for known
# environment quirks before running.
#==============================================================================

set project_xpr "<PROJECT_XPR>"
set tb_file "<TB_FILE>"
set tb_top "<TB_TOP>"
set sim_set "sim_1"

if {[llength [get_projects -quiet]] == 0} {
    open_project $project_xpr
}

set fs [get_filesets $sim_set]
if {[file exists $tb_file]} {
    add_files -fileset $fs $tb_file
}
set_property top $tb_top $fs
set_property top_lib xil_defaultlib $fs
update_compile_order -fileset $sim_set

launch_simulation -mode behavioral
run all
