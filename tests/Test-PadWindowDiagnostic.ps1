[CmdletBinding()]
param(
    [string]$Root = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
$checks = 0

function Check([bool]$Value, [string]$Name) {
    if (-not $Value) { throw ('FAIL: ' + $Name) }
    $script:checks++
}

function Read-Text([string]$RelativePath) {
    $path = [IO.Path]::GetFullPath((Join-Path $Root ($RelativePath.Replace('/', '\'))))
    Check (Test-Path -LiteralPath $path -PathType Leaf) ('file exists: ' + $RelativePath)
    return [IO.File]::ReadAllText($path, [Text.Encoding]::UTF8)
}

$scriptText = Read-Text 'tools/Diagnose-PadWindowVisibility.ps1'
$jsonText = Read-Text 'catalog/evidence/t04-independent-current-pad-window-diagnostic-20260914r.json'
$diagnostic = $jsonText | ConvertFrom-Json

foreach ($required in @(
    'Process\.Refresh\(\)',
    'EnumWindows',
    'IsWindowVisible',
    'GetWindowText',
    'GetClassName',
    'GetWindowThreadProcessId',
    'GetForegroundWindow',
    'UIAutomationClient',
    'process_refresh_only = \$true',
    'process_kill_or_restart = \$false',
    'window_input_or_click = \$false',
    'flow_binding_or_run = \$false'
)) {
    Check ([regex]::IsMatch($scriptText, $required)) ('diagnostic contains ' + $required)
}

foreach ($case in @('A', 'B', 'C', 'D')) {
    Check ([regex]::IsMatch($scriptText, "classification = '$case'")) ('diagnostic has case ' + $case + ' branch')
}

foreach ($forbidden in @('Stop-Process', '\.Kill\(', 'SendKeys', 'SetForegroundWindow')) {
    Check (-not [regex]::IsMatch($scriptText, $forbidden)) ('diagnostic excludes mutation ' + $forbidden)
}

Check ($diagnostic.result -eq 'READ_ONLY_PAD_WINDOW_DIAGNOSTIC_CASE_A') 'captured result is CASE_A'
Check ($diagnostic.target_process_ids -contains 25804 -and $diagnostic.target_process_ids -contains 31664) 'captured target PIDs'
Check ($diagnostic.top_level_window_counts.all -eq 0 -and $diagnostic.top_level_window_counts.visible -eq 0) 'captured no top-level windows'
Check ($diagnostic.top_level_windows.Count -eq 0) 'captured window list is empty'
Check ($diagnostic.foreground_window.hwnd -eq 0 -and $diagnostic.foreground_window.owner_pid -eq 0) 'captured no foreground window'
Check (@($diagnostic.session_comparison.unique_session_ids).Count -eq 1 -and $diagnostic.session_comparison.unique_session_ids[0] -eq 1) 'captured comparable SessionId'
Check ($diagnostic.computer_use_snapshot.apps_count -eq 0 -and $diagnostic.computer_use_snapshot.native_app_binding -eq 'UNAVAILABLE') 'captured Computer Use apps empty'
Check ($diagnostic.mutation_guard.process_refresh_only -and -not $diagnostic.mutation_guard.process_kill_or_restart -and -not $diagnostic.mutation_guard.window_input_or_click -and -not $diagnostic.mutation_guard.flow_binding_or_run) 'captured read-only mutation guard'

Write-Output ('PASS: ' + $checks + ' PAD window diagnostic contract checks; A-D branches and read-only guard preserved.')
