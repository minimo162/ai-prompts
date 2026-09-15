[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][int]$TargetProcessId,
    [Parameter(Mandatory = $true)][string]$FlowName,
    [Parameter(Mandatory = $true)][string]$EvidencePath,
    [int]$TimeoutSeconds = 30
)

$ErrorActionPreference = 'Stop'
$output = [IO.Path]::GetFullPath($EvidencePath)
if (Test-Path -LiteralPath $output) { throw 'Evidence exists; Run not requested' }
if (-not (Test-Path -LiteralPath ([IO.Path]::GetDirectoryName($output)) -PathType Container)) { throw 'Evidence directory missing; Run not requested' }
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$process = Get-Process -Id $TargetProcessId
$windowCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::ProcessIdProperty, $TargetProcessId)
$windows = @([Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children, $windowCondition) | Where-Object { $_.Current.Name -ceq ('Power Automate | ' + $FlowName) })
if ($process.ProcessName -ne 'PAD.Designer' -or $windows.Count -ne 1) { throw 'Target flow mismatch' }
$window = $windows[0]
$startCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::AutomationIdProperty, 'StartFlowButton')
$start = $window.FindAll([Windows.Automation.TreeScope]::Descendants, $startCondition)
if ($start.Count -ne 1 -or -not $start[0].Current.IsEnabled) { throw 'Run button unavailable' }
$start[0].GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke()
$deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
$ready = $false
do {
    Start-Sleep -Milliseconds 250
    $readyCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::AutomationIdProperty, 'Flow_status_ready')
    $ready = $window.FindAll([Windows.Automation.TreeScope]::Descendants, $readyCondition).Count -eq 1
    $startEnabled = $window.FindAll([Windows.Automation.TreeScope]::Descendants, $startCondition)[0].Current.IsEnabled
} while ((-not $ready -or -not $startEnabled) -and [DateTime]::UtcNow -lt $deadline)
$completionObserved = $ready -and $startEnabled
$previewCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::AutomationIdProperty, 'VariablePreviewTextBlock')
$previews = @($window.FindAll([Windows.Automation.TreeScope]::Descendants, $previewCondition) | ForEach-Object { $_.Current.Name })
$evidence = [ordered]@{
    schema_version = 1
    observed_at = [DateTime]::UtcNow.ToString('o')
    flow_name = $FlowName
    run_status = $(if ($completionObserved) { 'success' } else { 'completion_not_observed' })
    timeout_seconds = $TimeoutSeconds
    ready_observed = $ready
    start_enabled_after = $startEnabled
    variable_previews = $previews
}
$stream = [IO.File]::Open($output, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
try {
    $bytes = (New-Object Text.UTF8Encoding($false)).GetBytes(($evidence | ConvertTo-Json -Depth 8))
    $stream.Write($bytes, 0, $bytes.Length)
} finally { $stream.Dispose() }
$evidence | ConvertTo-Json -Depth 8
if (-not $completionObserved) { throw 'Run completion was not observed; observation saved, do not repeat Run' }
