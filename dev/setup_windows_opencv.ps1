$ErrorActionPreference = "Stop"

$Triplet = "x64-windows"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$vcpkgRoot = Join-Path $projectRoot 'vcpkg'

Write-Host "Project root: $projectRoot"
Write-Host "Using vcpkg root: $vcpkgRoot"

if (-not (Test-Path $vcpkgRoot)) {
    Write-Host "Cloning vcpkg..."
    git clone --depth 1 https://github.com/microsoft/vcpkg $vcpkgRoot
} else {
    Write-Host "Reusing existing vcpkg checkout"
}

Push-Location $vcpkgRoot
try {
    $bootstrapPath = Join-Path $vcpkgRoot 'bootstrap-vcpkg.bat'
    $vcpkgExe = Join-Path $vcpkgRoot 'vcpkg.exe'
    if (-not (Test-Path $vcpkgExe)) {
        Write-Host "Bootstrapping vcpkg..."
        & $bootstrapPath
        if ($LASTEXITCODE -ne 0) {
            throw "bootstrap-vcpkg failed with exit code $LASTEXITCODE"
        }
    }

    $args = @('install', "opencv[core]:$Triplet", '--recurse')
    Write-Host "Installing opencv via vcpkg..."
    & $vcpkgExe @args
    if ($LASTEXITCODE -ne 0) {
        throw "vcpkg install failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
