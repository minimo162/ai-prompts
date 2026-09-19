[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$FlowName,
    [Parameter(Mandatory = $true)][int]$FlowWindowId
)

$ErrorActionPreference = 'Stop'
$trial = Join-Path $PSScriptRoot 'trials/EX03-R12-FIXED-HELPER-P1-T1'
$runtime = Join-Path $trial 'runtime'
$candidatePath = Join-Path $trial 'candidate.robin'
$recopyPath = Join-Path $trial 'pad-recopy-mismatch.robin'
$recordPath = Join-Path $trial 'pad-recopy-mismatch.json'
$expectedCandidateSha = '0a84679b0b9875780aa70c975602a7404af0dd82fcf9b13978fe9c1e036f5b94'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..\..'))
$preflight = Get-Content -LiteralPath (Join-Path $trial 'preflight.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$templatePath = Join-Path $root ([string]$preflight.files.template.path)
$workPath = [string]$preflight.paths.target_workbook
$outputPath = [string]$preflight.paths.output

foreach ($path in @($candidatePath, $templatePath, $workPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required file missing: $path" }
}
foreach ($path in @($recopyPath, $recordPath)) {
    if (Test-Path -LiteralPath $path) { throw "Refusing overwrite: $path" }
}

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

function Get-FileSha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$candidateSha = Get-Sha256Text $candidate
if ($candidateSha -cne $expectedCandidateSha) { throw 'Candidate SHA changed before mismatch recording' }
$recopySha = Get-Sha256Text $recopy
$candidateLf = $candidate.Replace("`r`n", "`n")
$recopyLf = $recopy.Replace("`r`n", "`n")
$candidateTrimmed = $candidateLf.TrimEnd("`r", "`n")
$recopyTrimmed = $recopyLf.TrimEnd("`r", "`n")

$limit = [Math]::Min($candidate.Length, $recopy.Length)
$firstDifference = -1
for ($index = 0; $index -lt $limit; $index++) {
    if ($candidate[$index] -cne $recopy[$index]) {
        $firstDifference = $index
        break
    }
}
if ($firstDifference -lt 0 -and $candidate.Length -ne $recopy.Length) {
    $firstDifference = $limit
}

$jsonFiles = @()
for ($index = 1; $index -le 7; $index++) { $jsonFiles += Join-Path $runtime "source-$index.json" }
$jsonFiles += Join-Path $runtime 'mode.json'
$jsonPresent = @($jsonFiles | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })
$templateSha = Get-FileSha256 $templatePath
$workSha = Get-FileSha256 $workPath
if ($templateSha -cne $workSha) { throw 'Work copy changed before the authorized Run' }
if (Test-Path -LiteralPath $outputPath) { throw 'Output exists even though PAD Run was not authorized after mismatch' }
if ($jsonPresent.Count) { throw 'JSON handoff files exist even though PAD Run was not authorized after mismatch' }

[IO.File]::WriteAllText($recopyPath, $recopy, $utf8)
$record = [ordered]@{
    schema_version = 1
    trial_id = 'EX03-R12-FIXED-HELPER-P1-T1'
    recorded_utc = [DateTime]::UtcNow.ToString('o')
    decision = 'STOP_PAD_RECOPY_NOT_BYTE_EXACT_NO_RUN'
    flow = [ordered]@{
        name = $FlowName
        window_id = $FlowWindowId
        subflow = 'Main'
        power_fx = 'OFF'
    }
    observation = [ordered]@{
        paste_invocations = 1
        save_invocations = 1
        recopy_invocations = 1
        pad_run_count = 0
        helper_execution_count = 0
        excel_execution_count = 0
        designer_status_after_save = 'READY'
        designer_error_observed = $false
    }
    comparison = [ordered]@{
        candidate_path = 'catalog/acceptance/issue38/probes/ex03-r12-fixed-helper/trials/EX03-R12-FIXED-HELPER-P1-T1/candidate.robin'
        candidate_sha256 = $candidateSha
        candidate_characters = $candidate.Length
        candidate_utf8_bytes = $utf8.GetByteCount($candidate)
        candidate_crlf_count = [regex]::Matches($candidate, "`r`n").Count
        candidate_lf_only_count = [regex]::Matches($candidate, "(?<!`r)`n").Count
        candidate_final_newline = $candidate.EndsWith("`n") -or $candidate.EndsWith("`r")
        recopy_path = 'catalog/acceptance/issue38/probes/ex03-r12-fixed-helper/trials/EX03-R12-FIXED-HELPER-P1-T1/pad-recopy-mismatch.robin'
        recopy_sha256 = $recopySha
        recopy_characters = $recopy.Length
        recopy_utf8_bytes = $utf8.GetByteCount($recopy)
        recopy_crlf_count = [regex]::Matches($recopy, "`r`n").Count
        recopy_lf_only_count = [regex]::Matches($recopy, "(?<!`r)`n").Count
        recopy_final_newline = $recopy.EndsWith("`n") -or $recopy.EndsWith("`r")
        exact_text_and_utf8_bytes = $false
        lf_normalized_exact = $candidateLf -ceq $recopyLf
        lf_normalized_trim_final_newline_exact = $candidateTrimmed -ceq $recopyTrimmed
        first_utf16_difference_index = $firstDifference
    }
    stopped_state = [ordered]@{
        template_sha256 = $templateSha
        work_sha256 = $workSha
        work_still_exact_template = $true
        output_absent = $true
        json_handoff_files_absent = $true
        launcher_not_invoked = $true
        helper_not_invoked = $true
        numeric_writes_not_entered = $true
        save_as_not_entered = $true
    }
    prohibited_after_stop = [ordered]@{
        second_recopy = 0
        repaste = 0
        pad_run = 0
        candidate_change = 0
        formal_ex03_r12_run = 0
        copilot_send = 0
        github_write = 0
    }
}
[IO.File]::WriteAllText($recordPath, (($record | ConvertTo-Json -Depth 8) + "`n"), $utf8)
$record | ConvertTo-Json -Depth 8
