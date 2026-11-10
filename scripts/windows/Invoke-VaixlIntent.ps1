# Invoke only registered VAIXLNS Windows capabilities; never execute request text.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $RequestPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$startedAt = (Get-Date).ToUniversalTime().ToString("o")
$exitCode = 0
$result = $null

try {
    if (-not (Test-Path -LiteralPath $RequestPath -PathType Leaf)) {
        throw [System.ArgumentException]::new("RequestPath must identify an existing JSON file.")
    }

    $requestFile = (Resolve-Path -LiteralPath $RequestPath).Path
    $request = Get-Content -LiteralPath $requestFile -Raw -Encoding UTF8 |
        ConvertFrom-Json -ErrorAction Stop

    if ($null -eq $request -or $request -isnot [pscustomobject]) {
        throw [System.ArgumentException]::new("Request must be a JSON object.")
    }

    $expectedFields = @(
        "schemaVersion", "requestId", "intent", "target",
        "operation", "risk", "mode"
    )
    $actualFields = @($request.PSObject.Properties.Name)
    $fieldDifference = Compare-Object ($expectedFields | Sort-Object) ($actualFields | Sort-Object)
    if ($fieldDifference) {
        $result = [ordered]@{
            schemaVersion = "1.0"
            status = "BLOCKED"
            reason = "Request fields do not match the strict v1 envelope."
            requiredFields = $expectedFields
            suppliedFields = $actualFields
            executionPerformed = $false
            mutationPerformed = $false
        }
        $exitCode = 2
    }
    elseif ([string]$request.schemaVersion -ne "1.0") {
        $result = [ordered]@{
            schemaVersion = "1.0"
            status = "BLOCKED"
            reason = "Unsupported schemaVersion."
            executionPerformed = $false
            mutationPerformed = $false
        }
        $exitCode = 2
    }
    elseif ([string]$request.requestId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$') {
        $result = [ordered]@{
            schemaVersion = "1.0"
            status = "BLOCKED"
            reason = "requestId has an invalid format."
            executionPerformed = $false
            mutationPerformed = $false
        }
        $exitCode = 2
    }
    elseif ([string]::IsNullOrWhiteSpace([string]$request.intent) -or
            ([string]$request.intent).Length -lt 5 -or
            ([string]$request.intent).Length -gt 2000) {
        $result = [ordered]@{
            schemaVersion = "1.0"
            status = "BLOCKED"
            reason = "intent must contain 5 to 2000 characters."
            executionPerformed = $false
            mutationPerformed = $false
        }
        $exitCode = 2
    }
    elseif ([string]$request.target -ne "local_windows_host" -or
            [string]$request.operation -ne "windows.inventory.readonly" -or
            [string]$request.risk -ne "R0" -or
            [string]$request.mode -notin @("plan", "execute")) {
        $result = [ordered]@{
            schemaVersion = "1.0"
            status = "BLOCKED"
            reason = "Target, operation, risk, or mode is not allow-listed by v1."
            target = [string]$request.target
            operation = [string]$request.operation
            risk = [string]$request.risk
            mode = [string]$request.mode
            executionPerformed = $false
            mutationPerformed = $false
        }
        $exitCode = 2
    }
    elseif ([string]$request.mode -eq "plan") {
        $result = [ordered]@{
            schemaVersion = "1.0"
            requestId = [string]$request.requestId
            status = "PLANNED"
            operation = "windows.inventory.readonly"
            risk = "R0"
            startedAtUtc = $startedAt
            completedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
            executionPerformed = $false
            mutationPerformed = $false
            plannedActions = @(
                "Run the fixed read-only inventory collector.",
                "Write the JSON report under reports/windows/.",
                "Validate the report and calculate its SHA-256 hash."
            )
            limitations = @(
                "Plan mode does not inspect or modify the Windows host.",
                "Planning is not proof that backups are restorable."
            )
        }
    }
    else {
        $repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
        $collectorPath = Join-Path $PSScriptRoot "collect-readonly-inventory.ps1"
        if (-not (Test-Path -LiteralPath $collectorPath -PathType Leaf)) {
            throw [System.IO.FileNotFoundException]::new("Registered inventory handler is missing.")
        }

        $reportsRoot = Join-Path $repoRoot "reports\windows"
        if (-not (Test-Path -LiteralPath $reportsRoot -PathType Container)) {
            New-Item -ItemType Directory -Path $reportsRoot -Force | Out-Null
        }

        $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $reportName = "inventory-$($request.requestId)-$timestamp.json"
        $reportPath = Join-Path $reportsRoot $reportName

        # Fixed registered handler and controlled output path. No request text is evaluated as code.
        & $collectorPath -OutputPath $reportPath 2>&1 | Out-Null

        if (-not (Test-Path -LiteralPath $reportPath -PathType Leaf)) {
            throw [System.IO.InvalidDataException]::new("Inventory handler did not produce its report.")
        }

        $inventory = Get-Content -LiteralPath $reportPath -Raw -Encoding UTF8 |
            ConvertFrom-Json -ErrorAction Stop
        if ($inventory.reportType -ne "VAIXLNS_WINDOWS_READ_ONLY_INVENTORY" -or
            $inventory.mutationPerformed -ne $false) {
            throw [System.IO.InvalidDataException]::new("Inventory report failed the expected type or read-only assertion.")
        }

        $inconclusiveCount = @(
            $inventory.checks | Where-Object {
                $_.status -in @("UNKNOWN", "UNAVAILABLE")
            }
        ).Count
        $hash = (Get-FileHash -LiteralPath $reportPath -Algorithm SHA256).Hash
        $relativeReportPath = "reports/windows/$reportName"

        $result = [ordered]@{
            schemaVersion = "1.0"
            requestId = [string]$request.requestId
            status = $(if ($inconclusiveCount -gt 0) { "COMPLETED_WITH_UNKNOWN" } else { "COMPLETED" })
            operation = "windows.inventory.readonly"
            risk = "R0"
            startedAtUtc = $startedAt
            completedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
            executionPerformed = $true
            mutationPerformed = $false
            evidence = [ordered]@{
                reportPath = $relativeReportPath
                sha256 = $hash
                hashAlgorithm = "SHA256"
                checksTotal = @($inventory.checks).Count
                checksInconclusive = $inconclusiveCount
                reportJsonValidated = $true
            }
            limitations = @(
                "This inventory is a point-in-time snapshot, not proof of a restorable backup.",
                "UNKNOWN or UNAVAILABLE checks are not PASS.",
                "Review and redact host details before sharing the report."
            )
        }
    }
}
catch {
    $exitCode = 1
    $result = [ordered]@{
        schemaVersion = "1.0"
        status = "FAILED"
        errorType = $_.Exception.GetType().Name
        message = $_.Exception.Message
        startedAtUtc = $startedAt
        completedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
        mutationPerformed = $false
        limitations = @("Failure output is not proof that the host is healthy or recoverable.")
    }
}

$result | ConvertTo-Json -Depth 8
exit $exitCode
