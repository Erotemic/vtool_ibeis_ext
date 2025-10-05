@echo off
setlocal enabledelayedexpansion

set "VCPKG_ROOT=C:\vcpkg"
set "VCPKG_REPO=https://github.com/microsoft/vcpkg.git"
set "VCPKG_TRIPLET=x64-windows"

if not exist "%VCPKG_ROOT%" (
    echo [vtool_ibeis_ext] Cloning vcpkg into %VCPKG_ROOT%
    git clone --depth 1 "%VCPKG_REPO%" "%VCPKG_ROOT%"
    if errorlevel 1 (
        echo Failed to clone vcpkg repository.
        exit /b 1
    )
    call "%VCPKG_ROOT%\bootstrap-vcpkg.bat" -disableMetrics
    if errorlevel 1 (
        echo Failed to bootstrap vcpkg.
        exit /b 1
    )
) else (
    echo [vtool_ibeis_ext] Using existing vcpkg checkout at %VCPKG_ROOT%
)

"%VCPKG_ROOT%\vcpkg.exe" install opencv[core]:%VCPKG_TRIPLET% --recurse --clean-after-build
if errorlevel 1 (
    echo Failed to install OpenCV via vcpkg.
    exit /b 1
)

endlocal
