[CmdletBinding()]
param(
    [switch]$Refresh
)

$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($PSScriptRoot)
$acceptancePath = Join-Path $root 'acceptance.json'
$twoRunPath = Join-Path $root 'two-run-result.json'
$hashPath = Join-Path $root 'files-sha256.json'
foreach ($path in @($acceptancePath, $twoRunPath, $hashPath)) {
    if ((Test-Path -LiteralPath $path) -and -not $Refresh) { throw ('Output exists; pass -Refresh to rebuild derived records: ' + $path) }
}

function Read-Json([string]$RelativePath) {
    Get-Content -Raw -LiteralPath (Join-Path $root $RelativePath) | ConvertFrom-Json
}

function Get-Sha([string]$RelativePath) {
    (Get-FileHash -LiteralPath (Join-Path $root $RelativePath) -Algorithm SHA256).Hash.ToLowerInvariant()
}

$scalarVariables = Read-Json 'candidate-scalar-direct-variables.json'
$scalarStyle = Read-Json 'candidate-scalar-direct-style.json'
$prefixVerification = Read-Json 'candidate-prefix-text/verification.json'
$run1Variables = Read-Json 'run1/variables.json'
$run2Variables = Read-Json 'run2/variables.json'
$run1Terminal = Read-Json 'run1/terminal.json'
$run2Terminal = Read-Json 'run2/terminal.json'
$run1Verification = Read-Json 'run1/verification.json'
$run2Verification = Read-Json 'run2/verification.json'
$run1Style = Read-Json 'run1/style.json'
$run2Style = Read-Json 'run2/style.json'
$oldReview = Get-Content -Raw -LiteralPath (Join-Path $root '..\..\cycles\EX03-r5-G1\review.md')
$null = git merge-base --is-ancestor f134afe1958d3acc1601e2861cec4139d2b13310 HEAD
$baselineIsAncestor = ($LASTEXITCODE -eq 0)

$checks = [ordered]@{
    baseline_commit_is_ancestor = $baselineIsAncestor
    source_fixture_sha_fixed = ((Get-Sha 'source.xlsx') -ceq 'dda07aac129a7f2f55bbd40067eda426b4b8f4f997254e7e9f69059803ac5874')
    template_fixture_sha_fixed = ((Get-Sha 'template.xlsx') -ceq '13855dcaf2fa8a9dd8d282197fd74c2f138d9ebc5552debbedbc5886296d2bde')
    scalar_direct_converts_immediately = ($scalarVariables.variables.ImmediateTextJson.preview -ceq '{"probe":1.0}' -and $scalarVariables.variables.SourceVsImmediateText.preview -ceq 'False')
    scalar_direct_changes_number_format = ($scalarStyle.differences.Count -eq 1 -and $scalarStyle.differences[0].location -ceq 'A2' -and $scalarStyle.differences[0].before.invariant -ceq 'G/標準' -and $scalarStyle.differences[0].after.invariant -ceq '0%')
    prefix_candidate_rejected_for_residual = ($prefixVerification.status -ceq 'FAIL' -and -not $prefixVerification.checks.text_prefix_character_preserved -and -not $prefixVerification.checks.no_residual_extra_character)
    final_robin_stable_across_two_runs = ((Get-Sha 'captured-final.robin') -ceq (Get-Sha 'run1/recopy.robin') -and (Get-Sha 'captured-final.robin') -ceq (Get-Sha 'run2/recopy.robin'))
    run1_pad_values_and_types_match = (@($run1Variables.variables.PSObject.Properties | Where-Object { $_.Name -match '^(SourceVsImmediate|SourceVsReopened|ImmediateVsReopened)' } | Where-Object { $_.Value.preview -cne 'True' }).Count -eq 0)
    run2_pad_values_and_types_match = (@($run2Variables.variables.PSObject.Properties | Where-Object { $_.Name -match '^(SourceVsImmediate|SourceVsReopened|ImmediateVsReopened)' } | Where-Object { $_.Value.preview -cne 'True' }).Count -eq 0)
    two_run_pad_variables_semantically_equal = (($run1Variables.variables | ConvertTo-Json -Depth 10 -Compress) -ceq ($run2Variables.variables | ConvertTo-Json -Depth 10 -Compress))
    run1_terminal_confirmed = ($run1Terminal.status -ceq 'TERMINAL_CONFIRMED' -and @($run1Terminal.checks.PSObject.Properties | Where-Object { -not $_.Value }).Count -eq 0)
    run2_terminal_confirmed = ($run2Terminal.status -ceq 'TERMINAL_CONFIRMED' -and @($run2Terminal.checks.PSObject.Properties | Where-Object { -not $_.Value }).Count -eq 0)
    run1_saved_reopened_verification_pass = ($run1Verification.status -ceq 'PASS' -and @($run1Verification.checks.PSObject.Properties | Where-Object { -not $_.Value }).Count -eq 0)
    run2_saved_reopened_verification_pass = ($run2Verification.status -ceq 'PASS' -and @($run2Verification.checks.PSObject.Properties | Where-Object { -not $_.Value }).Count -eq 0)
    run1_effective_style_match = ($run1Style.status -ceq 'MATCH_EFFECTIVE_FORMAT' -and $run1Style.differences.Count -eq 0)
    run2_effective_style_match = ($run2Style.status -ceq 'MATCH_EFFECTIVE_FORMAT' -and $run2Style.differences.Count -eq 0)
    no_formula_or_prefix_residual_in_both_runs = ($run1Verification.checks.no_formula_substitution -and $run1Verification.checks.no_residual_extra_character -and $run2Verification.checks.no_formula_substitution -and $run2Verification.checks.no_residual_extra_character)
    source_and_template_unchanged_by_verifiers = ($run1Verification.checks.hashes_unchanged_by_verifier -and $run2Verification.checks.hashes_unchanged_by_verifier)
    r5_unchanged_from_base = (@(git diff --name-only f134afe1958d3acc1601e2861cec4139d2b13310 -- catalog/copilot/versions/20260915-excel-r5).Count -eq 0)
    prior_ex03_evidence_unchanged_from_base = (@(git diff --name-only f134afe1958d3acc1601e2861cec4139d2b13310 -- catalog/acceptance/issue38/cycles/EX03-r5-G1).Count -eq 0)
    prior_ex03_run_uncertainty_still_recorded = ($oldReview -match '開始ボタン再有効化を確認できなかった')
    new_version_created = $false
    copilot_resent = $false
    full_ex03_rerun = $false
    github_write = $false
}
$passed = @($checks.GetEnumerator() | Where-Object { $_.Value -ne $true -and $_.Key -notin @('new_version_created', 'copilot_resent', 'full_ex03_rerun', 'github_write') }).Count -eq 0
$forbiddenActionsStayedFalse = (-not $checks.new_version_created -and -not $checks.copilot_resent -and -not $checks.full_ex03_rerun -and -not $checks.github_write)
$passed = $passed -and $forbiddenActionsStayedFalse

$twoRun = [ordered]@{
    schema_version = 1
    kind = 'ISSUE38_PERCENT_TEXT_TWO_RUN_RESULT'
    status = if ($passed) { 'PASS_LOCAL_PROBE_ONLY' } else { 'FAIL' }
    flow = [ordered]@{
        name = 'RobinIssue38PercentTextWrite20260916A'
        action_count = 40
        robin_sha256 = Get-Sha 'captured-final.robin'
        run1_recopy_sha256 = Get-Sha 'run1/recopy.robin'
        run2_recopy_sha256 = Get-Sha 'run2/recopy.robin'
    }
    fixed_source = [ordered]@{
        range = 'Source!A2:B2'
        text = [ordered]@{ value = '100%'; type = 'text'; json = '{"probe":"100%"}' }
        number = [ordered]@{ value = 42.5; type = 'number'; json = '{"probe":42.5}' }
    }
    runs = @(
        [ordered]@{
            run = 1
            pad_before = [ordered]@{ text_json = $run1Variables.variables.BeforeTextJson.preview; number_json = $run1Variables.variables.BeforeNumberJson.preview }
            pad_immediate = [ordered]@{ text_json = $run1Variables.variables.ImmediateTextJson.preview; number_json = $run1Variables.variables.ImmediateNumberJson.preview; audit = $run1Terminal.variables.parsed_powershell_output }
            pad_reopened = [ordered]@{ text_json = $run1Variables.variables.ReopenedTextJson.preview; number_json = $run1Variables.variables.ReopenedNumberJson.preview }
            artifact_reopened = $run1Verification.output_after_reopen
            style_status = $run1Style.status
            terminal_status = $run1Terminal.status
            output_sha256 = $run1Verification.sha256_before.output
        },
        [ordered]@{
            run = 2
            pad_before = [ordered]@{ text_json = $run2Variables.variables.BeforeTextJson.preview; number_json = $run2Variables.variables.BeforeNumberJson.preview }
            pad_immediate = [ordered]@{ text_json = $run2Variables.variables.ImmediateTextJson.preview; number_json = $run2Variables.variables.ImmediateNumberJson.preview; audit = $run2Terminal.variables.parsed_powershell_output }
            pad_reopened = [ordered]@{ text_json = $run2Variables.variables.ReopenedTextJson.preview; number_json = $run2Variables.variables.ReopenedNumberJson.preview }
            artifact_reopened = $run2Verification.output_after_reopen
            style_status = $run2Style.status
            terminal_status = $run2Terminal.status
            output_sha256 = $run2Verification.sha256_before.output
        }
    )
}

$acceptance = [ordered]@{
    schema_version = 1
    audited_at = [DateTime]::UtcNow.ToString('o')
    status = if ($passed) { 'PASS_LOCAL_PROBE_ONLY' } else { 'FAIL' }
    baseline_commit = 'f134afe1958d3acc1601e2861cec4139d2b13310'
    cause = 'Excel.WriteToExcel.WriteCell applies Excel input interpretation to the text token 100% immediately, converting it to numeric 1 and changing General to 0%; save/reopen only persists the already-converted state.'
    adopted_method = 'For the verified text cell only, attach to the exact active workbook, temporarily set the destination NumberFormat to @, assign the string Value2, restore the previously captured NumberFormat immediately, and reject any non-string value, format mismatch, or PrefixCharacter. Numeric cells retain the ordinary numeric WriteCell path.'
    checks = $checks
    hashes = [ordered]@{
        source_xlsx = Get-Sha 'source.xlsx'
        template_xlsx = Get-Sha 'template.xlsx'
        captured_action_v2 = Get-Sha 'captured-powershell-format-action-v2.robin'
        captured_final_robin = Get-Sha 'captured-final.robin'
        run1_result = Get-Sha 'run1/result.xlsx'
        run2_result = Get-Sha 'run2/result.xlsx'
    }
    limits = @(
        'Verified only for the fixed synthetic Source!A2:B2 values: text 100% and numeric 42.5.',
        'The PowerShell action is bound to the exact probe workbook, sheet, and cell and is not yet integrated into EX03 or the r5 bundle.',
        'Blank, boolean, date, error, formula-result, object, other text tokens, other PAD versions, and other computers remain unverified.',
        'The earlier EX03-r5-G1 Run completion observation uncertainty remains a separate unresolved item.'
    )
}

$utf8 = New-Object Text.UTF8Encoding($false)
[IO.File]::WriteAllText($twoRunPath, ($twoRun | ConvertTo-Json -Depth 16), $utf8)
[IO.File]::WriteAllText($acceptancePath, ($acceptance | ConvertTo-Json -Depth 16), $utf8)

$fileHashes = [ordered]@{}
Get-ChildItem -LiteralPath $root -Recurse -File | Where-Object { $_.FullName -cne $hashPath } | Sort-Object FullName | ForEach-Object {
    $relative = [IO.Path]::GetRelativePath($root, $_.FullName).Replace('\', '/')
    $fileHashes[$relative] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
$hashRecord = [ordered]@{
    schema_version = 1
    generated_at = [DateTime]::UtcNow.ToString('o')
    root = 'catalog/acceptance/issue38/probes/percent-text-write'
    excludes = @('files-sha256.json')
    files = $fileHashes
}
[IO.File]::WriteAllText($hashPath, ($hashRecord | ConvertTo-Json -Depth 6), $utf8)

[pscustomobject]@{
    status = $acceptance.status
    check_count = $checks.Count
    file_count = $fileHashes.Count
    final_robin_sha256 = $acceptance.hashes.captured_final_robin
    run1_result_sha256 = $acceptance.hashes.run1_result
    run2_result_sha256 = $acceptance.hashes.run2_result
} | ConvertTo-Json
if (-not $passed) { exit 2 }
