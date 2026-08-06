[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $ProjectRoot,
    [Parameter(Mandatory)] [string] $VivadoBat,
    [Parameter(Mandatory)] [string] $ProjectFile,
    [Parameter(Mandatory)] [string] $Top,
    [Parameter(Mandatory)] [string] $Part,
    [string] $SimulationTcl,
    [string] $SynthesisTcl,
    [string] $ImplementationTcl,
    [string] $BitstreamTcl,
    [string] $BaselineId = (Get-Date -Format 'yyyyMMdd-HHmmss')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Each supplied stage Tcl receives exactly: <project.xpr> <unit-local-stage-output>.
# It must create all tool work/log/report output in that second directory and
# must not reuse the project's synth_1/impl_1 runs. The caller supplies Top and
# Part from inspected project facts; the helper deliberately does not guess.

function Require-Path([string] $Path, [string] $Label) {
    if (-not (Test-Path -LiteralPath $Path)) { throw "$Label not found: $Path" }
    return (Resolve-Path -LiteralPath $Path).Path
}

function Test-Under([string] $Child, [string] $Parent) {
    $fullChild = [IO.Path]::GetFullPath($Child).TrimEnd('\')
    $fullParent = [IO.Path]::GetFullPath($Parent).TrimEnd('\')
    return $fullChild.StartsWith($fullParent + '\', [StringComparison]::OrdinalIgnoreCase)
}

$root = Require-Path $ProjectRoot 'Project root'
$vivado = Require-Path $VivadoBat 'Vivado executable'
$xpr = Require-Path $ProjectFile 'Project file'
$aiWork = Join-Path $root 'AI-work'
if (-not (Test-Path -LiteralPath $aiWork)) { throw "AI-work is required before a baseline run: $aiWork" }
$baseline = Join-Path $aiWork "reports\baseline\$BaselineId"
if (-not (Test-Under $baseline $aiWork)) { throw "refusing output outside AI-work: $baseline" }
New-Item -ItemType Directory -Force -Path $baseline | Out-Null

$gitHead = $null
$gitDirty = $null
try {
    $gitHead = (& git -C $root rev-parse HEAD 2>$null).Trim()
    $gitDirty = [bool]((& git -C $root status --porcelain 2>$null).Count)
} catch { }
$hashes = @()
if (-not $gitHead) {
    $hashes = Get-ChildItem -LiteralPath $root -Recurse -File -Include *.v,*.sv,*.vhd,*.vhdl,*.xdc,*.xci,*.bd |
        Where-Object { $_.FullName -notmatch '\\AI-work\\|\\.Xil\\|\\runs\\' } |
        ForEach-Object { [ordered]@{ path = $_.FullName; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } }
}

function Invoke-BaselineStage([string] $Name, [string] $Tcl) {
    $stageDir = Join-Path $baseline $Name
    New-Item -ItemType Directory -Force -Path $stageDir | Out-Null
    $log = Join-Path $stageDir "vivado_$Name.log"
    $journal = Join-Path $stageDir "vivado_$Name.jou"
    $stage = [ordered]@{
        status = 'NOT_RUN'; command = $null; work_dir = $stageDir; log = $log
        journal = $journal; next_action = 'supply a project-specific non-destructive Tcl stage'; blocker = $null
    }
    if (-not $Tcl) { return $stage }
    $tclPath = Require-Path $Tcl "$Name Tcl"
    $stage.command = "`"$vivado`" -mode batch -source `"$tclPath`" -tclargs `"$xpr`" `"$stageDir`" -log `"$log`" -journal `"$journal`""
    Push-Location $stageDir
    try {
        & $vivado -mode batch -source $tclPath -tclargs $xpr $stageDir -log $log -journal $journal
        if ($LASTEXITCODE -eq 0) {
            $stage.status = 'PASS'; $stage.next_action = 'none'
        } else {
            $stage.status = 'BLOCKED'; $stage.blocker = "Vivado exit code $LASTEXITCODE"; $stage.next_action = 'inspect stage log'
        }
    } catch {
        $stage.status = 'BLOCKED'; $stage.blocker = $_.Exception.Message; $stage.next_action = 'inspect stage log'
    } finally { Pop-Location }
    return $stage
}

$stages = [ordered]@{
    simulation = Invoke-BaselineStage 'sim' $SimulationTcl
    synthesis = Invoke-BaselineStage 'synth' $SynthesisTcl
    implementation = Invoke-BaselineStage 'impl' $ImplementationTcl
    bitstream = Invoke-BaselineStage 'bitstream' $BitstreamTcl
}
$allPass = @($stages.Values | ForEach-Object { $_.status }) -notcontains 'BLOCKED' -and
    @($stages.Values | ForEach-Object { $_.status }) -notcontains 'NOT_RUN'
$overall = if ($allPass) { 'READY_NO_BOARD' } elseif ($stages.simulation.status -eq 'BLOCKED') { 'SIM_BLOCKED' } else { 'BUILD_BLOCKED' }
$manifest = [ordered]@{
    baseline_id = $BaselineId; created_at = (Get-Date).ToString('o'); overall_status = $overall
    target_profile = [ordered]@{ project = $xpr; top = $Top; part = $Part }
    baseline_protection = [ordered]@{ state = if ($gitDirty) { 'DIRTY_BASELINE' } else { 'CLEAN_BASELINE' }; git_head = $gitHead; source_hashes = $hashes }
    stages = $stages
}
$manifestPath = Join-Path $baseline 'foundation_manifest.json'
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Host "Baseline manifest: $manifestPath"
Write-Host "Overall status: $overall"
if ($overall -notin @('READY_NO_BOARD')) { exit 1 }
