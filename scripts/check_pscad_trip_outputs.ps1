param(
    [string]$RunDir = "C:\pscad_work\trip_shell_stage16\PSCAD\WFCASE.gf46",
    [string]$Namespace = "WFCASE",
    [string]$CaseCsv = "config\offline_trip_cases.csv",
    [string]$CaseId = "baseline_manual_verified",
    [double]$TimeToleranceS = 0.015,
    [double]$NoTripSentinelS = 90.0
)

$ErrorActionPreference = "Stop"

function Resolve-RepoPath([string]$Path) {
    if ([System.IO.Path]::IsPathRooted($Path)) {
        return $Path
    }
    return (Join-Path (Get-Location) $Path)
}

function Read-OutRows([string]$Path) {
    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($line in [System.IO.File]::ReadLines($Path)) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }
        $parts = $line.Trim() -split '\s+'
        $values = @()
        foreach ($part in $parts) {
            $values += [double]::Parse($part.Replace("D", "E"), [System.Globalization.CultureInfo]::InvariantCulture)
        }
        $rows.Add($values)
    }
    return $rows
}

function Get-TransitionTime($Rows, [int]$Column, [double]$Threshold) {
    $previous = $Rows[0][$Column]
    foreach ($row in $Rows | Select-Object -Skip 1) {
        $current = $row[$Column]
        if (($previous -lt $Threshold) -and ($current -ge $Threshold)) {
            return $row[0]
        }
        $previous = $current
    }
    return $null
}

function Get-ChannelIndex([xml]$OutputXml, [string]$SignalName) {
    $node = $OutputXml.Output.List.Analog | Where-Object { $_.name -like "*:$SignalName" } | Select-Object -First 1
    if ($null -eq $node) {
        throw "Could not find channel '$SignalName' in $($Namespace).infx."
    }
    return [int]$node.index
}

function Get-ChannelRowsAndColumn([xml]$OutputXml, [string]$SignalName) {
    $index = Get-ChannelIndex $OutputXml $SignalName
    $fileNumber = [math]::Floor($index / 10) + 1
    $column = ($index % 10) + 1
    $outPath = Join-Path $RunDir ("{0}_{1:00}.out" -f $Namespace, $fileNumber)
    if (!(Test-Path -LiteralPath $outPath)) {
        throw "Expected output file not found for $SignalName : $outPath"
    }
    return @{
        Rows = Read-OutRows $outPath
        Column = $column
        File = $outPath
    }
}

$caseCsvPath = Resolve-RepoPath $CaseCsv
$case = Import-Csv -LiteralPath $caseCsvPath | Where-Object { $_.case_id -eq $CaseId } | Select-Object -First 1
if ($null -eq $case) {
    throw "Case '$CaseId' not found in $caseCsvPath"
}

$infxPath = Join-Path $RunDir "$Namespace.infx"
if (!(Test-Path -LiteralPath $infxPath)) {
    throw "Compiled output index not found: $infxPath"
}
[xml]$outputXml = Get-Content -LiteralPath $infxPath

$checks = @(
    @{ Farm = "WF38"; Expected = [double]$case.wf38_trip_time_s },
    @{ Farm = "WF35"; Expected = [double]$case.wf35_trip_time_s },
    @{ Farm = "WF33"; Expected = [double]$case.wf33_trip_time_s }
)

$results = @()
foreach ($check in $checks) {
    $farm = $check.Farm
    $expected = $check.Expected
    $cmd = Get-ChannelRowsAndColumn $outputXml "${farm}_TRIP_CMD"
    $state = Get-ChannelRowsAndColumn $outputXml "${farm}_BRK_STATE"
    $cmdTime = Get-TransitionTime $cmd.Rows $cmd.Column 0.5
    $stateTime = Get-TransitionTime $state.Rows $state.Column 1.0
    if ($expected -ge $NoTripSentinelS) {
        $cmdOk = $null -eq $cmdTime
        $stateOk = $null -eq $stateTime
    } else {
        $cmdOk = ($null -ne $cmdTime) -and ([math]::Abs($cmdTime - $expected) -le $TimeToleranceS)
        $stateOk = ($null -ne $stateTime) -and ([math]::Abs($stateTime - $expected) -le $TimeToleranceS)
    }
    $results += [pscustomobject]@{
        Farm = $farm
        ExpectedTripTimeS = $expected
        CommandTransitionS = $cmdTime
        BreakerStateTransitionS = $stateTime
        CommandOk = $cmdOk
        BreakerStateOk = $stateOk
    }
}

$results | Format-Table -AutoSize

$failed = $results | Where-Object { -not ($_.CommandOk -and $_.BreakerStateOk) }
if ($failed.Count -gt 0) {
    throw "One or more wind-farm trip checks failed."
}

Write-Host "All PSCAD trip checks passed for case '$CaseId'."
