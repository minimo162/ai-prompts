[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][int]$TargetConsoleProcessId,
    [Parameter(Mandatory = $true)][string]$FlowName,
    [Parameter(Mandatory = $true)][string]$EvidencePath,
    [int]$TimeoutSeconds = 40
)

$ErrorActionPreference = 'Stop'
$output = [IO.Path]::GetFullPath($EvidencePath)
if (Test-Path -LiteralPath $output) { throw 'Evidence exists; flow creation not requested' }
if (-not (Test-Path -LiteralPath ([IO.Path]::GetDirectoryName($output)) -PathType Container)) {
    throw 'Evidence directory missing; flow creation not requested'
}
if ([string]::IsNullOrWhiteSpace($FlowName) -or $FlowName.IndexOfAny([IO.Path]::GetInvalidFileNameChars()) -ge 0) {
    throw 'Invalid flow name; flow creation not requested'
}

Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes

function Get-PadDescendantsById {
    param(
        [Parameter(Mandatory = $true)][Windows.Automation.AutomationElement]$Root,
        [Parameter(Mandatory = $true)][string]$AutomationId
    )
    $condition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @(
        [Windows.Automation.AutomationElement]::AutomationIdProperty,
        $AutomationId
    )
    @($Root.FindAll([Windows.Automation.TreeScope]::Descendants, $condition))
}

function Get-PadTopWindowsForPid {
    param([Parameter(Mandatory = $true)][int]$ProcessId)
    $condition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @(
        [Windows.Automation.AutomationElement]::ProcessIdProperty,
        $ProcessId
    )
    @([Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children, $condition))
}

function Write-PadCreationEvidence {
    param([Parameter(Mandatory = $true)][hashtable]$Record)
    $stream = [IO.File]::Open($output, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        $json = $Record | ConvertTo-Json -Depth 8
        $bytes = (New-Object Text.UTF8Encoding($false)).GetBytes($json)
        $stream.Write($bytes, 0, $bytes.Length)
    }
    finally {
        $stream.Dispose()
    }
}

$record = [ordered]@{
    schema_version = 1
    requested_at = [DateTime]::UtcNow.ToString('o')
    console_process_id = $TargetConsoleProcessId
    flow_name = $FlowName
    status = 'NOT_STARTED'
    create_invocations = 0
    ok_invocations = 0
    dialog_count_before = $null
    dialog_count_after_create = $null
    power_fx_before = $null
    power_fx_toggle_invocations = 0
    power_fx_after = $null
    designer_process_id = $null
    designer_process_reused = $null
    designer_precreate_hwnd = $null
    designer_precreate_title = $null
    designer_session_id = $null
    designer_hwnd = $null
    designer_title = $null
    main_action_count = $null
    error = $null
}

try {
    $consoleProcess = Get-Process -Id $TargetConsoleProcessId
    if ($consoleProcess.ProcessName -cne 'PAD.Console.Host') { throw 'Console process mismatch' }
    $consoleWindows = @(Get-PadTopWindowsForPid -ProcessId $TargetConsoleProcessId | Where-Object {
        $_.Current.Name -ceq 'Power Automate' -and $_.Current.AutomationId -ceq 'ConsoleMainWindow'
    })
    if ($consoleWindows.Count -ne 1) { throw 'Console window is not unique' }
    $consoleWindow = $consoleWindows[0]

    $targetTitle = 'Power Automate | ' + $FlowName
    $existingTarget = @(Get-Process -Name 'PAD.Designer' -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowTitle -ceq $targetTitle
    })
    if ($existingTarget.Count -ne 0) { throw 'Target flow title already exists' }
    $designerBefore = @{}
    Get-Process -Name 'PAD.Designer' -ErrorAction SilentlyContinue | ForEach-Object {
        $designerBefore[$_.Id] = [ordered]@{
            hwnd = $_.MainWindowHandle
            title = $_.MainWindowTitle
        }
    }

    $dialogs = @(Get-PadDescendantsById -Root $consoleWindow -AutomationId 'DialogWindow')
    $record.dialog_count_before = $dialogs.Count
    if ($dialogs.Count -ne 0) { throw 'A create-flow dialog already exists; no button invoked' }

    $createButtons = @(Get-PadDescendantsById -Root $consoleWindow -AutomationId 'CreateNewFlowButton')
    if ($createButtons.Count -ne 1 -or -not $createButtons[0].Current.IsEnabled) {
        throw 'CreateNewFlowButton is not uniquely available'
    }
    $createPattern = $createButtons[0].GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern)
    $createPattern.Invoke()
    $record.create_invocations = 1

    $dialogDeadline = [DateTime]::UtcNow.AddSeconds([Math]::Min(15, $TimeoutSeconds))
    do {
        Start-Sleep -Milliseconds 200
        $dialogs = @(Get-PadDescendantsById -Root $consoleWindow -AutomationId 'DialogWindow')
    } while ($dialogs.Count -eq 0 -and [DateTime]::UtcNow -lt $dialogDeadline)
    $record.dialog_count_after_create = $dialogs.Count
    if ($dialogs.Count -ne 1) { throw 'Create-flow dialog is not unique after one invocation' }
    $dialog = $dialogs[0]

    $nameFields = @(Get-PadDescendantsById -Root $dialog -AutomationId 'NewFlowNameTextBox')
    $powerToggles = @(Get-PadDescendantsById -Root $dialog -AutomationId 'PowerFxEnabledToggleButton')
    $okButtons = @(Get-PadDescendantsById -Root $dialog -AutomationId 'OKNewFlowButton')
    if ($nameFields.Count -ne 1 -or $powerToggles.Count -ne 1 -or $okButtons.Count -ne 1) {
        throw 'Create-flow controls are not unique'
    }

    $togglePattern = $powerToggles[0].GetCurrentPattern([Windows.Automation.TogglePattern]::Pattern)
    $record.power_fx_before = $togglePattern.Current.ToggleState.ToString()
    if ($togglePattern.Current.ToggleState -ne [Windows.Automation.ToggleState]::Off) {
        $togglePattern.Toggle()
        $record.power_fx_toggle_invocations = 1
        Start-Sleep -Milliseconds 250
    }
    $record.power_fx_after = $togglePattern.Current.ToggleState.ToString()
    if ($togglePattern.Current.ToggleState -ne [Windows.Automation.ToggleState]::Off) {
        throw 'Power Fx could not be verified Off'
    }

    $valuePattern = $nameFields[0].GetCurrentPattern([Windows.Automation.ValuePattern]::Pattern)
    $valuePattern.SetValue($FlowName)
    if ($valuePattern.Current.Value -cne $FlowName) { throw 'Flow name readback mismatch' }
    if (-not $okButtons[0].Current.IsEnabled) { throw 'OKNewFlowButton is disabled' }
    $okButtons[0].GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke()
    $record.ok_invocations = 1

    $designerDeadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $designerWindows = @()
    do {
        Start-Sleep -Milliseconds 250
        $designerWindows = @([Windows.Automation.AutomationElement]::RootElement.FindAll(
            [Windows.Automation.TreeScope]::Children,
            [Windows.Automation.Condition]::TrueCondition
        ) | Where-Object { $_.Current.Name -ceq $targetTitle })
    } while ($designerWindows.Count -eq 0 -and [DateTime]::UtcNow -lt $designerDeadline)
    if ($designerWindows.Count -ne 1) { throw 'Created Designer window is not unique' }
    $designerWindow = $designerWindows[0]
    $designerProcess = Get-Process -Id $designerWindow.Current.ProcessId
    if ($designerProcess.ProcessName -cne 'PAD.Designer') { throw 'Created window process mismatch' }
    $record.designer_process_reused = $designerBefore.ContainsKey($designerProcess.Id)
    if ($record.designer_process_reused) {
        $record.designer_precreate_hwnd = $designerBefore[$designerProcess.Id].hwnd
        $record.designer_precreate_title = $designerBefore[$designerProcess.Id].title
        if ($record.designer_precreate_hwnd -ne 0 -or -not [string]::IsNullOrEmpty($record.designer_precreate_title)) {
            throw 'Created Designer reused a previously visible or titled process'
        }
    }
    if ($designerWindow.Current.NativeWindowHandle -eq 0) { throw 'Created Designer HWND is zero' }

    $actionLists = @(Get-PadDescendantsById -Root $designerWindow -AutomationId 'ProgramItemsListBoxActions')
    if ($actionLists.Count -ne 1) { throw 'Main action list is not unique' }
    $itemCondition = New-Object -TypeName Windows.Automation.PropertyCondition -ArgumentList @(
        [Windows.Automation.AutomationElement]::ControlTypeProperty,
        [Windows.Automation.ControlType]::ListItem
    )
    $actionCount = $actionLists[0].FindAll([Windows.Automation.TreeScope]::Children, $itemCondition).Count
    if ($actionCount -ne 0) { throw 'Created Main is not empty' }

    $record.designer_process_id = $designerProcess.Id
    $record.designer_session_id = $designerProcess.SessionId
    $record.designer_hwnd = $designerWindow.Current.NativeWindowHandle
    $record.designer_title = $designerWindow.Current.Name
    $record.main_action_count = $actionCount
    $record.status = 'CREATED_EMPTY_POWER_FX_OFF'
    Write-PadCreationEvidence -Record $record
    $record | ConvertTo-Json -Depth 8
}
catch {
    $record.status = 'FAILED_STOP_NO_RETRY'
    $record.error = $_.Exception.Message
    if (-not (Test-Path -LiteralPath $output)) {
        Write-PadCreationEvidence -Record $record
    }
    $record | ConvertTo-Json -Depth 8 | Write-Output
    throw
}
