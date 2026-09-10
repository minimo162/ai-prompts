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
$audit = Read-Json 'catalog\evidence\issue5-completion-audit-20260911.json'
$precheck = Read-Json 'catalog\generated\normal-chat-current-bundle-knowledge-precheck-20260911\result.json'
$stageExpired = Read-Json 'catalog\evidence\t01-current-bundle-stage-expired-20260911.json'
$bundleHash = Hash 'copilot\knowledge\PAD-Robin-Knowledge-Bundle.txt'
$instructionHash = Hash 'copilot\agent-instructions.txt'

Check ($bundleHash -ceq $coverage.current_package.knowledge_bundle_sha256) 'coverage bundle hash matches file'
Check ($instructionHash -ceq $coverage.current_package.instruction_sha256) 'coverage instruction hash matches file'
Check ($coverage.current_package.status -like '*knowledge_precheck_pass*' -and $coverage.current_package.status -like '*t01_t10_pending*') 'coverage keeps partial current status'
foreach ($field in @('knowledge_precheck','t01_prepared','t01_stage_current')) {
    $relative = $coverage.current_package.$field
    Check (-not [string]::IsNullOrWhiteSpace($relative)) ('coverage field exists: ' + $field)
    Check (Test-Path -LiteralPath (Join-Path $repo ('catalog\' + $relative)) -PathType Leaf) ('coverage path exists: ' + $field)
}
$p4 = @($audit.requirements | Where-Object id -ceq 'P4')[0]
$p5 = @($audit.requirements | Where-Object id -ceq 'P5')[0]
Check ($p4.status -ceq 'PARTIAL_NEW_BUNDLE_PRECHECK_PASS') 'audit P4 records precheck pass only'
Check (@($p4.evidence | Where-Object { $_ -like '*normal-chat-current-bundle-knowledge-precheck-20260911*' }).Count -eq 1) 'audit P4 references current precheck'
Check (@($p5.evidence | Where-Object { $_ -like '*nonlive-all-suite-20260911c*' }).Count -eq 1) 'audit P5 references latest non-live suite'
Check ($precheck.status -ceq 'PASS_REFERENCE_ONLY') 'precheck status is reference-only'
Check ($precheck.chat.sent -eq $true -and $precheck.chat.response_observed -eq $true) 'precheck was sent and observed'
Check ($precheck.package.bundle_sha256 -ceq $bundleHash) 'precheck binds current bundle'
Check ($precheck.response.robin_blocks -eq 0 -and $precheck.checks.generated_robin -eq $false) 'precheck generated no Robin'
Check ($stageExpired.status -ceq 'STAGED_STATE_EXPIRED') 'expired stage is explicit'
Check ($null -eq $stageExpired.current_edge_observation.matching_t01_tab_id -and $stageExpired.current_edge_observation.matching_t01_tab_visible -eq $false) 'expired stage is not treated as current'
Check ($stageExpired.actions_taken.Count -eq 0) 'expired-stage observation made no UI actions'
$acceptance = [IO.File]::ReadAllText((Join-Path $repo 'catalog\generated\acceptance-t01-t10\README.md'), $utf8)
Check ($acceptance.Contains($bundleHash)) 'acceptance table contains current bundle hash'
$fullCase = 'T01' + [char]0x301c + 'T10'
Check ($acceptance.Contains($fullCase)) 'acceptance table retains full case scope'
Write-Output ('PASS: ' + $checks + ' Issue #5 current-status integrity checks; no Copilot/PAD actions.')
