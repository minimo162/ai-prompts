[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][int]$TargetProcessId,
    [Parameter(Mandatory = $true)][string]$FlowName,
    [Parameter(Mandatory = $true)][string]$OutputPath,
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
$itemCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::ControlTypeProperty, [Windows.Automation.ControlType]::ListItem)
$items = $lists[0].FindAll([Windows.Automation.TreeScope]::Children, $itemCondition)
if ($items.Count -ne $ExpectedActionCount -or $items.Count -eq 0) { throw ('Unexpected action count: ' + $items.Count) }
$output = [IO.Path]::GetFullPath($OutputPath)
if (Test-Path -LiteralPath $output) { throw 'Output exists' }
$beforeClipboard = Get-AgentPadClipboard
$beforeSequence = Get-AgentPadClipboardSequence
$copiedSequence = $null
$text = $null
try {
    [void][AgentPadNative]::SetForegroundWindow($window.Current.NativeWindowHandle)
    $items[0].GetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern).Select()
    $items[0].SetFocus()
    if ([AgentPadNative]::GetForegroundWindow() -ne $window.Current.NativeWindowHandle) { throw 'Foreground changed' }
    [Windows.Forms.SendKeys]::SendWait('^a')
    [Windows.Forms.SendKeys]::SendWait('^c')
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    do { Start-Sleep -Milliseconds 100; $copiedSequence = Get-AgentPadClipboardSequence } while ($copiedSequence -eq $beforeSequence -and [DateTime]::UtcNow -lt $deadline)
    if ($copiedSequence -eq $beforeSequence) { throw 'Copy was not observed' }
    $text = Get-AgentPadClipboardText
    Start-Sleep -Milliseconds 200
    if ([string]::IsNullOrWhiteSpace($text) -or (Get-AgentPadClipboardSequence) -ne $copiedSequence -or (Get-AgentPadClipboardText) -cne $text) { throw 'Copied text was not stable' }
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($output)) | Out-Null
    [IO.File]::WriteAllText($output, $text, (New-Object Text.UTF8Encoding($false)))
}
finally {
    if ($null -ne $copiedSequence -and (Get-AgentPadClipboardSequence) -eq $copiedSequence) { Restore-AgentPadClipboard $beforeClipboard }
}
[pscustomobject]@{ path=$output; sha256=(Get-AgentHash $output); bytes=(Get-Item -LiteralPath $output).Length; action_count=$ExpectedActionCount; clipboard_restored=$true } | ConvertTo-Json
