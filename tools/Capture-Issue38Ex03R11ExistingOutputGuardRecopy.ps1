[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][int]$ObservedActionCount,
    [Parameter(Mandatory = $true)][int]$ObservedVariableCount,
    [Parameter(Mandatory = $true)][int]$FlowWindowId,
    [string]$Root
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = Split-Path -Parent $PSScriptRoot
}
$rootPath = [IO.Path]::GetFullPath($Root)
$cycle = Join-Path $rootPath 'catalog/acceptance/issue38/cycles/EX03-r11-file-aux1-existing-output-neg1'
$candidatePath = Join-Path $rootPath 'catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/copilot-downloaded-ex03.robin'
$recopyPath = Join-Path $cycle 'pad-recopy-before-guard-run.robin'
$recordPath = Join-Path $cycle 'pad-recopy.json'
$expectedSha = 'a1e07de1f9370640773fcd8d36db1a2effe602f175bb437cb7c65457f6f24875'
$testId = 'EX03-R11-FILE-AUX1-EXISTING-OUTPUT-NEG1'
$flowName = ([string][char]0x7121) + ([string][char]0x984C) + ' (10)'

if (-not (Test-Path -LiteralPath $cycle -PathType Container)) { throw 'Dedicated guard cycle missing' }
if (-not (Test-Path -LiteralPath $candidatePath -PathType Leaf)) { throw 'FILE-AUX1 candidate missing' }
if (Test-Path -LiteralPath $recordPath) { throw 'Refusing to overwrite guard re-copy evidence' }
if ($ObservedActionCount -ne 110 -or $ObservedVariableCount -ne 45) { throw 'Observed PAD counts differ from FILE-AUX1' }
$utf8 = [Text.UTF8Encoding]::new($false)
$candidate = [IO.File]::ReadAllText($candidatePath, $utf8)
$recopy = Get-Clipboard -Raw
if ([string]::IsNullOrEmpty($recopy)) { throw 'PAD re-copy clipboard is empty' }
$normalizedCandidate = $candidate.Replace("`r`n", "`n").TrimEnd("`r", "`n")
$normalizedRecopy = $recopy.Replace("`r`n", "`n").TrimEnd("`r", "`n")
if ($normalizedCandidate -cne $normalizedRecopy) { throw 'PAD re-copy differs outside newline serialization' }

function Get-Sha256Text([string]$Value) {
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($algorithm.ComputeHash($utf8.GetBytes($Value)))).Replace('-', '').ToLowerInvariant() }
    finally { $algorithm.Dispose() }
}

if ((Get-Sha256Text $candidate) -cne $expectedSha) { throw 'Candidate SHA changed before guard re-copy capture' }
if ($normalizedRecopy.Split("`n").Count -ne 167) { throw 'Unexpected normalized Robin line count' }
if (-not $recopy.Contains("SET TransferState TO `$'''OUTPUT_EXISTS_NO_WRITE'''")) { throw 'Guard fragment missing from re-copy' }
if (($recopy -split "Excel.SaveExcel.SaveAs").Count -ne 2) { throw 'Unexpected SaveAs count in re-copy' }

[IO.File]::WriteAllText($recopyPath, $recopy, $utf8)
$record = [ordered]@{
    schema_version = 1
    test_id = $testId
    captured_utc = [DateTime]::UtcNow.ToString('o')
    flow_name = $flowName
    flow_window_id = $FlowWindowId
    subflow = 'Main'
    power_fx = 'OFF'
    guard_run_execution_before_capture = $false
    observation = [ordered]@{
        recopy_invocations = 1
        actions_visible = $ObservedActionCount
        variables_visible = $ObservedVariableCount
        designer_error_observed = $false
    }
    comparison = [ordered]@{
        candidate_path = 'catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/copilot-downloaded-ex03.robin'
        candidate_sha256 = Get-Sha256Text $candidate
        recopy_path = 'catalog/acceptance/issue38/cycles/EX03-r11-file-aux1-existing-output-neg1/pad-recopy-before-guard-run.robin'
        recopy_sha256 = Get-Sha256Text $recopy
        exact_text = $candidate -ceq $recopy
        lf_normalized_exact = $true
        candidate_lines = $candidate.Split("`n").Count
        recopy_raw_lines = $recopy.Split("`n").Count
        recopy_normalized_lines = $normalizedRecopy.Split("`n").Count
        guard_fragment_present = $true
        save_as_count = 1
    }
    result = 'PASS_UNMODIFIED_R11_FILE_AUX1_PAD_RECOPY_BEFORE_GUARD_RUN'
}
[IO.File]::WriteAllText($recordPath, (($record | ConvertTo-Json -Depth 8) + "`n"), $utf8)
$record | ConvertTo-Json -Depth 8
