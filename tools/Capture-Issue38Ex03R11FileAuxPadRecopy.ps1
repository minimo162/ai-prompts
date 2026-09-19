[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][int]$ObservedActionCount,
    [Parameter(Mandatory = $true)][int]$ObservedVariableCount,
    [string]$Root
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = Split-Path -Parent $PSScriptRoot
}
$rootPath = [IO.Path]::GetFullPath($Root)
$cycle = Join-Path $rootPath 'catalog/acceptance/issue38/cycles/EX03-r11-file-aux1'
$candidatePath = Join-Path $cycle 'copilot-downloaded-ex03.robin'
$recopyPath = Join-Path $cycle 'pad-recopy-before-run.robin'
$recordPath = Join-Path $cycle 'pad-recopy.json'
$flowName = ([string][char]0x7121) + ([string][char]0x984C) + ' (10)'
$flowWindowId = 71280
$expectedSha = 'a1e07de1f9370640773fcd8d36db1a2effe602f175bb437cb7c65457f6f24875'

if (-not (Test-Path -LiteralPath $candidatePath -PathType Leaf)) { throw 'Auxiliary candidate missing' }
if (Test-Path -LiteralPath $recordPath) { throw 'Refusing to overwrite PAD re-copy evidence' }
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

if ((Get-Sha256Text $candidate) -cne $expectedSha) { throw 'Candidate SHA changed before PAD re-copy capture' }
$required = @(
    'SAVED_REOPENED_12_JSON_COMPARISONS_READY',
    'Scripting.RunPowershellScript.RunScript',
    '[IO.Path]::GetFullPath([string]$candidate.FullName) -ieq $targetPath',
    '$cell.Value2 = [string]$payload.probe',
    'finally { $cell.NumberFormat = $beforeNumberFormat }',
    'F6_ValueTypeMatch TO SourceCellJson = SavedCellJson'
)
$forbidden = @('File.Delete', 'Folder.Delete', 'WebAutomation.', 'HTTP.', 'Start-Process', 'Remove-Item')
$missing = @($required | Where-Object { -not $recopy.Contains($_) })
$presentForbidden = @($forbidden | Where-Object { $recopy.Contains($_) })
if ($missing.Count -ne 0) { throw ('Required fragment missing: ' + ($missing -join ', ')) }
if ($presentForbidden.Count -ne 0) { throw ('Forbidden fragment present: ' + ($presentForbidden -join ', ')) }
if ($normalizedRecopy.Split("`n").Count -ne 167) { throw 'Unexpected PAD re-copy normalized line count' }

[IO.File]::WriteAllText($recopyPath, $recopy, $utf8)
$record = [ordered]@{
    schema_version = 1
    test_id = 'EX03-R11-FILE-AUX1'
    captured_utc = [DateTime]::UtcNow.ToString('o')
    flow_name = $flowName
    flow_window_id = $flowWindowId
    flow_creation_note = 'PAD create dialog did not retain the preferred name; PAD assigned this unique new name automatically before any Robin paste.'
    subflow = 'Main'
    power_fx = 'OFF'
    execution_before_capture = $false
    observation = [ordered]@{
        paste_invocations = 1
        save_invocations = 1
        recopy_invocations = 1
        actions_after_paste = $ObservedActionCount
        variables_after_paste = $ObservedVariableCount
        designer_error_observed = $false
    }
    comparison = [ordered]@{
        candidate_path = 'catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/copilot-downloaded-ex03.robin'
        candidate_sha256 = Get-Sha256Text $candidate
        recopy_path = 'catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/pad-recopy-before-run.robin'
        recopy_sha256 = Get-Sha256Text $recopy
        exact_text = $candidate -ceq $recopy
        lf_normalized_exact = $true
        candidate_chars = $candidate.Length
        recopy_chars = $recopy.Length
        candidate_lines = $candidate.Split("`n").Count
        recopy_raw_lines = $recopy.Split("`n").Count
        recopy_normalized_lines = $normalizedRecopy.Split("`n").Count
        required_fragments_present = $true
        forbidden_fragments_absent = $true
    }
    result = 'PASS_UNMODIFIED_PAD_SAVE_RECOPY_BEFORE_RUN1'
}
[IO.File]::WriteAllText($recordPath, (($record | ConvertTo-Json -Depth 8) + "`n"), $utf8)
$record | ConvertTo-Json -Depth 8
