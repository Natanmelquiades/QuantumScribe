param(
    [switch]$Setup,
    [switch]$Cuda
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
    $Setup = $true
}

if ($Setup) {
    $RequirementsFile = if ($Cuda) { "requirements-cuda.txt" } else { "requirements-cpu.txt" }
    Write-Host "Preparando o Quantum Scribe com $RequirementsFile..."
    & ".venv\Scripts\python.exe" -m pip install -r $RequirementsFile
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao preparar as dependências do Quantum Scribe."
    }
}

& ".venv\Scripts\pythonw.exe" main.py
