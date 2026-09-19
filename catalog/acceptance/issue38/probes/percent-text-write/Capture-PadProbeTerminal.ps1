[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][int]$TargetProcessId,
    [Parameter(Mandatory = $true)][string]$FlowName,
    [Parameter(Mandatory = $true)][string]$ResultPath,
    [Parameter(Mandatory = $true)][string]$EvidencePath
)

$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($PSScriptRoot)
$result = (Resolve-Path -LiteralPath $ResultPath).Path
$evidence = [IO.Path]::GetFullPath($EvidencePath)
foreach ($path in @($result, $evidence)) {
    if (-not $path.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Probe paths only'
    }
}
if (Test-Path -LiteralPath $evidence) { throw 'Evidence exists' }

Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$process = Get-Process -Id $TargetProcessId
if ($process.ProcessName -cne 'PAD.Designer' -or $process.MainWindowTitle -cne ('Power Automate | ' + $FlowName)) {
    throw 'Target flow mismatch'
}
$window = [Windows.Automation.AutomationElement]::FromHandle($process.MainWindowHandle)

function Find-ById([Windows.Automation.AutomationElement]$Root, [string]$Id) {
    $condition = New-Object Windows.Automation.PropertyCondition(
        [Windows.Automation.AutomationElement]::AutomationIdProperty,
        $Id
    )
    @($Root.FindAll([Windows.Automation.TreeScope]::Descendants, $condition))
}

$search = @(Find-ById $window 'VariablesPanelSearchVariablesSearchBox')
$list = @(Find-ById $window 'VariablesPanelFlowVariablesList')
if ($search.Count -ne 1 -or $list.Count -ne 1) { throw 'Variables controls are not unique' }
$searchPattern = $search[0].GetCurrentPattern([Windows.Automation.ValuePattern]::Pattern)
$originalFilter = $searchPattern.Current.Value

function Read-Variable([string]$Name) {
    $searchPattern.SetValue($Name)
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    $matches = @()
    do {
        Start-Sleep -Milliseconds 150
        $items = @(Find-ById $list[0] 'VariablesListItem')
        $matches = @($items | Where-Object { $_.Current.Name -ceq $Name })
    } while ($matches.Count -ne 1 -and [DateTime]::UtcNow -lt $deadline)
    if ($matches.Count -ne 1) { throw ('Variable not unique: ' + $Name) }
    $previews = @(Find-ById $matches[0] 'VariablePreviewTextBlock')
    if ($previews.Count -ne 1) { throw ('Variable preview not unique: ' + $Name) }
    [ordered]@{
        preview = [string]$previews[0].Current.Name
        help_text = [string]$previews[0].Current.HelpText
        raw_exact = ([string]$previews[0].Current.Name -ceq [string]$previews[0].Current.HelpText)
        trimmed_exact = ([string]$previews[0].Current.Name.Trim() -ceq [string]$previews[0].Current.HelpText.Trim())
    }
}

try {
    $probeState = Read-Variable 'ProbeState'
    $powershellOutput = Read-Variable 'PowershellOutput'
}
finally {
    $searchPattern.SetValue($originalFilter)
}
$auditText = $powershellOutput.help_text.Trim()
$audit = $auditText | ConvertFrom-Json

$start = @(Find-ById $window 'StartFlowButton')
$ready = @(Find-ById $window 'Flow_status_ready')
$running = @(Find-ById $window 'Flow_status_running')
$errorState = @(Find-ById $window 'Flow_status_error')
$checks = [ordered]@{
    ready_visible = ($ready.Count -eq 1 -and -not $ready[0].Current.IsOffscreen)
    start_enabled = ($start.Count -eq 1 -and $start[0].Current.IsEnabled)
    running_absent = ($running.Count -eq 0)
    error_status_absent = ($errorState.Count -eq 0)
    final_marker = ($probeState.preview -ceq 'FORMAT_SANDWICH_FINISHED' -and $probeState.raw_exact)
    powershell_output_trimmed_exact = $powershellOutput.trimmed_exact
    immediate_before_text = ($audit.b -ceq 'BEFORE_TEXT' -and $audit.bt -ceq 'System.String')
    immediate_after_text = ($audit.a -ceq '100%' -and $audit.at -ceq 'System.String')
    immediate_number_format_restored = ($audit.bf -ceq $audit.af)
    immediate_prefix_absent = ([string]::IsNullOrEmpty([string]$audit.ap))
    no_excel_process = (@(Get-Process -Name EXCEL -ErrorAction SilentlyContinue).Count -eq 0)
    result_exists = (Test-Path -LiteralPath $result -PathType Leaf)
}
$passed = @($checks.Values | Where-Object { -not $_ }).Count -eq 0
$record = [ordered]@{
    schema_version = 1
    kind = 'ISSUE38_PERCENT_TEXT_PAD_TERMINAL'
    observed_at = [DateTime]::UtcNow.ToString('o')
    flow_name = $FlowName
    process_id = $TargetProcessId
    execution_requested = $false
    status = if ($passed) { 'TERMINAL_CONFIRMED' } else { 'TERMINAL_NOT_CONFIRMED' }
    ui = [ordered]@{
        ready = @($ready | ForEach-Object { [ordered]@{ name = $_.Current.Name; enabled = $_.Current.IsEnabled; offscreen = $_.Current.IsOffscreen } })
        start = @($start | ForEach-Object { [ordered]@{ name = $_.Current.Name; enabled = $_.Current.IsEnabled; offscreen = $_.Current.IsOffscreen } })
        running_count = $running.Count
        error_count = $errorState.Count
    }
    variables = [ordered]@{
        ProbeState = $probeState
        PowershellOutput = $powershellOutput
        parsed_powershell_output = $audit
    }
    result = [ordered]@{
        path = $result
        bytes = (Get-Item -LiteralPath $result).Length
        sha256 = (Get-FileHash -LiteralPath $result -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    checks = $checks
}
$stream = [IO.File]::Open($evidence, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
try {
    $bytes = (New-Object Text.UTF8Encoding($false)).GetBytes(($record | ConvertTo-Json -Depth 12))
    $stream.Write($bytes, 0, $bytes.Length)
}
finally { $stream.Dispose() }
$record | ConvertTo-Json -Depth 12
if (-not $passed) { exit 2 }
