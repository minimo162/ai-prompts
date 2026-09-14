[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$TargetProcessIds,
    [Parameter(Mandatory = $true)][string]$OutputPath,
    [int]$ComputerUseAppsCount = -1,
    [string]$ComputerUseBinding = 'NOT_CAPTURED',
    [string]$ComputerUseSource = ''
)

$ErrorActionPreference = 'Stop'

if (-not ([System.Management.Automation.PSTypeName]'PadWindowNative').Type) {
    Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class PadWindowNative {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassName(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
"@
}

function Get-ProcessRecord {
    param([System.Diagnostics.Process]$Process)
    if ($null -eq $Process) { return $null }
    try { $Process.Refresh() } catch {}
    $handle = [int64]0
    $title = ''
    $start = $null
    $responding = $null
    $session = $null
    try { $handle = [int64]$Process.MainWindowHandle } catch {}
    try { $title = [string]$Process.MainWindowTitle } catch {}
    try { $start = $Process.StartTime.ToString('o') } catch {}
    try { $responding = [bool]$Process.Responding } catch {}
    try { $session = [int]$Process.SessionId } catch {}
    [ordered]@{
        pid = [int]$Process.Id
        process = [string]$Process.ProcessName
        session_id = $session
        responding = $responding
        start_time = $start
        main_window_handle = $handle
        main_window_title = $title
    }
}

$resolvedOutput = [IO.Path]::GetFullPath($OutputPath)
if (Test-Path -LiteralPath $resolvedOutput) { throw 'OutputPath already exists' }
$parent = Split-Path -Parent $resolvedOutput
if (-not (Test-Path -LiteralPath $parent -PathType Container)) { throw 'Output parent does not exist' }

$uniqueTargetPids = @($TargetProcessIds -split '[,;\s]+' | Where-Object { $_ -match '^\d+$' } | ForEach-Object { [int]$_ } | Sort-Object -Unique)
if ($uniqueTargetPids.Count -eq 0) { throw 'TargetProcessIds must contain one or more integer PIDs' }
$targetProcessRecords = @()
foreach ($targetPid in $uniqueTargetPids) {
    $targetProcess = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
    if ($null -eq $targetProcess) {
        $targetProcessRecords += [ordered]@{ pid = [int]$targetPid; present = $false }
        continue
    }
    $record = Get-ProcessRecord $targetProcess
    $record['present'] = $true
    $targetProcessRecords += $record
}

$selfProcess = Get-Process -Id $PID -ErrorAction SilentlyContinue
$selfRecord = Get-ProcessRecord $selfProcess
$explorerRecords = @()
foreach ($explorer in @(Get-Process -Name 'explorer' -ErrorAction SilentlyContinue)) {
    $explorerRecords += Get-ProcessRecord $explorer
}

$script:windowRecords = @()
$enumCallback = [PadWindowNative+EnumWindowsProc]{
    param([IntPtr]$hWnd, [IntPtr]$lParam)
    $titleBuilder = New-Object Text.StringBuilder 1024
    $classBuilder = New-Object Text.StringBuilder 512
    [void][PadWindowNative]::GetWindowText($hWnd, $titleBuilder, $titleBuilder.Capacity)
    [void][PadWindowNative]::GetClassName($hWnd, $classBuilder, $classBuilder.Capacity)
    [uint32]$ownerPid = 0
    [void][PadWindowNative]::GetWindowThreadProcessId($hWnd, [ref]$ownerPid)
    $script:windowRecords += [ordered]@{
        hwnd = [int64]$hWnd.ToInt64()
        is_window_visible = [bool][PadWindowNative]::IsWindowVisible($hWnd)
        title = $titleBuilder.ToString()
        class_name = $classBuilder.ToString()
        owner_pid = [int]$ownerPid
    }
    return $true
}
[void][PadWindowNative]::EnumWindows($enumCallback, [IntPtr]::Zero)

$enrichedWindows = @()
foreach ($window in $script:windowRecords) {
    $ownerProcess = Get-Process -Id $window.owner_pid -ErrorAction SilentlyContinue
    $ownerRecord = Get-ProcessRecord $ownerProcess
    $enriched = [ordered]@{}
    foreach ($property in $window.Keys) { $enriched[$property] = $window[$property] }
    $enriched['owner_process'] = if ($null -ne $ownerRecord) { $ownerRecord.process } else { $null }
    $enriched['owner_session_id'] = if ($null -ne $ownerRecord) { $ownerRecord.session_id } else { $null }
    $enrichedWindows += $enriched
}

$foregroundHandle = [PadWindowNative]::GetForegroundWindow()
$foregroundPid = 0
if ($foregroundHandle -ne [IntPtr]::Zero) {
    [uint32]$foregroundPidNative = 0
    [void][PadWindowNative]::GetWindowThreadProcessId($foregroundHandle, [ref]$foregroundPidNative)
    $foregroundPid = [int]$foregroundPidNative
}
$foregroundRecord = $null
if ($foregroundHandle -ne [IntPtr]::Zero) {
    $foregroundWindow = @($enrichedWindows | Where-Object { $_.hwnd -eq [int64]$foregroundHandle.ToInt64() }) | Select-Object -First 1
    if ($null -ne $foregroundWindow) { $foregroundRecord = $foregroundWindow }
    else {
        $foregroundRecord = [ordered]@{
            hwnd = [int64]$foregroundHandle.ToInt64()
            owner_pid = $foregroundPid
            is_window_visible = [bool][PadWindowNative]::IsWindowVisible($foregroundHandle)
        }
    }
}

$uiaRecords = @()
try {
    Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
    foreach ($target in @($targetProcessRecords | Where-Object { $_.present -and $_.process -eq 'PAD.Designer' })) {
        $condition = New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ProcessIdProperty, $target.pid)
        $elements = @([Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children, $condition))
        $uiaWindows = @($elements | ForEach-Object {
            [ordered]@{
                name = $_.Current.Name
                automation_id = $_.Current.AutomationId
                control_type = $_.Current.ControlType.ProgrammaticName
                native_window_handle = [int64]$_.Current.NativeWindowHandle
            }
        })
        $uiaRecords += [ordered]@{ pid = $target.pid; root_children_count = [int]$elements.Count; windows = $uiaWindows }
    }
} catch {
    $uiaRecords += [ordered]@{ error = $_.Exception.Message }
}

$designerPids = @($targetProcessRecords | Where-Object { $_.present -and $_.process -eq 'PAD.Designer' } | ForEach-Object { [int]$_.pid })
$allTargetPids = @($targetProcessRecords | Where-Object { $_.present } | ForEach-Object { [int]$_.pid })
$visibleWindows = @($enrichedWindows | Where-Object { $_.is_window_visible })
$designerVisibleWindows = @($visibleWindows | Where-Object { $designerPids -contains [int]$_.owner_pid -and [int64]$_.hwnd -ne 0 })
$padLikeOtherWindows = @($visibleWindows | Where-Object {
    ($_.title -match 'Power Automate|PAD\.Designer' -or $_.class_name -match 'PAD|PowerAutomate') -and
    -not ($allTargetPids -contains [int]$_.owner_pid)
})
$uiaVisibleCounts = @($uiaRecords | Where-Object { $null -ne $_.root_children_count } | ForEach-Object { [int]$_.root_children_count })

$classification = 'UNCLASSIFIED'
$classificationBasis = @()
if ($visibleWindows.Count -eq 0 -and $foregroundHandle -eq [IntPtr]::Zero -and $ComputerUseAppsCount -eq 0) {
    $classification = 'A'
    $classificationBasis += 'no visible top-level windows'
    $classificationBasis += 'foreground window is null'
    $classificationBasis += 'Computer Use apps=[]'
} elseif ($designerVisibleWindows.Count -eq 0 -and $padLikeOtherWindows.Count -eq 0 -and $visibleWindows.Count -gt 0) {
    $classification = 'B'
    $classificationBasis += 'normal visible windows enumerated'
    $classificationBasis += 'no visible PAD Designer window'
} elseif ($padLikeOtherWindows.Count -gt 0) {
    $classification = 'C'
    $classificationBasis += 'PAD-like visible title/class owned by another PID'
} elseif ($designerVisibleWindows.Count -gt 0 -and (($uiaVisibleCounts | Where-Object { $_ -eq 0 }).Count -gt 0 -or $ComputerUseAppsCount -eq 0)) {
    $classification = 'D'
    $classificationBasis += 'visible PAD Designer HWND exists'
    $classificationBasis += 'UIA or Computer Use path does not expose it'
}

$sessionComparison = [ordered]@{
    powershell = $selfRecord
    explorer = $explorerRecords
    pad_targets = $targetProcessRecords
    unique_session_ids = @(@($selfRecord.session_id) + @($explorerRecords | ForEach-Object { $_.session_id }) + @($targetProcessRecords | Where-Object { $_.present } | ForEach-Object { $_.session_id }) | Where-Object { $null -ne $_ } | Sort-Object -Unique)
}

$record = [ordered]@{
    schema_version = 1
    captured_at = (Get-Date).ToString('yyyy-MM-ddTHH:mm:sszzz')
    verification_id = 'T04-INDEPENDENT-CURRENT-20260914E-WINDOW-DIAGNOSTIC-12'
    case = 'T04'
    scope = 'read_only_pad_window_visibility_diagnostic'
    target_process_ids = $uniqueTargetPids
    target_process_snapshot_after_refresh = $targetProcessRecords
    session_comparison = $sessionComparison
    top_level_windows = $enrichedWindows
    top_level_window_counts = [ordered]@{
        all = [int]$enrichedWindows.Count
        visible = [int]$visibleWindows.Count
        visible_nonempty_title = [int](@($visibleWindows | Where-Object { -not [string]::IsNullOrEmpty($_.title) }).Count)
    }
    foreground_window = [ordered]@{
        hwnd = [int64]$foregroundHandle.ToInt64()
        owner_pid = $foregroundPid
        details = $foregroundRecord
    }
    uia_snapshot = $uiaRecords
    computer_use_snapshot = [ordered]@{
        apps_count = $ComputerUseAppsCount
        native_app_binding = $ComputerUseBinding
        source = $ComputerUseSource
    }
    result = ('READ_ONLY_PAD_WINDOW_DIAGNOSTIC_CASE_' + $classification)
    classification = [ordered]@{
        case = $classification
        basis = $classificationBasis
    }
    reopen_conditions = @(
        'interactive desktop or Computer Use native app binding exposes a visible PAD Designer window',
        'PAD Designer has a stable nonzero HWND, owner PID/process, SessionId, and target-flow correspondence',
        'only then evaluate the saved Robin with a new verification ID; preserve the Run1 output gate before any Run2'
    )
    mutation_guard = [ordered]@{
        process_refresh_only = $true
        process_kill_or_restart = $false
        window_input_or_click = $false
        flow_binding_or_run = $false
    }
}

$json = $record | ConvertTo-Json -Depth 10
[IO.File]::WriteAllText($resolvedOutput, $json, (New-Object Text.UTF8Encoding($false)))
Write-Output ('PASS: diagnostic saved to ' + $resolvedOutput)
Write-Output ('CLASSIFICATION: ' + $classification)
