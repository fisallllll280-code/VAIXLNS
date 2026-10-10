[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
)

$ErrorActionPreference = "Stop"
$PyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($PyLauncher) {
    & py -3.11 --version
    if ($LASTEXITCODE -ne 0) { throw "Python 3.11 is required. Install Python 3.11+ and retry." }
    & py -3.11 -m venv (Join-Path $RepositoryRoot ".venv-arcx")
} else {
    $Python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $Python) { throw "Python 3.11+ is required." }
    & python --version
    & python -m venv (Join-Path $RepositoryRoot ".venv-arcx")
}
if ($LASTEXITCODE -ne 0) { throw "Failed to create the ARC-X virtual environment." }

$VenvPython = Join-Path $RepositoryRoot ".venv-arcx/Scripts/python.exe"
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }
& $VenvPython -m pip install -r (Join-Path $RepositoryRoot "requirements-arcx-mcp.txt")
if ($LASTEXITCODE -ne 0) { throw "ARC-X dependency installation failed." }
& $VenvPython -m unittest discover -s (Join-Path $RepositoryRoot "tests") -p "test_arcx_mcp_server.py" -v
if ($LASTEXITCODE -ne 0) { throw "ARC-X MCP tests failed." }
Write-Host "ARC-X MCP prototype environment and tests completed."
Write-Host "Set ARCX_REPOSITORY_ROOT before starting the server."
