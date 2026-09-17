[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$FlowName,
    [Parameter(Mandatory = $true)][int]$FlowWindowId
)

$ErrorActionPreference = 'Stop'
$trial = Join-Path $PSScriptRoot 'trials/EX03-R12-FIXED-HELPER-P1-T1'
$candidatePath = Join-Path $trial 'candidate.robin'
$recopyPath = Join-Path $trial 'pad-recopy-before-run.robin'
$recordPath = Join-Path $trial 'pad-recopy.json'
$expectedCandidateSha = '0a84679b0b9875780aa70c975602a7404af0dd82fcf9b13978fe9c1e036f5b94'

if (-not (Test-Path -LiteralPath $candidatePath -PathType Leaf)) { throw 'Trial candidate missing' }
if (Test-Path -LiteralPath $recopyPath) { throw 'Refusing to overwrite PAD re-copy' }
if (Test-Path -LiteralPath $recordPath) { throw 'Refusing to overwrite PAD re-copy record' }

$utf8 = [Text.UTF8Encoding]::new($false)
$candidate = [IO.File]::ReadAllText($candidatePath, $utf8)
$recopy = Get-Clipboard -Raw
if ([string]::IsNullOrEmpty($recopy)) { throw 'PAD re-copy clipboard is empty' }
if ($recopy -ceq 'ISSUE38_FIXED_HELPER_RECOPY_SENTINEL') { throw 'PAD copy did not replace the sentinel' }

function Get-Sha256Text([string]$Value) {
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($algorithm.ComputeHash($utf8.GetBytes($Value)))).Replace('-', '').ToLowerInvariant()
    }
    finally { $algorithm.Dispose() }
}

$candidateSha = Get-Sha256Text $candidate
$recopySha = Get-Sha256Text $recopy
if ($candidateSha -cne $expectedCandidateSha) { throw 'Candidate SHA changed before re-copy capture' }
if ($candidate -cne $recopy) { throw 'PAD saved re-copy is not byte-exact candidate text' }

$required = @(
    'Scripting.RunPowershellScript.RunScript',
    'EX03-R12-Fixed-StringTransfer.ps1',
    'EX03-R12-FIXED-HELPER-P1-T1\\invocation.json',
    'SAVED_REOPENED_12_JSON_COMPARISONS_READY',
    '追記先_F6_ValueTypeMatch TO SourceCellJson = SavedCellJson'
)
$forbidden = @(
    'Invoke-Expression', 'ScriptBlock]::Create', 'Start-Process', 'Remove-Item',
    'Invoke-WebRequest', 'Invoke-RestMethod', 'File.Delete', 'Folder.Delete',
    'WebAutomation.', 'HTTP.'
)
$missing = @($required | Where-Object { -not $recopy.Contains($_) })
$presentForbidden = @($forbidden | Where-Object { $recopy.Contains($_) })
if ($missing.Count) { throw ('Required fragment missing: ' + ($missing -join ', ')) }
if ($presentForbidden.Count) { throw ('Forbidden fragment present: ' + ($presentForbidden -join ', ')) }

[IO.File]::WriteAllText($recopyPath, $recopy, $utf8)
$record = [ordered]@{
    schema_version = 1
    trial_id = 'EX03-R12-FIXED-HELPER-P1-T1'
    captured_utc = [DateTime]::UtcNow.ToString('o')
    environment = [ordered]@{
        pad_file_version = '2.71.115.26224'
        language = 'ja-JP'
        power_fx = 'OFF'
        flow_name = $FlowName
        flow_window_id = $FlowWindowId
        subflow = 'Main'
    }
    observation = [ordered]@{
        initial_actions = 0
        paste_invocations = 1
        save_invocations = 1
        recopy_invocations = 1
        executed_before_capture = $false
        designer_status_after_save = 'READY'
        designer_error_observed = $false
    }
    comparison = [ordered]@{
        candidate_path = 'catalog/acceptance/issue38/probes/ex03-r12-fixed-helper/trials/EX03-R12-FIXED-HELPER-P1-T1/candidate.robin'
        candidate_sha256 = $candidateSha
        recopy_path = 'catalog/acceptance/issue38/probes/ex03-r12-fixed-helper/trials/EX03-R12-FIXED-HELPER-P1-T1/pad-recopy-before-run.robin'
        recopy_sha256 = $recopySha
        exact_text_and_utf8_bytes = $true
        characters = $candidate.Length
        lines = $candidate.Split("`n").Count
        crlf_count = [regex]::Matches($candidate, "`r`n").Count
        lf_only_count = [regex]::Matches($candidate, "(?<!`r)`n").Count
        required_fragments_present = $true
        forbidden_fragments_absent = $true
    }
    result = 'PASS_EXACT_PAD_SAVE_RECOPY_BEFORE_ONLY_RUN'
}
[IO.File]::WriteAllText($recordPath, (($record | ConvertTo-Json -Depth 8) + "`n"), $utf8)
$record | ConvertTo-Json -Depth 8
