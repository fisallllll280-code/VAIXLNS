# Read-only Windows inventory for VAIXLNS
# This script does not change boot configuration, services, drivers, security settings, or updates.
# It never reads BitLocker recovery keys or credential stores.

[CmdletBinding()]
param(
    [Parameter()]
    [string] $OutputPath = (Join-Path (Get-Location) ("vaixlns-windows-inventory-{0}.json" -f (Get-Date -Format "yyyyMMdd-HHmmss")))
)

$ErrorActionPreference = "Continue"
$checks = [System.Collections.Generic.List[object]]::new()

function Add-Check {
    param(
        [string] $Name,
        [string] $Status,
        [object] $Data,
        [string] $Note = ""
    )
    $checks.Add([ordered]@{
        name = $Name
        status = $Status
        data = $Data
        note = $Note
    })
}

$os = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction SilentlyContinue
if ($os) {
    Add-Check -Name "os" -Status "OK" -Data ([ordered]@{
        caption = $os.Caption
        version = $os.Version
        buildNumber = $os.BuildNumber
        architecture = $os.OSArchitecture
        lastBootUpTime = $os.LastBootUpTime
    })
} else {
    Add-Check -Name "os" -Status "UNAVAILABLE" -Data $null -Note "Win32_OperatingSystem query failed."
}

$computer = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction SilentlyContinue
if ($computer) {
    Add-Check -Name "computer" -Status "OK" -Data ([ordered]@{
        manufacturer = $computer.Manufacturer
        model = $computer.Model
        systemType = $computer.SystemType
        totalPhysicalMemoryBytes = $computer.TotalPhysicalMemory
    })
} else {
    Add-Check -Name "computer" -Status "UNAVAILABLE" -Data $null
}

try {
    $secureBoot = Confirm-SecureBootUEFI -ErrorAction Stop
    Add-Check -Name "secureBoot" -Status "OK" -Data ([ordered]@{ enabled = [bool]$secureBoot })
} catch {
    Add-Check -Name "secureBoot" -Status "UNKNOWN" -Data $null -Note "Unavailable on legacy BIOS, unsupported firmware, or insufficient permissions; no setting was changed."
}

try {
    $bcd = (& bcdedit.exe /enum '{current}' 2>&1 | Out-String).Trim()
    $bcdExit = $LASTEXITCODE
    if ($bcdExit -eq 0) {
        Add-Check -Name "bcdCurrentEntry" -Status "OK" -Data $bcd
    } else {
        Add-Check -Name "bcdCurrentEntry" -Status "UNKNOWN" -Data $bcd -Note "bcdedit returned a non-zero exit code."
    }
} catch {
    Add-Check -Name "bcdCurrentEntry" -Status "UNAVAILABLE" -Data $null -Note $_.Exception.Message
}

try {
    $winre = (& reagentc.exe /info 2>&1 | Out-String).Trim()
    $winreExit = $LASTEXITCODE
    Add-Check -Name "windowsRecoveryEnvironment" -Status $(if ($winreExit -eq 0) { "OK" } else { "UNKNOWN" }) -Data $winre
} catch {
    Add-Check -Name "windowsRecoveryEnvironment" -Status "UNAVAILABLE" -Data $null -Note $_.Exception.Message
}

try {
    if (Get-Command Get-BitLockerVolume -ErrorAction SilentlyContinue) {
        $volumes = @(Get-BitLockerVolume -ErrorAction Stop | Select-Object MountPoint, VolumeType, VolumeStatus, ProtectionStatus, EncryptionMethod, EncryptionPercentage)
        Add-Check -Name "bitLockerStatus" -Status "OK" -Data $volumes -Note "Status only; recovery keys are never collected."
    } else {
        Add-Check -Name "bitLockerStatus" -Status "UNKNOWN" -Data $null -Note "BitLocker cmdlet unavailable on this edition or host."
    }
} catch {
    Add-Check -Name "bitLockerStatus" -Status "UNKNOWN" -Data $null -Note "Status query failed; no keys were accessed."
}

try {
    $disk = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DriveType=3" -ErrorAction Stop |
        Select-Object DeviceID, FileSystem, Size, FreeSpace
    Add-Check -Name "fixedDisks" -Status "OK" -Data @($disk)
} catch {
    Add-Check -Name "fixedDisks" -Status "UNAVAILABLE" -Data $null -Note $_.Exception.Message
}

$report = [ordered]@{
    schemaVersion = "1.0"
    reportType = "VAIXLNS_WINDOWS_READ_ONLY_INVENTORY"
    generatedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
    machineName = $env:COMPUTERNAME
    currentUser = $env:USERNAME
    readOnly = $true
    mutationPerformed = $false
    checks = @($checks)
    warnings = @(
        "This report is a point-in-time inventory, not proof that a backup is restorable.",
        "UNKNOWN means the check could not be established; do not treat it as PASS.",
        "Review the report before sharing; host and configuration details may be sensitive."
    )
}

$json = $report | ConvertTo-Json -Depth 8
$parent = Split-Path -Parent $OutputPath
if ($parent -and -not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}
Set-Content -LiteralPath $OutputPath -Value $json -Encoding utf8
Write-Output ("Inventory report written to: " + (Resolve-Path -LiteralPath $OutputPath).Path)
Write-Output "Read-only mode: no Windows settings were changed."
