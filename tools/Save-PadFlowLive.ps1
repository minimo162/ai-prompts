[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][int]$TargetProcessId,
    [Parameter(Mandatory = $true)][string]$FlowName
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$process = Get-Process -Id $TargetProcessId
$windowCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::ProcessIdProperty, $TargetProcessId)
$windows = @([Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children, $windowCondition) | Where-Object { $_.Current.Name -ceq ('Power Automate | ' + $FlowName) })
if ($process.ProcessName -ne 'PAD.Designer' -or $windows.Count -ne 1) { throw 'Target flow mismatch' }
$window = $windows[0]
$saveCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::AutomationIdProperty, 'SaveFlowButton')
$containers = $window.FindAll([Windows.Automation.TreeScope]::Descendants, $saveCondition)
if ($containers.Count -ne 1) { throw 'SaveFlowButton is not unique' }
$buttonCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::ControlTypeProperty, [Windows.Automation.ControlType]::Button)
$buttons = $containers[0].FindAll([Windows.Automation.TreeScope]::Descendants, $buttonCondition)
if ($buttons.Count -ne 1 -or -not $buttons[0].Current.IsEnabled) { throw 'Save button unavailable' }
$buttons[0].GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke()
$savedCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::AutomationIdProperty, 'Flow_status_saved')
$deadline = [DateTime]::UtcNow.AddSeconds(20)
do {
    Start-Sleep -Milliseconds 200
    $saved = $window.FindAll([Windows.Automation.TreeScope]::Descendants, $savedCondition).Count -eq 1
} while (-not $saved -and [DateTime]::UtcNow -lt $deadline)
if (-not $saved) { throw 'Save completion was not observed' }
Write-Output ('SAVED=' + $FlowName)
