[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][int]$TargetProcessId,
    [Parameter(Mandatory = $true)][string]$AutomationId,
    [Parameter(Mandatory = $true)][string]$FlowName,
    [string]$Name = ''
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes, System.Windows.Forms
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class RobinKnowledgeMouse {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,UIntPtr e);
}
'@
$process = Get-Process -Id $TargetProcessId
$windowCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::ProcessIdProperty, $TargetProcessId)
$windows = [Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children, $windowCondition)
$windows = @($windows | Where-Object { $_.Current.Name -ceq ('Power Automate | ' + $FlowName) })
if ($process.ProcessName -ne 'PAD.Designer' -or $windows.Count -ne 1) { throw 'Target flow mismatch' }
$window = $windows[0]
$matches = @()
foreach ($element in $window.FindAll([Windows.Automation.TreeScope]::Descendants, [Windows.Automation.Condition]::TrueCondition)) {
    $current = $element.Current
    if (-not $current.IsOffscreen -and $current.AutomationId -ceq $AutomationId -and (-not $Name -or $current.Name -ceq $Name)) { $matches += ,$element }
}
$unique = @{}
foreach ($element in $matches) { $unique[($element.GetRuntimeId() -join ',')] = $element }
$matches = @($unique.Values)
if ($matches.Count -ne 1) { throw ('Target not unique/visible: ' + $matches.Count) }
$target = $matches[0]
[void][RobinKnowledgeMouse]::SetForegroundWindow($window.Current.NativeWindowHandle)
$target.SetFocus()
$rect = $target.Current.BoundingRectangle
if ($rect.Width -le 0 -or $rect.Height -le 0) { throw 'Target has no visible bounds' }
$pointX = [int]($rect.Left + ($rect.Width / 2))
$pointY = [int]($rect.Top + ($rect.Height / 2))
[Windows.Forms.Cursor]::Position = New-Object Drawing.Point($pointX, $pointY)
[RobinKnowledgeMouse]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero)
[RobinKnowledgeMouse]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
Start-Sleep -Milliseconds 70
[RobinKnowledgeMouse]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero)
[RobinKnowledgeMouse]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
Write-Output ('DOUBLE_CLICKED=' + $AutomationId)
