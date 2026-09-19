param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Normal', 'Negative')]
    [string]$Mode
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

$probe = Split-Path -Parent $PSCommandPath
$trialId = 'EX03-R2R3-POSTFIX-20260917-T1'
$label = $Mode.ToLowerInvariant()
$phase = Join-Path (Join-Path (Join-Path $probe 'trials') $trialId) $label
$candidatePath = Join-Path $phase 'candidate.robin'
$recopyPath = Join-Path $phase 'pad-recopy-before-run.robin'
$recordPath = Join-Path $phase 'pad-recopy.json'
$utf8 = [Text.UTF8Encoding]::new($false)

if (Test-Path -LiteralPath $recopyPath) { throw "Refusing to overwrite re-copy: $recopyPath" }
if (Test-Path -LiteralPath $recordPath) { throw "Refusing to overwrite capture record: $recordPath" }

$candidate = [IO.File]::ReadAllText($candidatePath, $utf8)
$recopy = Get-Clipboard -Raw
if ([string]::IsNullOrEmpty($recopy)) { throw 'PAD re-copy clipboard is empty' }
if ($recopy -ceq '__ISSUE38_POSTFIX_RECOPY_SENTINEL__') { throw 'PAD re-copy did not replace the sentinel' }
if ($candidate -cne $recopy) { throw 'PAD saved re-copy differs from the path-bound candidate' }

[IO.File]::WriteAllText($recopyPath, $recopy, $utf8)
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $candidatePath).Hash -cne (Get-FileHash -Algorithm SHA256 -LiteralPath $recopyPath).Hash) {
    throw 'Re-copy file SHA differs after capture'
}

$record = [ordered]@{
    schema_version = 1
    trial_id = $trialId
    phase = $label
    result = 'PASS_EXACT_PAD_SAVE_RECOPY_BEFORE_RUN'
    candidate_path = [IO.Path]::GetRelativePath($probe, $candidatePath).Replace('\', '/')
    candidate_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $candidatePath).Hash.ToLowerInvariant()
    recopy_path = [IO.Path]::GetRelativePath($probe, $recopyPath).Replace('\', '/')
    recopy_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $recopyPath).Hash.ToLowerInvariant()
    exact_text = $true
    exact_bytes = $true
    recopy_chars = $recopy.Length
    recopy_crlf_count = [regex]::Matches($recopy, "`r`n").Count
    recopy_lf_only_count = [regex]::Matches($recopy, "(?<!`r)`n").Count
    paste_invocations = 1
    save_invocations = 1
    recopy_invocations = 1
    run_invocations_at_capture = 0
}
[IO.File]::WriteAllText(
    $recordPath,
    (($record | ConvertTo-Json -Depth 5) + "`n"),
    $utf8
)
$record | ConvertTo-Json -Compress
