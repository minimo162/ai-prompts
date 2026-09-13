[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][int]$TargetProcessId,
    [Parameter(Mandatory = $true)][string]$FlowName,
    [Parameter(Mandatory = $true)][string]$ExpectationPath,
    [Parameter(Mandatory = $true)][string]$EvidencePath,
    [Parameter(Mandatory = $true)][ValidateSet(1, 2)][int]$RunNumber,
    [int]$TimeoutSeconds = 45
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
Initialize-AgentPadTypes

$expectedSubflows = @('Main', 'P3Worker')
$evidence = [IO.Path]::GetFullPath($EvidencePath)
$evidenceDirectory = [IO.Path]::GetDirectoryName($evidence)
if ([string]::IsNullOrWhiteSpace($evidenceDirectory)) { throw 'PAD_EVIDENCE: evidence directory is required.' }
[IO.Directory]::CreateDirectory($evidenceDirectory) | Out-Null
if (Test-Path -LiteralPath $evidence) { throw 'PAD_EVIDENCE: evidence path already exists.' }
$requestPath = Join-Path $evidenceDirectory ('run' + $RunNumber + '-request.json')
if (Test-Path -LiteralPath $requestPath) { throw 'PAD_EVIDENCE: run-request path already exists.' }

function Write-SubflowEvidence([hashtable]$Value) {
    if (Test-Path -LiteralPath $evidence) { throw 'PAD_EVIDENCE: evidence path already exists.' }
    [IO.File]::WriteAllText($evidence, ($Value | ConvertTo-Json -Depth 16), (New-Object Text.UTF8Encoding($false)))
    $Value | ConvertTo-Json -Depth 16
}

function Resolve-SubflowSource([string]$Path) {
    if ([IO.Path]::IsPathRooted($Path)) { return [IO.Path]::GetFullPath($Path) }
    return [IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $PSScriptRoot) $Path))
}

function Get-SubflowTargetWindow([int]$ProcessId, [string]$Name) {
    $process = Get-Process -Id $ProcessId
    if ($process.ProcessName -cne 'PAD.Designer') { throw ('PAD_TARGET: process is not PAD.Designer: ' + $process.ProcessName) }
    if ([IntPtr]$process.MainWindowHandle -eq [IntPtr]::Zero) { throw 'PAD_TARGET: PAD.Designer has no nonzero main window handle.' }
    $condition = New-Object Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::ProcessIdProperty, $ProcessId)
    $windows = @([Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children, $condition) | Where-Object {
        $_.Current.Name -ceq ('Power Automate | ' + $Name)
    })
    if ($windows.Count -ne 1) { throw ('PAD_TARGET: expected one exact PAD flow window; observed ' + $windows.Count + '.') }
    return $windows[0]
}

function Get-SubflowVariablePreviews($Window) {
    $condition = New-Object Windows.Automation.PropertyCondition -ArgumentList @([Windows.Automation.AutomationElement]::AutomationIdProperty, 'VariablePreviewTextBlock')
    return @($Window.FindAll([Windows.Automation.TreeScope]::Descendants, $condition) | ForEach-Object { [string]$_.Current.Name })
}

function Get-SubflowRunSample($Window) {
    # After a subflow call completes, PAD may select the called child tab.
    # Run-state observation must therefore not require Main to remain selected.
    $status = Get-AgentPadStatus $Window
    $stop = Get-AgentPadInvokableButton $Window 'StopFlowButton' '停止' -Wrapped
    $stopEnabled = [bool]$stop.Current.IsEnabled
    $runningStatus = ($status.state -cin @('running', 'stepping', 'stepping_over', 'stepping_out', 'running_flow'))
    if ($runningStatus -and -not $stopEnabled) {
        throw 'PAD_SELECTOR: StopFlowButton is not enabled during the observed execution state.'
    }
    $idle = (-not $stopEnabled -and $status.state -cin @('ready', 'saved'))
    $errorState = Get-AgentPadErrorState -Window $Window -Running $stopEnabled -Idle $idle -StatusBar $status.status_bar
    return [pscustomobject]@{
        status = $status.state
        running = $stopEnabled
        execution_observed = ($runningStatus -or ($status.state -ceq 'saved' -and $stopEnabled))
        idle = $idle
        errors = $errorState.count
        errors_known = $errorState.known
    }
}

$fixedAt = [DateTime]::UtcNow
$expectation = $null
$sourceHashes = [ordered]@{}
$sourceBytes = [ordered]@{}
try {
    $expectation = Get-Content -LiteralPath ([IO.Path]::GetFullPath($ExpectationPath)) -Raw | ConvertFrom-Json
    if ([string]$expectation.expected_variable -cne 'ButtonPressed' -or [string]$expectation.expected_preview -cne 'OK') { throw 'PAD_EXPECTATION: fixed expectation is not ButtonPressed=OK.' }
    foreach ($name in @('call', 'worker')) {
        $entry = $expectation.raw.$name
        $source = Resolve-SubflowSource ([string]$entry.source)
        if (-not (Test-Path -LiteralPath $source)) { throw ('PAD_EXPECTATION: missing source: ' + $source) }
        $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash.ToLowerInvariant()
        $bytes = (Get-Item -LiteralPath $source).Length
        if ($hash -cne ([string]$entry.actual_sha256).ToLowerInvariant()) { throw ('PAD_EXPECTATION: source changed: ' + $name) }
        $sourceHashes[$name] = $hash
        $sourceBytes[$name] = $bytes
    }
} catch {
    $failure = [ordered]@{
        schema_version = 2
        captured_at = [DateTime]::UtcNow.ToString('o')
        status = 'NOT_RUN_PRECONDITION_FAILED'
        run_number = $RunNumber
        flow_name = $FlowName
        execution_requested = $false
        error = $_.Exception.Message
        fixed_at = $fixedAt.ToString('o')
    }
    Write-SubflowEvidence $failure
    return
}

$window = $null
$before = $null
try {
    $window = Get-SubflowTargetWindow $TargetProcessId $FlowName
    $before = Get-AgentPadSnapshot -Window $window -AllowErrors -ExpectedSubflowNames $expectedSubflows
    if (-not $before.ready -or -not $before.errors_known -or $before.errors -ne 0) { throw 'PAD_SETUP: fixed Main/P3Worker flow is not ready with confirmed zero errors.' }
} catch {
    $failure = [ordered]@{
        schema_version = 2
        captured_at = [DateTime]::UtcNow.ToString('o')
        status = 'NOT_RUN_PREPARATION_FAILED'
        run_number = $RunNumber
        flow_name = $FlowName
        process_id = $TargetProcessId
        expected_subflows = $expectedSubflows
        execution_requested = $false
        source_hashes = $sourceHashes
        source_bytes = $sourceBytes
        error = $_.Exception.Message
        fixed_at = $fixedAt.ToString('o')
    }
    Write-SubflowEvidence $failure
    return
}

$requestedAt = [DateTime]::UtcNow
$request = [ordered]@{
    schema_version = 1
    requested_at = $requestedAt.ToString('o')
    run_number = $RunNumber
    flow_name = $FlowName
    process_id = $TargetProcessId
    hwnd = [Int64]$window.Current.NativeWindowHandle
    selected_subflow = 'Main'
    expected_subflows = $expectedSubflows
    source_hashes = $sourceHashes
    source_bytes = $sourceBytes
    expected_variable = 'ButtonPressed'
    expected_preview = 'OK'
}
[IO.File]::WriteAllText($requestPath, ($request | ConvertTo-Json -Depth 12), (New-Object Text.UTF8Encoding($false)))

$states = New-Object System.Collections.Generic.List[object]
$runningObserved = $false
$completionObserved = $false
$last = $null
$invokedAt = $null
try {
    Invoke-AgentPadControl $before.start
    $invokedAt = [DateTime]::UtcNow
    $deadline = $invokedAt.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        try {
            $sample = Get-SubflowRunSample -Window $window
            if ($sample.running -or $sample.execution_observed) { $runningObserved = $true }
            $states.Add([ordered]@{ at = [DateTime]::UtcNow.ToString('o'); status = $sample.status; running = $sample.running; idle = $sample.idle; errors = $sample.errors; errors_known = $sample.errors_known })
            $last = $sample
            if ($runningObserved -and $sample.idle -and $sample.errors_known) { $completionObserved = $true; break }
        } catch {
            $states.Add([ordered]@{ at = [DateTime]::UtcNow.ToString('o'); observation_error = $_.Exception.Message })
        }
        Start-Sleep -Milliseconds 250
    }
} catch {
    $states.Add([ordered]@{ at = [DateTime]::UtcNow.ToString('o'); execution_error = $_.Exception.Message })
}

$previews = if ($null -ne $window) { Get-SubflowVariablePreviews $window } else { @() }
$buttonPressedMatch = @($previews | Where-Object { $_ -match '(?i)ButtonPressed\s*[:=→-]\s*OK' }).Count -gt 0
$afterHashes = [ordered]@{}
$sourceUnchanged = $true
foreach ($name in @('call', 'worker')) {
    $entry = $expectation.raw.$name
    $source = Resolve-SubflowSource ([string]$entry.source)
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash.ToLowerInvariant()
    $afterHashes[$name] = $hash
    if ($hash -cne $sourceHashes[$name]) { $sourceUnchanged = $false }
}
$status = if (-not $sourceUnchanged) { 'FAIL_SOURCE_CHANGED' } elseif ($completionObserved -and $last.errors -eq 0 -and $buttonPressedMatch) { 'success' } elseif (-not $runningObserved) { 'OBSERVATION_FAILED_AFTER_RUN_REQUEST' } elseif (-not $completionObserved) { 'OBSERVATION_TIMEOUT_AFTER_RUN_REQUEST' } else { 'FAIL_EXPECTATION_OR_RUNTIME_ERROR' }
$result = [ordered]@{
    schema_version = 2
    captured_at = [DateTime]::UtcNow.ToString('o')
    status = $status
    run_number = $RunNumber
    flow_name = $FlowName
    process_id = $TargetProcessId
    hwnd = [Int64]$window.Current.NativeWindowHandle
    expected_subflows = $expectedSubflows
    selected_subflow = 'Main'
    execution_requested = $true
    execution_invoked_at = if ($null -eq $invokedAt) { $null } else { $invokedAt.ToString('o') }
    running_observed = $runningObserved
    completion_observed = $completionObserved
    final_status = if ($null -eq $last) { $null } else { $last.status }
    final_error_count = if ($null -eq $last) { $null } else { $last.errors }
    variable_previews = $previews
    button_pressed_match = $buttonPressedMatch
    expected_variable = 'ButtonPressed'
    expected_preview = 'OK'
    source_hashes_before = $sourceHashes
    source_hashes_after = $afterHashes
    source_unchanged = $sourceUnchanged
    states = @($states)
    fixed_at = $fixedAt.ToString('o')
}
Write-SubflowEvidence $result
