[CmdletBinding()]
param([string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path)
$ErrorActionPreference = "Stop"
$ResolvedRoot = (Resolve-Path $RepositoryRoot).Path
$VenvPython = Join-Path $ResolvedRoot ".venv-model-mcp/Scripts/python.exe"
if (-not (Test-Path $VenvPython)) { throw "Model gateway environment missing. Create .venv-model-mcp and install requirements-model-mcp.txt first." }
$env:PYTHONPATH = $ResolvedRoot
& $VenvPython -m tools.model_mcp.server
if ($LASTEXITCODE -ne 0) { throw "VAIXLNS model gateway MCP exited with code $LASTEXITCODE." }
