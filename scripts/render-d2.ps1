param(
  [Parameter(Mandatory=$true)][string]$Input,
  [Parameter(Mandatory=$true)][string]$Output,
  [string]$D2Exe = ".tools\d2-v0.7.1-windows-amd64\d2-v0.7.1\bin\d2.exe",
  [string]$Layout = "elk",
  [int]$Theme = 0,
  [int]$Pad = 60
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $D2Exe)) {
  throw "D2 executable not found at '$D2Exe'. Install D2 locally or pass -D2Exe."
}

$outDir = Split-Path -Parent $Output
if ($outDir) {
  New-Item -ItemType Directory -Force -Path $outDir | Out-Null
}

& $D2Exe $Input $Output "--theme=$Theme" "--layout=$Layout" "--pad=$Pad"
