[CmdletBinding()]
param([string]$Root)
if (-not $Root) { $Root = Split-Path -Parent $PSScriptRoot }
$ErrorActionPreference = 'Stop'
$checks = 0
function Check([bool]$Value, [string]$Name) {
    if (-not $Value) { throw ('C_CELL_READ: ' + $Name) }
    $script:checks++
}
function Read-Record([string]$Name) {
    return ([IO.File]::ReadAllText((Join-Path $dir $Name), [Text.Encoding]::UTF8) | ConvertFrom-Json)
}
function Test-ScalarWitness($Before, $After, [string]$Expected) {
    return ($Before.ready -eq $true -and $Before.running -eq $false -and
        $null -ne $Before.previews -and @($Before.previews).Count -eq 0 -and
        $After.status -ceq 'ready' -and $After.running -eq $false -and
        $After.errors_known -eq $true -and $After.errors -eq 0 -and
        @($After.variables | Where-Object { $_.variable -ceq 'CellReadValue' -and $_.preview -ceq $Expected }).Count -eq 1)
}
$dir = Join-Path $Root 'catalog/evidence/c-cell-read-20260914v'
$a = Read-Record 'acceptance.json'
$e = Read-Record 'expectation.json'
Check ($a.status -ceq 'PASS_REQUIRED_CELL_READ_NATIVE_REUSE') 'native scope status'
Check ($a.package.version -ceq '20260913e' -and -not $a.package.instruction_knowledge_bundle_changed -and -not $a.package.new_generation_claimed) 'no package or generation promotion'
Check ($a.source.read_configuration.value_expression -ceq '%DataTable[0][0]%') 'UI expression is recorded'
Check ($a.reuse.empty_before_paste -and $a.reuse.source_file_pasted_without_edit -and $a.reuse.saved_then_closed_and_reopened) 'file reuse stages'
Check ($a.reuse.flow_name -cne $a.source.flow_name) 'separate source and reuse flows'
Check ($a.counts.pad_run_starts -eq 2 -and $a.counts.reuse_flow_runs -eq 2 -and $a.counts.source_flow_runs -eq 0) 'exactly two native runs'
Check ($a.counts.copilot_sends -eq 0 -and $a.counts.extra_run_after_observer_error -eq 0) 'no resend or duplicate run'
Check ($e.fixed_before_configuration_and_run -and $e.required_reuse_runs -eq 2 -and $e.expected_output.type -ceq 'Text') 'fixed scalar expectation'
foreach ($f in $a.files) {
    $path = Join-Path $Root $f.path
    Check (Test-Path -LiteralPath $path -PathType Leaf) ('original exists: ' + $f.path)
    Check ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ceq $f.sha256 -and (Get-Item -LiteralPath $path).Length -eq $f.bytes) ('original hash/bytes: ' + $f.path)
}
$copies = @($a.reuse.copies)
Check ($copies.Count -eq 4) 'all four copy stages'
foreach ($copy in $copies) {
    $path = Join-Path $dir $copy
    Check ((Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() -ceq $a.source.raw_sha256) ('raw equality, no normalization: ' + $copy)
    $lines = [IO.File]::ReadAllLines($path, [Text.Encoding]::UTF8)
    Check ($lines.Count -eq 2 -and $lines[0].StartsWith('Variables.CreateNewDatatable ') -and $lines[1] -ceq 'SET CellReadValue TO DataTable[0][0]') ('cell read RHS, not update: ' + $copy)
}
$paste = Read-Record 'reuse-paste.json'
Check ($paste.empty_before_paste -and $paste.paste_confirmed -and $paste.designer_action_count -eq 2 -and -not $paste.execution_requested) 'original paste record'
Check ([IO.File]::ReadAllText((Join-Path $dir 'reuse-save.txt')).Contains('SAVED=RobinKnowledgeCCellReadReuse_20260914v')) 'original save observation'
foreach ($number in @(1,2)) {
    $before = Read-Record ('run' + $number + '-before.json')
    $after = Read-Record $(if ($number -eq 1) { 'run1-observed-values.json' } else { 'run2-observer-recovery.json' })
    $request = Read-Record ('run' + $number + '-request.json')
    Check (Test-ScalarWitness $before $after $e.expected_output.value) ('fresh scalar witness run ' + $number)
    Check ($request.request_count -eq 1 -and $request.expectation_sha256 -ceq (Get-FileHash (Join-Path $dir 'expectation.json')).Hash.ToLowerInvariant()) ('one request with fixed expectation ' + $number)
}
$recovery = Read-Record 'run2-observer-recovery.json'
Check ($recovery.observation_only -and -not $recovery.additional_run_requested -and $recovery.helper_error) 'same-run observer failure preserved'
Check (-not (Test-Path -LiteralPath (Join-Path $dir 'run2.json'))) 'missing original helper output is not manufactured'
$goodBefore = Read-Record 'run1-before.json'
$goodAfter = Read-Record 'run1-observed-values.json'
$badBefore = Read-Record 'run1-before.json'
$badBefore.previews = @($e.expected_output.value)
Check (-not (Test-ScalarWitness $badBefore $goodAfter $e.expected_output.value)) 'reject residual value as a fresh run'
$badAfter = Read-Record 'run1-observed-values.json'
$badAfter.variables = @()
Check (-not (Test-ScalarWitness $goodBefore $badAfter $e.expected_output.value)) 'reject missing scalar output'
$badAfter.variables = @([pscustomobject]@{variable='CellReadValue';preview='1 row, 2 columns'})
Check (-not (Test-ScalarWitness $goodBefore $badAfter $e.expected_output.value)) 'reject DataTable preview as scalar proof'
$badAfter = Read-Record 'run1-observed-values.json'
$badAfter.errors_known = $false
Check (-not (Test-ScalarWitness $goodBefore $badAfter $e.expected_output.value)) 'reject unknown error state'
Check ($a.preserved.t04_old_run1 -ceq 'NOT_CAPTURED' -and $a.preserved.t10_strict_raw_bytes -ceq 'NOT_PROVEN') 'T04 and T10 boundaries preserved'
Write-Output ('PASS: ' + $checks + ' C DataTable cell-read evidence checks; no PAD/Copilot actions.')
