[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][int]$TargetProcessId,
    [Parameter(Mandatory = $true)][string]$FlowName,
    [Parameter(Mandatory = $true)][string]$EvidencePath,
    [Parameter(Mandatory = $true)][string[]]$VariableName
)

$ErrorActionPreference = 'Stop'
$output = [IO.Path]::GetFullPath($EvidencePath)
if (Test-Path -LiteralPath $output) { throw 'Evidence exists; variable inspection not requested' }
if (-not (Test-Path -LiteralPath ([IO.Path]::GetDirectoryName($output)) -PathType Container)) {
    throw 'Evidence directory missing; variable inspection not requested'
}
if ($VariableName.Count -eq 0 -or @($VariableName | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count) {
    throw 'Exact variable names are required'
}

Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes

function Find-ByAutomationId {
    param($Root, [string]$AutomationId)
    $condition = New-Object Windows.Automation.PropertyCondition(
        [Windows.Automation.AutomationElement]::AutomationIdProperty,
        $AutomationId
    )
    @($Root.FindAll([Windows.Automation.TreeScope]::Descendants, $condition))
}

$record = [ordered]@{
    schema_version = 1
    observed_at = [DateTime]::UtcNow.ToString('o')
    flow_name = $FlowName
    process_id = $TargetProcessId
    filter_method = 'VariablesPanelSearchVariablesSearchBox ValuePattern with exact per-variable name'
    execution_requested = $false
    status = 'NOT_STARTED'
    variables = [ordered]@{}
    error = $null
}

$searchPattern = $null
$originalFilter = $null
try {
    $process = Get-Process -Id $TargetProcessId
    if ($process.ProcessName -cne 'PAD.Designer') { throw 'Target process mismatch' }
    $windowCondition = New-Object Windows.Automation.PropertyCondition(
        [Windows.Automation.AutomationElement]::ProcessIdProperty,
        $TargetProcessId
    )
    $windows = @([Windows.Automation.AutomationElement]::RootElement.FindAll(
        [Windows.Automation.TreeScope]::Children,
        $windowCondition
    ) | Where-Object { $_.Current.Name -ceq ('Power Automate | ' + $FlowName) })
    if ($windows.Count -ne 1) { throw 'Target flow mismatch' }
    $window = $windows[0]

    $searches = @(Find-ByAutomationId -Root $window -AutomationId 'VariablesPanelSearchVariablesSearchBox')
    $lists = @(Find-ByAutomationId -Root $window -AutomationId 'VariablesPanelFlowVariablesList')
    if ($searches.Count -ne 1 -or $lists.Count -ne 1) { throw 'Variables panel controls are not unique' }
    $searchPattern = $searches[0].GetCurrentPattern([Windows.Automation.ValuePattern]::Pattern)
    $originalFilter = $searchPattern.Current.Value

    foreach ($name in $VariableName) {
        $searchPattern.SetValue($name)
        $deadline = [DateTime]::UtcNow.AddSeconds(4)
        $items = @()
        do {
            Start-Sleep -Milliseconds 100
            $items = @(Find-ByAutomationId -Root $lists[0] -AutomationId 'VariablesListItem' | Where-Object {
                $_.Current.Name -ceq $name
            })
        } while ($items.Count -eq 0 -and [DateTime]::UtcNow -lt $deadline)
        if ($items.Count -ne 1) { throw ('Variable is not uniquely visible: ' + $name) }
        $nameParts = @(Find-ByAutomationId -Root $items[0] -AutomationId 'VariableTextBlock')
        $previewParts = @(Find-ByAutomationId -Root $items[0] -AutomationId 'VariablePreviewTextBlock')
        if ($nameParts.Count -ne 1 -or $previewParts.Count -ne 1 -or $nameParts[0].Current.Name -cne $name) {
            throw ('Variable readback structure mismatch: ' + $name)
        }
        $preview = [string]$previewParts[0].Current.Name
        $help = [string]$previewParts[0].Current.HelpText
        if (-not [string]::IsNullOrEmpty($help) -and $help -cne $preview) {
            throw ('Variable preview/help mismatch: ' + $name)
        }
        $record.variables[$name] = [ordered]@{
            preview = $preview
            help_text = $help
            preview_help_exact = ($preview -ceq $help)
        }
    }
    $record.status = 'OBSERVED_EXACT_FILTERED_VARIABLES'
}
catch {
    $record.status = 'INSPECTION_FAILED_NO_RUN_RETRY'
    $record.error = $_.Exception.Message
}
finally {
    if ($null -ne $searchPattern -and $null -ne $originalFilter) {
        try { $searchPattern.SetValue($originalFilter) } catch {}
    }
}

$stream = [IO.File]::Open($output, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
try {
    $json = $record | ConvertTo-Json -Depth 8
    $bytes = (New-Object Text.UTF8Encoding($false)).GetBytes($json)
    $stream.Write($bytes, 0, $bytes.Length)
}
finally {
    $stream.Dispose()
}
$record | ConvertTo-Json -Depth 8
if ($record.status -ne 'OBSERVED_EXACT_FILTERED_VARIABLES') { throw $record.error }
