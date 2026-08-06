# Simulation Environment SOP

Use this reference in Mode 1 to record how **this project on this machine** can be simulated. Mode 3 units cite this canonical SOP and contribute verified discoveries back to it.

## 1. Canonical entry point

The normal entry is `AI-work/env/SIMULATION.md`. An established long-form SOP may remain at `AI-work/guide/VIVADO_SIM_SOP.md`, but `env/SIMULATION.md` or `env/ENVIRONMENT.md` must explicitly point to it. Validators accept either location only when that pointer is real; this removes the old contradiction between documentation and validation.

## 2. Required evidence

Record facts, not just instructions:

| Item | Record |
|---|---|
| Toolchain | Vivado executable/path/version and chosen simulator |
| Known-good path | Exact command/Tcl sequence, working directory, input files, output/log paths, version and result |
| Known-bad path | Exact command, error/symptom, evidence link and whether it is project-specific |
| Dependencies | IP simulation model generation, libraries, `.prj`, environment variables, licenses and source order |
| Constraint | Encryption, GUI/Webtalk, batch pipe, process lock, long path, GUI-only behavior or unavailable hardware |
| Recovery | Non-destructive workaround and how to restore a user-authorized environment change |
| Smoke evidence | Testbench or known-good run, assertions/checkpoint and the generated report |

For the current Vivado 2021.1 workstation, an observed project-specific path may be “Vivado batch → Tcl `exec xvlog/xelab` → Vivado built-in `xsim`”; direct `xsim`, batch `launch_simulation`, encrypted `init.tcl`, or GUI/Webtalk symptoms must be reported with their actual logs. This is an example of how to record evidence, not a universal rule. Do not rename, patch, or otherwise mutate Vivado installation files without explicit user authorization and a restoration path.

## 3. Mode 1 simulation smoke

Mode 1 must establish a minimal simulator capability, not prove every future testbench:

1. confirm project opening and compile order, or record the blocker;
2. run/replay one small known-good testbench or smoke command in the isolated baseline directory;
3. record `SIM_READY`, `SIM_BLOCKED`, or `NOT_RUN` with command and log;
4. distinguish an executable command path from actual functional coverage.

If no simulation route works, write `SIM_BLOCKED` and the needed external condition. A blocked simulation path never allows Mode 3 to claim simulation closure.

## 4. Output containment

- Mode 1: all logs, journals, `xsim.dir`, WDB/VCD/CSV and reports live under `AI-work/reports/baseline/<baseline-id>/sim/`.
- Mode 3: all equivalent outputs live under `AI-work/features/<feature>/<UNIT>/out/sim/`.
- Pass Vivado explicit `-log`, `-journal`, `-tempDir`/work (when supported), and export paths. Scan for spill after the run.
- Never deliberately leave new `vivado*.log`, `.jou`, `xvlog.pb`, `.wdb`, `xsim.dir`, CSV, or `hw_ila_data_*` in a project root, drive root, or system temp location.

## 5. Relationship to Mode 3

Mode 3 documents feature-specific stimuli, assertions and results in its unit’s `sim/SIM_REPLAY.md`; it links the project SOP rather than copying tool quirks. A reusable, verified discovery is then added back to the canonical SOP and `LOG.md`.

## 6. Validation

Run:

```powershell
python <skill>/scripts/validate-simulation-sop.py <project-root>/AI-work
python <skill>/scripts/validate-foundation.py <project-root>/AI-work
```

These checks validate structure and evidence references; read the actual Vivado/simulator logs before declaring a simulation pass.
