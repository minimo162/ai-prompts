[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][int]$TargetProcessId,
    [Parameter(Mandatory = $true)][string]$FlowName,
    [Parameter(Mandatory = $true)][string]$InputPath,
    [Parameter(Mandatory = $true)][string]$EvidencePath,
    [int]$ExpectedActionCount = 1
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
Initialize-AgentPadTypes
$process = Get-Process -Id $TargetProcessId
$windowCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::ProcessIdProperty, $TargetProcessId)
$windows = [Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children, $windowCondition)
$windows = @($windows | Where-Object { $_.Current.Name -ceq ('Power Automate | ' + $FlowName) })
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
try {
    [void][AgentPadNative]::SetForegroundWindow($window.Current.NativeWindowHandle)
    $list.SetFocus()
    if ([AgentPadNative]::GetForegroundWindow() -ne $window.Current.NativeWindowHandle) { throw 'Foreground changed' }
    [Windows.Forms.Clipboard]::SetText($text)
    $pasteSequence = Get-AgentPadClipboardSequence
    [Windows.Forms.SendKeys]::SendWait('^v')
    $deadline = [DateTime]::UtcNow.AddSeconds(20)
    do { Start-Sleep -Milliseconds 200; $count = $list.FindAll([Windows.Automation.TreeScope]::Children, $itemCondition).Count } while ($count -ne $ExpectedActionCount -and [DateTime]::UtcNow -lt $deadline)
    if ($count -ne $ExpectedActionCount) { throw ('Paste not confirmed; count=' + $count) }
    $settled = $true
}
finally {
    if ($settled -and $null -ne $pasteSequence -and (Get-AgentPadClipboardSequence) -eq $pasteSequence -and (Get-AgentPadClipboardText) -ceq $text) { Restore-AgentPadClipboard $beforeClipboard }
}
$saveCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::AutomationIdProperty, 'SaveFlowButton')
$saveContainer = $window.FindAll([Windows.Automation.TreeScope]::Descendants, $saveCondition)
if ($saveContainer.Count -ne 1) { throw 'SaveFlowButton is not unique' }
$buttonCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::ControlTypeProperty, [Windows.Automation.ControlType]::Button)
$buttons = $saveContainer[0].FindAll([Windows.Automation.TreeScope]::Descendants, $buttonCondition)
if ($buttons.Count -ne 1) { throw 'Save button is not unique' }
$buttons[0].GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke()
$saved = $false
$deadline = [DateTime]::UtcNow.AddSeconds(20)
do {
    Start-Sleep -Milliseconds 200
    $savedCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::AutomationIdProperty, 'Flow_status_saved')
    $saved = $window.FindAll([Windows.Automation.TreeScope]::Descendants, $savedCondition).Count -eq 1
} while (-not $saved -and [DateTime]::UtcNow -lt $deadline)
if (-not $saved) { throw 'Save completion was not observed' }
$evidence = [ordered]@{
    schema_version = 1
    captured_at = [DateTime]::UtcNow.ToString('o')
    flow_name = $FlowName
    source_robin = $InputPath
    source_sha256 = Get-AgentHash $input
    source_bytes = (Get-Item -LiteralPath $input).Length
    paste_confirmed = $settled
    action_count_after_paste = $count
    saved_confirmed = $saved
    clipboard_restored = ($settled -and $null -ne $pasteSequence -and (Get-AgentPadClipboardSequence) -ne $pasteSequence)
    execution_requested = $false
}
$out = [IO.Path]::GetFullPath($EvidencePath)
if (Test-Path -LiteralPath $out) { throw 'Evidence exists' }
[IO.File]::WriteAllText($out, ($evidence | ConvertTo-Json -Depth 8), (New-Object Text.UTF8Encoding($false)))
$evidence | ConvertTo-Json -Depth 8
