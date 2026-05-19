param(
    [ValidateSet("gui", "cli", "both")]
    [string]$Target = "gui",

    [switch]$Clean
)

$ErrorActionPreference = "Stop"

function Assert-Command {
    param([string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name not found. Install $Name and make sure it is available on PATH."
    }
}

function Invoke-PyInstaller {
    param(
        [string]$Name,
        [string]$EntryPoint,
        [switch]$Windowed
    )

    $pyInstallerArgs = @(
        "run", "pyinstaller",
        "-F",
        "-n", $Name,
        "--clean",
        "--noconfirm",
        "--collect-all", "PyMuPDF",
        "--collect-all", "numpy",
        "--collect-all", "lxml",
        "--icon", "assets\icon\app.ico"
    )

    if ($Windowed) {
        $pyInstallerArgs += "--windowed"
    }

    $pyInstallerArgs += $EntryPoint
    & uv @pyInstallerArgs
}

Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))

Assert-Command "uv"

if ($Clean) {
    Remove-Item -Recurse -Force "build", "dist" -ErrorAction SilentlyContinue
}

if (-not (Test-Path ".venv")) {
    & uv venv
}

& uv sync
& uv pip install pyinstaller

if ($Target -eq "gui" -or $Target -eq "both") {
    Invoke-PyInstaller -Name "pdf-tools-gui" -EntryPoint "pdf_tools\gui_main.py" -Windowed
}

if ($Target -eq "cli" -or $Target -eq "both") {
    Invoke-PyInstaller -Name "pdf-tools" -EntryPoint "pdf_tools\__main__.py"
}

Write-Host "Build output:"
Get-ChildItem "dist" -Filter "*.exe" | ForEach-Object {
    Write-Host "  $($_.FullName)"
}
