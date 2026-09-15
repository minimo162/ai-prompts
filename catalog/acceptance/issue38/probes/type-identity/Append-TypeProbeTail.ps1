[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$RepositoryPath,
      [Parameter(Mandatory = $true)][int]$TargetProcessId)

# One-off collection helper. Existing five PAD actions must already be saved.
# Execute with Windows PowerShell 5.1 -STA (PadClipboardLease dependency).
$ErrorActionPreference = 'Stop'
$flowName = 'RobinIssue38TypeIdentity20260915C'
$evidencePath = Join-Path $PSScriptRoot 'append-tail.json'
if (Test-Path -LiteralPath $evidencePath) { throw 'Append evidence exists; do not repeat' }
. (Join-Path $RepositoryPath 'App.ps1') -Mode Library
Initialize-AgentPadTypes
$process = Get-Process -Id $TargetProcessId
if ($process.ProcessName -ne 'PAD.Designer' -or $process.MainWindowTitle -cne ('Power Automate | ' + $flowName)) { throw 'Target mismatch' }
$window = [Windows.Automation.AutomationElement]::FromHandle($process.MainWindowHandle)
function Find-UniqueId($root, $id) {
    $items = @($root.FindAll([Windows.Automation.TreeScope]::Descendants,
        [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::AutomationIdProperty, $id)))
    if ($items.Count -ne 1) { throw ('Non-unique control: ' + $id) }
    return $items[0]
}
$list = Find-UniqueId $window 'ProgramItemsListBoxActions'
$condition = [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ControlTypeProperty, [Windows.Automation.ControlType]::ListItem)
$items = @($list.FindAll([Windows.Automation.TreeScope]::Children, $condition))
if ($items.Count -ne 5) { throw 'Expected exactly five existing actions' }
$tailPath = Join-Path $PSScriptRoot 'assembled-tail.robin'
$tail = [IO.File]::ReadAllText($tailPath, [Text.Encoding]::UTF8)
if (($tail -split '\r?\n' | Where-Object { $_.Trim() }).Count -ne 30) { throw 'Unexpected tail line count' }
Add-Type -Path (Join-Path $RepositoryPath 'tools\PadClipboardLease.cs') -ReferencedAssemblies System.Windows.Forms
$clipboard = New-Object PadClipboard.NativeClipboard
$lease = $null
$restoration = 'not_changed'
$requested = $false
$status = @()
try {
    [void][AgentPadNative]::SetForegroundWindow($window.Current.NativeWindowHandle)
    $items[4].GetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern).Select()
    $items[4].SetFocus()
    if ([AgentPadNative]::GetForegroundWindow() -ne $window.Current.NativeWindowHandle) { throw 'Foreground changed' }
    $lease = [PadClipboard.Lease]::Begin($clipboard, $tail)
    $requested = $true
    [Windows.Forms.SendKeys]::SendWait('^v')
    $deadline = [DateTime]::UtcNow.AddSeconds(20)
    do {
        Start-Sleep -Milliseconds 200
        $status = @($window.FindAll([Windows.Automation.TreeScope]::Descendants, [Windows.Automation.Condition]::TrueCondition) |
            Where-Object { $_.Current.Name -match '^35\s+.*アクション' } | ForEach-Object { $_.Current.Name })
    } while ($status.Count -eq 0 -and [DateTime]::UtcNow -lt $deadline)
} finally {
    try { if ($null -ne $lease) { $restoration = $lease.Restore() } }
    finally { $clipboard.Dispose() }
    $record = [ordered]@{
        at = [DateTime]::UtcNow.ToString('o'); flow = $flowName; processId = $TargetProcessId
        beforeActions = 5; expectedAfterActions = 35; pasteRequested = $requested
        observedStatus = $status; clipboardRestoration = $restoration
        sourceSha256 = (Get-FileHash -LiteralPath $tailPath -Algorithm SHA256).Hash.ToLowerInvariant()
        scope = 'Assembled from captured action syntax; not yet runtime evidence'
    }
    [IO.File]::WriteAllText($evidencePath, ($record | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))
    $record | ConvertTo-Json -Depth 5
}
if ($status.Count -eq 0) { throw 'Append completion not observed; do not repeat paste' }
