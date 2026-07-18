param(
    [switch]$Cuda,
    [switch]$Installer
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$BuildVenv = ".venv-build-core"
$BuildPython = Join-Path $BuildVenv "Scripts\python.exe"

if (-not (Test-Path $BuildPython)) {
    Write-Host "Criando ambiente isolado de build em $BuildVenv..."
    python -m venv $BuildVenv
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao criar o ambiente isolado de build."
    }
}

if ($Cuda) {
    throw "O CUDA não faz mais parte do Core. Use scripts\build_optional_components.ps1 para gerar o componente sob demanda."
}

$RequirementsFile = "requirements-build.lock"
Write-Host "Instalando dependências reproduzíveis de $RequirementsFile..."
& $BuildPython -m pip install --require-hashes -r $RequirementsFile
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao instalar as dependências de build."
}

& $BuildPython scripts\prepare_windows_build.py
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao preparar o ícone e os metadados do Windows."
}

& $BuildPython -m PyInstaller --clean --noconfirm QuantumScribe.spec
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao gerar o executável com PyInstaller."
}

Write-Host ""
Write-Host "Executável criado em: dist\QuantumScribe\QuantumScribe.exe (Core CPU; GPU automática sob demanda)"

if ($Installer) {
    $BundleBytes = (Get-ChildItem "dist\QuantumScribe" -Recurse -File | Measure-Object Length -Sum).Sum
    $NsisSafeLimit = 1900MB
    if ($BundleBytes -gt $NsisSafeLimit) {
        $BundleMB = [math]::Round($BundleBytes / 1MB)
        throw "Bundle com ${BundleMB} MB excede o limite seguro de 1900 MB do NSIS."
    }

    $VersionLine = Get-Content "localwhisper\__init__.py" | Select-String '__version__\s*=\s*"([^"]+)"'
    if (-not $VersionLine) {
        throw "Não foi possível determinar a versão do QuantumScribe."
    }
    $Version = $VersionLine.Matches[0].Groups[1].Value
    $VersionParts = @($Version.Split('.') | ForEach-Object { [int]$_ })
    if ($VersionParts.Count -gt 4) {
        throw "Versão incompatível com os metadados do Windows: $Version"
    }
    while ($VersionParts.Count -lt 4) {
        $VersionParts += 0
    }
    $WindowsVersion = $VersionParts -join '.'

    & $BuildPython scripts\generate_nsis_uninstall_manifest.py
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao gerar a lista segura de desinstalação."
    }

    $NsisCandidates = @(
        (Get-Command makensis.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
        "${env:ProgramFiles}\NSIS\makensis.exe",
        "${env:ProgramFiles(x86)}\NSIS\makensis.exe",
        "${env:LOCALAPPDATA}\Programs\NSIS\makensis.exe"
    ) | Where-Object { $_ -and (Test-Path $_) }

    $MakeNsis = $NsisCandidates | Select-Object -First 1
    if (-not $MakeNsis) {
        throw "NSIS não encontrado. Instale-o e execute novamente com -Installer."
    }

    & $MakeNsis "/INPUTCHARSET" "UTF8" "/DAPP_VERSION=$Version" "/DAPP_VERSION_NUM=$WindowsVersion" "installer\QuantumScribe.nsi"
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao gerar o instalador com NSIS."
    }

    Write-Host "Instalador criado em: dist\QuantumScribe-Setup-$Version-Windows-x64.exe"
}
