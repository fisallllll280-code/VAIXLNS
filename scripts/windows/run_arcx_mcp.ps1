[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepositoryRoot
)

$ErrorActionPreference = "Stop"
$ResolvedRoot = (Resolve-Path $RepositoryRoot).Path
$VenvPython = Join-Path $PSScriptRoot "../../.venv-arcx/Scripts/python.exe"
$VenvPython = (Resolve-Path $VenvPython).Path
$env:ARCX_REPOSITORY_ROOT = $ResolvedRoot
& $VenvPython -m tools.arcx_mcp.server
if ($LASTEXITCODE -ne 0) { throw "ARC-X MCP server exited with code $LASTEXITCODE." }
