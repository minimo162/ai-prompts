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
    # Excel actions can take longer than the list virtualization update.  Keep
    # waiting for the Designer's status summary (rather than treating the
    # six realized ListItems as a paste failure).
    $deadline = [DateTime]::UtcNow.AddSeconds(60)
    do {
        Start-Sleep -Milliseconds 200
        $visibleCount = $list.FindAll([Windows.Automation.TreeScope]::Children, $itemCondition).Count
        # PAD localizes/qualifies this summary differently across builds (for
        # example, "9 アクション" and "9 選択されたアクション").  The
        # direct ListItem collection is virtualized, so use the authoritative
        # numeric prefix plus the action word instead of an exact label.
        $allNodes = @($window.FindAll([Windows.Automation.TreeScope]::Descendants, [Windows.Automation.Condition]::TrueCondition))
        $statusNodes = @($allNodes | Where-Object {
            try { $_.Current.Name -match ('^' + [regex]::Escape($ExpectedActionCount.ToString()) + '\s+.*アクション') } catch { $false }
        })
        if ($statusNodes.Count -gt 0) { $statusName = $statusNodes[0].Current.Name }
    } while ($null -eq $statusName -and [DateTime]::UtcNow -lt $deadline)
    if ($null -eq $statusName) { throw ('Paste not confirmed by Designer status; visible_count=' + $visibleCount) }
    $settled = $true
}
finally {
    # Observation failure must not discard the clipboard snapshot. Restore only
    # while this paste still owns both the sequence and exact text.
    if ($null -ne $pasteSequence -and (Get-AgentPadClipboardSequence) -eq $pasteSequence -and (Get-AgentPadClipboardText) -ceq $text) { Restore-AgentPadClipboard $beforeClipboard }
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
