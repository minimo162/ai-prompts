[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$utf8 = [Text.Encoding]::UTF8
$checks = 0
function Check([bool]$Value, [string]$Name) { if (-not $Value) { throw ('FAIL: ' + $Name) }; $script:checks++ }
function Read-Json([string]$RelativePath) { return ([IO.File]::ReadAllText((Join-Path $repo $RelativePath), $utf8) | ConvertFrom-Json) }
function Hash([string]$RelativePath) { return (Get-FileHash -LiteralPath (Join-Path $repo $RelativePath) -Algorithm SHA256).Hash.ToLowerInvariant() }

$coverage = Read-Json 'catalog\coverage.json'
$auditRelative = if ($coverage.current_package.PSObject.Properties.Name -contains 'audit' -and -not [string]::IsNullOrWhiteSpace([string]$coverage.current_package.audit)) { [string]$coverage.current_package.audit } else { 'evidence/issue5-completion-audit-20260911.json' }
$audit = Read-Json ('catalog\' + $auditRelative.Replace('/','\'))
$precheckRelative = [string]$coverage.current_package.knowledge_precheck
$precheck = Read-Json ('catalog\' + $precheckRelative.Replace('/','\'))
$stageExpired = Read-Json 'catalog\evidence\t01-current-bundle-stage-expired-20260911.json'
$bundleHash = Hash 'copilot\knowledge\PAD-Robin-Knowledge-Bundle.txt'
$instructionHash = Hash 'copilot\agent-instructions.txt'

Check ($bundleHash -ceq $coverage.current_package.knowledge_bundle_sha256) 'coverage bundle hash matches file'
Check ($instructionHash -ceq $coverage.current_package.instruction_sha256) 'coverage instruction hash matches file'
Check (($coverage.current_package.status -cin @('partial_new_bundle_t08_error_handler_added_live_reacceptance_pending','partial_new_bundle_t08_composed_error_reference_live_reacceptance_pending','partial_t08_pass_live_remainder_pending','partial_new_bundle_t08_final_reacceptance_pending','partial_t08_pass_final_bundle_remainder_pending','partial_new_bundle_t08_t01_reacceptance_pending','partial_t01_t08_pass_final2_bundle_remainder_pending','partial_new_final_bundle_acceptance_pending','partial_t09_runtime_p3_independent_negative_pending')) -or ($coverage.current_package.status -like '*knowledge_precheck_pass*' -and $coverage.current_package.status -like '*t01_t10_pending*')) 'coverage keeps partial current status'
foreach ($field in @('knowledge_precheck','t01_prepared','t01_stage_current')) {
    $relative = $coverage.current_package.$field
    Check (-not [string]::IsNullOrWhiteSpace($relative)) ('coverage field exists: ' + $field)
    Check (Test-Path -LiteralPath (Join-Path $repo ('catalog\' + $relative)) -PathType Leaf) ('coverage path exists: ' + $field)
}
if ($audit.PSObject.Properties.Name -contains 'p4_current_bundle') {
    Check ($audit.package.bundle_sha256 -ceq $bundleHash) 'new audit binds current bundle'
    Check ($audit.p4_current_bundle.status -cin @('PARTIAL_NEW_BUNDLE_LIVE_ACCEPTANCE_PENDING','PARTIAL_T08_PASS_LIVE_REMAINDER_PENDING','PARTIAL_T08_PASS_FINAL_BUNDLE_REMAINDER_PENDING','PARTIAL_T01_T08_PASS_FINAL2_BUNDLE_REMAINDER_PENDING','PARTIAL_T09_RUNTIME_P3_INDEPENDENT_NEGATIVE_PENDING')) 'new audit keeps live acceptance partial'
    if ($audit.p4_current_bundle.status -cin @('PARTIAL_T08_PASS_LIVE_REMAINDER_PENDING','PARTIAL_T08_PASS_FINAL_BUNDLE_REMAINDER_PENDING','PARTIAL_T01_T08_PASS_FINAL2_BUNDLE_REMAINDER_PENDING','PARTIAL_T09_RUNTIME_P3_INDEPENDENT_NEGATIVE_PENDING')) {
        Check ($audit.p4_current_bundle.knowledge_precheck -ceq 'PASS_REFERENCE_ONLY') 'new audit records precheck pass'
        Check (($audit.p4_current_bundle.t08.status -cin @('PASS_CURRENT_BUNDLE_T08_EXPECTED_ERROR','PASS_CURRENT_FINAL_BUNDLE_T08_EXPECTED_ERROR','PASS_CURRENT_FINAL2_BUNDLE_T08_EXPECTED_ERROR')) -or ($audit.p4_current_bundle.accepted_cases -contains 'T08')) 'new audit records T08 pass'
    } else {
        Check ($audit.p4_current_bundle.knowledge_precheck -ceq 'NOT_RUN_NEW_BUNDLE') 'new audit marks precheck not run'
        Check ($audit.p4_current_bundle.t08.status -ceq 'NOT_RUN_NEW_BUNDLE') 'new audit marks T08 not run'
    }
    Check ($audit.p5.issue_close -eq $false) 'new audit keeps issue open'
} else {
    $p4 = @($audit.requirements | Where-Object id -ceq 'P4')[0]
    $p5 = @($audit.requirements | Where-Object id -ceq 'P5')[0]
    Check ($p4.status -ceq 'PARTIAL_NEW_BUNDLE_PRECHECK_PASS') 'audit P4 records precheck pass only'
    Check (@($p4.evidence | Where-Object { $_ -like '*normal-chat-current-bundle-knowledge-precheck-20260911*' }).Count -eq 1) 'audit P4 references current precheck'
    Check (@($p5.evidence | Where-Object { $_ -like '*nonlive-all-suite-20260911c*' }).Count -eq 1) 'audit P5 references latest non-live suite'
}
if ($precheck.status -ceq 'NOT_RUN_NEW_BUNDLE') {
    Check ($precheck.bundle_sha256 -ceq $bundleHash) 'pending precheck binds current bundle'
    Check ($precheck.chat.sent -eq $false -and $precheck.chat.response_observed -eq $false) 'pending precheck has no send'
} else {
    Check ($precheck.status -ceq 'PASS_REFERENCE_ONLY') 'precheck is reference-only'
    Check ($precheck.chat.sent -eq $true -and $precheck.chat.response_observed -eq $true) 'precheck was sent and observed'
    $precheckBundle = if ($precheck.PSObject.Properties.Name -contains 'package') { [string]$precheck.package.bundle_sha256 } else { [string]$precheck.bundle_sha256 }
    Check ($precheckBundle -ceq $bundleHash) 'precheck binds current bundle'
    if ($precheck.PSObject.Properties.Name -contains 'response') {
        Check ($precheck.response.robin_blocks -eq 0 -and $precheck.checks.generated_robin -eq $false) 'precheck generated no Robin'
    } else {
        Check ($precheck.chat.response_contains_robin -eq $false) 'precheck generated no Robin'
    }
}
Check ($stageExpired.status -ceq 'STAGED_STATE_EXPIRED') 'expired stage is explicit'
Check ($null -eq $stageExpired.current_edge_observation.matching_t01_tab_id -and $stageExpired.current_edge_observation.matching_t01_tab_visible -eq $false) 'expired stage is not treated as current'
Check ($stageExpired.actions_taken.Count -eq 0) 'expired-stage observation made no UI actions'
$acceptance = [IO.File]::ReadAllText((Join-Path $repo 'catalog\generated\acceptance-t01-t10\README.md'), $utf8)
Check ($acceptance.Contains($bundleHash)) 'acceptance table contains current bundle hash'
$fullCase = 'T01' + [char]0x301c + 'T10'
Check ($acceptance.Contains($fullCase)) 'acceptance table retains full case scope'
Write-Output ('PASS: ' + $checks + ' Issue #5 current-status integrity checks; no Copilot/PAD actions.')
