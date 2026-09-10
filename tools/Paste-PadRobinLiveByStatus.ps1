[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][int]$TargetProcessId,
    [Parameter(Mandatory = $true)][string]$FlowName,
    [Parameter(Mandatory = $true)][string]$InputPath,
    [Parameter(Mandatory = $true)][string]$EvidencePath,
    [Parameter(Mandatory = $true)][int]$ExpectedActionCount
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
Initialize-AgentPadTypes
$process = Get-Process -Id $TargetProcessId
$windowCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::ProcessIdProperty, $TargetProcessId)
$windows = @([Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children, $windowCondition) | Where-Object { $_.Current.Name -ceq ('Power Automate | ' + $FlowName) })
if ($process.ProcessName -ne 'PAD.Designer' -or $windows.Count -ne 1) { throw 'Target flow mismatch' }
$window = $windows[0]
$listCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::AutomationIdProperty, 'ProgramItemsListBoxActions')
$lists = $window.FindAll([Windows.Automation.TreeScope]::Descendants, $listCondition)
if ($lists.Count -ne 1) { throw 'Action list is not unique' }
$list = $lists[0]
$itemCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::ControlTypeProperty, [Windows.Automation.ControlType]::ListItem)
$beforeCount = $list.FindAll([Windows.Automation.TreeScope]::Children, $itemCondition).Count
if ($beforeCount -ne 0) { throw 'Roundtrip flow is not empty' }
$input = [IO.Path]::GetFullPath($InputPath)
$text = [IO.File]::ReadAllText($input, (New-Object Text.UTF8Encoding($false)))
if ([string]::IsNullOrWhiteSpace($text)) { throw 'Input Robin is empty' }
$beforeClipboard = Get-AgentPadClipboard
$beforeSequence = Get-AgentPadClipboardSequence
$pasteSequence = $null
$settled = $false
$visibleCount = $beforeCount
$statusName = $null
try {
    [void][AgentPadNative]::SetForegroundWindow($window.Current.NativeWindowHandle)
    $list.SetFocus()
    if ([AgentPadNative]::GetForegroundWindow() -ne $window.Current.NativeWindowHandle) { throw 'Foreground changed' }
    [Windows.Forms.Clipboard]::SetText($text)
    $pasteSequence = Get-AgentPadClipboardSequence
    [Windows.Forms.SendKeys]::SendWait('^v')
    $deadline = [DateTime]::UtcNow.AddSeconds(25)
    do {
        Start-Sleep -Milliseconds 200
        $visibleCount = $list.FindAll([Windows.Automation.TreeScope]::Children, $itemCondition).Count
        $statusNodes = @($window.FindAll([Windows.Automation.TreeScope]::Descendants, (New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::NameProperty, ($ExpectedActionCount.ToString() + ' アクション')))))
        if ($statusNodes.Count -gt 0) { $statusName = $statusNodes[0].Current.Name }
    } while ($null -eq $statusName -and [DateTime]::UtcNow -lt $deadline)
    if ($null -eq $statusName) { throw ('Paste not confirmed by Designer status; visible_count=' + $visibleCount) }
    $settled = $true
}
finally {
    if ($settled -and $null -ne $pasteSequence -and (Get-AgentPadClipboardSequence) -eq $pasteSequence -and (Get-AgentPadClipboardText) -ceq $text) { Restore-AgentPadClipboard $beforeClipboard }
}
$evidence = [ordered]@{
    schema_version = 1
    captured_at = [DateTime]::UtcNow.ToString('o')
    flow_name = $FlowName
    process_id = $TargetProcessId
    source_robin = $InputPath
    source_sha256 = Get-AgentHash $input
    source_bytes = (Get-Item -LiteralPath $input).Length
    empty_before_paste = ($beforeCount -eq 0)
    paste_confirmed = $settled
    visible_action_count = $visibleCount
    designer_action_count = $ExpectedActionCount
    designer_status = $statusName
    virtualized_list_false_negative = ($visibleCount -ne $ExpectedActionCount)
    saved_confirmed = $false
    execution_requested = $false
}
$out = [IO.Path]::GetFullPath($EvidencePath)
if (Test-Path -LiteralPath $out) { throw 'Evidence exists' }
[IO.File]::WriteAllText($out, ($evidence | ConvertTo-Json -Depth 8), (New-Object Text.UTF8Encoding($false)))
$evidence | ConvertTo-Json -Depth 8
