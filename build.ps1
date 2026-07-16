param(
    [switch]$Cuda
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
}

$RequirementsFile = if ($Cuda) { "requirements-cuda.txt" } else { "requirements-cpu.txt" }
& ".venv\Scripts\python.exe" -m pip install -r $RequirementsFile
& ".venv\Scripts\python.exe" -m PyInstaller --noconfirm QuantumScribe.spec

Write-Host ""
Write-Host "Executável criado em: dist\QuantumScribe\QuantumScribe.exe"
