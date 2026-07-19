param([string]$Version = "")

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

if (-not $Version) {
    $VersionLine = Get-Content "localwhisper\__init__.py" | Select-String '__version__\s*=\s*"([^"]+)"'
    if (-not $VersionLine) { throw "Não foi possível determinar a versão." }
    $Version = $VersionLine.Matches[0].Groups[1].Value
}

$Dist = Join-Path $ProjectRoot "dist"
New-Item -ItemType Directory -Force -Path $Dist | Out-Null
$ComponentRoot = Join-Path $ProjectRoot ".component-build"
$ResolvedRoot = [IO.Path]::GetFullPath($ProjectRoot).TrimEnd('\') + '\'
$ResolvedComponent = [IO.Path]::GetFullPath($ComponentRoot)
if (-not $ResolvedComponent.StartsWith($ResolvedRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Diretório temporário fora do projeto: $ResolvedComponent"
}
if (Test-Path -LiteralPath $ComponentRoot) { Remove-Item -LiteralPath $ComponentRoot -Recurse -Force }
New-Item -ItemType Directory -Path $ComponentRoot | Out-Null

try {
    # CUDA: ambiente separado; nenhum pacote NVIDIA toca o build do Core.
    $CudaVenv = Join-Path $ComponentRoot "cuda-venv"
    python -m venv $CudaVenv
    $CudaPython = Join-Path $CudaVenv "Scripts\python.exe"
    & $CudaPython -m pip install --no-deps --require-hashes -r requirements-cuda-component.txt
    if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar o runtime CUDA verificado." }

    $CudaStage = Join-Path $ComponentRoot "cuda-stage"
    $SitePackages = Join-Path $CudaVenv "Lib\site-packages"
    $CudaFiles = @(
        "nvidia\cublas\bin\cublas64_12.dll",
        "nvidia\cublas\bin\cublasLt64_12.dll",
        "nvidia\cudnn\bin\cudnn64_9.dll",
        "nvidia\cudnn\bin\cudnn_ops64_9.dll",
        "nvidia\cudnn\bin\cudnn_cnn64_9.dll",
        "nvidia\cudnn\bin\cudnn_graph64_9.dll",
        "nvidia\cudnn\bin\cudnn_heuristic64_9.dll",
        "nvidia\cudnn\bin\cudnn_engines_runtime_compiled64_9.dll",
        "nvidia\cudnn\bin\cudnn_engines_tensor_ir64_9.dll",
        "nvidia\cudnn\bin\cudnn_ext64_9.dll"
    )
    foreach ($Relative in $CudaFiles) {
        $Source = Join-Path $SitePackages $Relative
        if (-not (Test-Path -LiteralPath $Source)) { throw "DLL CUDA ausente: $Relative" }
        $Target = Join-Path $CudaStage $Relative
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
        Copy-Item -LiteralPath $Source -Destination $Target
    }
    $CudaLicenses = @{
        "NVIDIA-cuBLAS-LICENSE.txt" = "nvidia_cublas_cu12-*.dist-info\licenses\License.txt"
        "NVIDIA-cuDNN-LICENSE.txt" = "nvidia_cudnn_cu12-*.dist-info\licenses\License.txt"
    }
    foreach ($TargetName in $CudaLicenses.Keys) {
        $License = Get-ChildItem -Path (Join-Path $SitePackages $CudaLicenses[$TargetName]) -File | Select-Object -First 1
        if (-not $License) { throw "Licença obrigatória não encontrada: $TargetName" }
        Copy-Item -LiteralPath $License.FullName -Destination (Join-Path $CudaStage $TargetName)
    }
    $CudaZip = Join-Path $Dist "QuantumScribe-CUDA-$Version-Windows-x64.zip"
    if (Test-Path -LiteralPath $CudaZip) { Remove-Item -LiteralPath $CudaZip -Force }
    Compress-Archive -Path (Join-Path $CudaStage "*") -DestinationPath $CudaZip -CompressionLevel Optimal

    # Silero: baixa a wheel com hash fixado e extrai somente o modelo ONNX.
    $VadDownload = Join-Path $ComponentRoot "vad-download"
    $VadStage = Join-Path $ComponentRoot "vad-stage"
    New-Item -ItemType Directory -Path $VadDownload, $VadStage | Out-Null
    python -m pip download --require-hashes --no-deps -r requirements-vad-component.txt -d $VadDownload
    if ($LASTEXITCODE -ne 0) { throw "Falha ao baixar o modelo Silero verificado." }
    $Wheel = Get-ChildItem -LiteralPath $VadDownload -Filter "silero_vad-*.whl" -File | Select-Object -First 1
    if (-not $Wheel) { throw "Wheel do Silero não encontrada." }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $Archive = [IO.Compression.ZipFile]::OpenRead($Wheel.FullName)
    try {
        $Entry = $Archive.GetEntry("silero_vad/data/silero_vad.onnx")
        if (-not $Entry) { throw "Modelo ONNX não encontrado na wheel verificada." }
        [IO.Compression.ZipFileExtensions]::ExtractToFile($Entry, (Join-Path $VadStage "silero_vad.onnx"), $true)
        $LicenseEntry = $Archive.GetEntry("silero_vad-6.2.1.dist-info/licenses/LICENSE")
        if (-not $LicenseEntry) { throw "Licença MIT do Silero não encontrada." }
        [IO.Compression.ZipFileExtensions]::ExtractToFile($LicenseEntry, (Join-Path $VadStage "SILERO-LICENSE.txt"), $true)
    } finally {
        $Archive.Dispose()
    }
    $VadZip = Join-Path $Dist "QuantumScribe-SileroVAD-$Version-Windows-x64.zip"
    if (Test-Path -LiteralPath $VadZip) { Remove-Item -LiteralPath $VadZip -Force }
    Compress-Archive -Path (Join-Path $VadStage "*") -DestinationPath $VadZip -CompressionLevel Optimal

    Write-Host "Componentes criados:"
    Write-Host "  $CudaZip"
    Write-Host "  $VadZip"
} finally {
    if (Test-Path -LiteralPath $ComponentRoot) { Remove-Item -LiteralPath $ComponentRoot -Recurse -Force }
}
