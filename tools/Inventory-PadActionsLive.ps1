[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][int]$TargetProcessId,
    [Parameter(Mandatory = $true)][string]$FlowName,
    [Parameter(Mandatory = $true)][string]$OutputPath
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$process = Get-Process -Id $TargetProcessId
if ($process.ProcessName -ne 'PAD.Designer') { throw 'Target is not PAD.Designer' }
if ($process.MainWindowTitle -cne ('Power Automate | ' + $FlowName)) { throw 'Target flow title mismatch' }
$window = [Windows.Automation.AutomationElement]::FromHandle($process.MainWindowHandle)
$treeCondition = New-Object Windows.Automation.PropertyCondition(
    [Windows.Automation.AutomationElement]::AutomationIdProperty, 'ActionsTreeView')
$treeNodes = $window.FindAll([Windows.Automation.TreeScope]::Descendants, $treeCondition)
if ($treeNodes.Count -ne 1) { throw 'ActionsTreeView is not unique' }
$tree = $treeNodes[0]
$itemCondition = New-Object Windows.Automation.PropertyCondition(
    [Windows.Automation.AutomationElement]::ControlTypeProperty,
    [Windows.Automation.ControlType]::TreeItem)
$scroll = $tree.GetCurrentPattern([Windows.Automation.ScrollPattern]::Pattern)
$scroll.SetScrollPercent([Windows.Automation.ScrollPattern]::NoScroll, 0)
Start-Sleep -Milliseconds 500
$observed = [ordered]@{}
$settled = $false
for ($pass = 0; $pass -lt 120; $pass++) {
    $elements = $tree.FindAll([Windows.Automation.TreeScope]::Descendants, $itemCondition)
    if ($elements.Count -eq 0 -or $elements.Count -gt 3000) { throw 'Inventory bound exceeded or empty' }
    $expand = $null
    foreach ($element in $elements) {
        if ($element.Current.IsOffscreen) { continue }
        $current = $element.Current
        $expandCollapse = $element.GetCurrentPattern([Windows.Automation.ExpandCollapsePattern]::Pattern)
        $isLeaf = $expandCollapse.Current.ExpandCollapseState -eq [Windows.Automation.ExpandCollapseState]::LeafNode
        $parent = [Windows.Automation.TreeWalker]::ControlViewWalker.GetParent($element)
        $parentId = ''
        while ($null -ne $parent -and $parent.Current.AutomationId -cne 'ActionsTreeView') {
            if ($parent.Current.ControlType -eq [Windows.Automation.ControlType]::TreeItem) {
                $parentId = $parent.Current.AutomationId
                break
            }
            $parent = [Windows.Automation.TreeWalker]::ControlViewWalker.GetParent($parent)
        }
        $key = $current.AutomationId
        if ([string]::IsNullOrWhiteSpace($key)) { $key = '__' + $current.Name }
        $observed[$key] = [ordered]@{
            ui_name = $current.Name
            automation_id = $current.AutomationId
            parent_id = $parentId
            kind = if ($isLeaf) { 'action' } else { 'group' }
            enabled = [bool]$current.IsEnabled
            offscreen = [bool]$current.IsOffscreen
        }
        if ($null -eq $expand -and $expandCollapse.Current.ExpandCollapseState -eq [Windows.Automation.ExpandCollapseState]::Collapsed) {
            $expand = $expandCollapse
        }
    }
    if ($null -ne $expand) {
        $expand.Expand()
        Start-Sleep -Milliseconds 180
        continue
    }
    if ($scroll.Current.VerticalScrollPercent -ge 99.999 -or -not $scroll.Current.VerticallyScrollable) {
        $settled = $true
        break
    }
    $before = $scroll.Current.VerticalScrollPercent
    $next = [Math]::Min(100, $before + 10)
    $scroll.SetScrollPercent([Windows.Automation.ScrollPattern]::NoScroll, $next)
    Start-Sleep -Milliseconds 180
    $after = $scroll.Current.VerticalScrollPercent
    Write-Output ('Observed ' + $observed.Count + ' nodes; scroll ' + $before + ' -> ' + $after)
}
if (-not $settled) { throw 'Scroll inventory did not reach end' }
$full = [IO.Path]::GetFullPath($OutputPath)
if (Test-Path -LiteralPath $full) { throw 'Evidence exists' }
$version = $null
try { $version = $process.MainModule.FileVersionInfo.FileVersion } catch { $version = 'unreadable' }
$record = [ordered]@{
    schema_version = 1
    captured_at = [DateTime]::UtcNow.ToString('o')
    pad_process_id = $TargetProcessId
    pad_file_version = $version
    flow_name = $FlowName
    language = 'ja-JP (observed UI labels)'
    power_fx = 'Off (new-flow dialog observation)'
    source = 'live ActionsTreeView: expanded visible groups and scrolled top to bottom'
    reached_bottom = $settled
    actions_executed = 0
    nodes = @($observed.Values)
}
$json = $record | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText($full, $json, (New-Object Text.UTF8Encoding($false)))
Write-Output ('WROTE=' + $full)
Write-Output ('OBSERVED_NODES=' + $observed.Count)
Write-Output ('ACTION_NODES=' + @($observed.Values | Where-Object kind -eq 'action').Count)
