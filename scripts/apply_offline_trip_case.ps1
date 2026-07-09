param(
    [string]$TemplateProject = "C:\pscad_work\trip_shell_stage16\PSCAD\WFMR1.pscx",
    [string]$CaseCsv = "config\offline_trip_cases.csv",
    [string]$CaseId = "baseline_manual_verified",
    [string]$OutputProject = "C:\pscad_work\trip_shell_stage16\PSCAD\WFCASE.pscx",
    [string]$OutputNamespace = "WFCASE",
    [string]$TemplateNamespace = "WFTripShell"
)

$ErrorActionPreference = "Stop"

function Resolve-RepoPath([string]$Path) {
    if ([System.IO.Path]::IsPathRooted($Path)) {
        return $Path
    }
    return (Join-Path (Get-Location) $Path)
}

function Set-TripVariable([string]$Text, [string]$Name, [string]$Value) {
    $escapedName = [regex]::Escape($Name)
    $blockPattern = "(?s)<User\b(?=[^>]*defn=`"master:var`")[\s\S]*?</User>"
    $valuePattern = "(?s)(<param name=`"Value`" value=`")[^`"]*(`" />)"
    $blocks = [regex]::Matches($Text, $blockPattern) | Where-Object {
        $_.Value -match "<param name=`"Name`" value=`"$escapedName`" />"
    }
    if ($blocks.Count -ne 1) {
        throw "Expected exactly one PSCAD Variable component named $Name, found $($blocks.Count)."
    }
    $block = $blocks[0]
    $newBlock = [regex]::Replace($block.Value, $valuePattern, "`${1}$Value`${2}", 1)
    return $Text.Substring(0, $block.Index) + $newBlock + $Text.Substring($block.Index + $block.Length)
}

function Set-CompareThreshold([string]$Text, [string]$Name, [string]$Value) {
    $escapedName = [regex]::Escape($Name)
    $blockPattern = "(?s)<User\b(?=[^>]*defn=`"master:compare`")[\s\S]*?</User>"
    $thresholdPattern = "(?s)(<param name=`"X`" value=`")[^`"]*(`" />)"
    $blocks = [regex]::Matches($Text, $blockPattern) | Where-Object {
        $_.Value -match "<param name=`"X`" value=`"$escapedName`" />"
    }
    if ($blocks.Count -ne 1) {
        throw "Expected exactly one PSCAD Compare component using $Name, found $($blocks.Count)."
    }
    $block = $blocks[0]
    $newBlock = [regex]::Replace($block.Value, $thresholdPattern, "`${1}$Value`${2}", 1)
    return $Text.Substring(0, $block.Index) + $newBlock + $Text.Substring($block.Index + $block.Length)
}

function Format-Seconds($Value) {
    $number = [double]::Parse([string]$Value, [System.Globalization.CultureInfo]::InvariantCulture)
    return $number.ToString("0.######", [System.Globalization.CultureInfo]::InvariantCulture)
}

$caseCsvPath = Resolve-RepoPath $CaseCsv
if (!(Test-Path -LiteralPath $TemplateProject)) {
    throw "Template project not found: $TemplateProject"
}
if (!(Test-Path -LiteralPath $caseCsvPath)) {
    throw "Case CSV not found: $caseCsvPath"
}

$case = Import-Csv -LiteralPath $caseCsvPath | Where-Object { $_.case_id -eq $CaseId } | Select-Object -First 1
if ($null -eq $case) {
    throw "Case '$CaseId' not found in $caseCsvPath"
}

$outputDir = Split-Path -Parent $OutputProject
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

$text = [System.IO.File]::ReadAllText($TemplateProject)
$text = $text -replace '<project name="[^"]+"', ('<project name="' + $OutputNamespace + '"')
$text = $text.Replace($TemplateNamespace + ":", $OutputNamespace + ":")
$wf38TripTime = Format-Seconds $case.wf38_trip_time_s
$wf35TripTime = Format-Seconds $case.wf35_trip_time_s
$wf33TripTime = Format-Seconds $case.wf33_trip_time_s
$text = Set-TripVariable $text "WF38_TRIP_TIME" $wf38TripTime
$text = Set-TripVariable $text "WF35_TRIP_TIME" $wf35TripTime
$text = Set-TripVariable $text "WF33_TRIP_TIME" $wf33TripTime
$text = Set-CompareThreshold $text "WF38_TRIP_TIME" $wf38TripTime
$text = Set-CompareThreshold $text "WF35_TRIP_TIME" $wf35TripTime
$text = Set-CompareThreshold $text "WF33_TRIP_TIME" $wf33TripTime

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($OutputProject, $text, $utf8NoBom)

$templateMeta = [System.IO.Path]::ChangeExtension($TemplateProject, ".psmx")
$outputMeta = [System.IO.Path]::ChangeExtension($OutputProject, ".psmx")
if (Test-Path -LiteralPath $templateMeta) {
    $metaText = [System.IO.File]::ReadAllText($templateMeta)
    $metaText = $metaText -replace '<Meta name="[^"]+"', ('<Meta name="' + $OutputNamespace + '"')
    $metaText = $metaText.Replace($TemplateNamespace + ":", $OutputNamespace + ":")
    [System.IO.File]::WriteAllText($outputMeta, $metaText, $utf8NoBom)
}

Write-Host "Wrote PSCAD offline trip case:"
Write-Host "  Case: $CaseId"
Write-Host "  Project: $OutputProject"
Write-Host "  Namespace: $OutputNamespace"
Write-Host "  WF38_TRIP_TIME = $($case.wf38_trip_time_s) s"
Write-Host "  WF35_TRIP_TIME = $($case.wf35_trip_time_s) s"
Write-Host "  WF33_TRIP_TIME = $($case.wf33_trip_time_s) s"
