[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$utf8 = [Text.Encoding]::UTF8
$checks = 0
function Check([bool]$Value, [string]$Name) { if (-not $Value) { throw ('FAIL: ' + $Name) }; $script:checks++ }
function Read-Json([string]$RelativePath) { return ([IO.File]::ReadAllText((Join-Path $repo $RelativePath), $utf8) | ConvertFrom-Json) }
function Read-JsonAbs([string]$Path) { return ([IO.File]::ReadAllText($Path, $utf8) | ConvertFrom-Json) }
function Hash([string]$RelativePath) { return (Get-FileHash -LiteralPath (Join-Path $repo $RelativePath) -Algorithm SHA256).Hash.ToLowerInvariant() }
function Resolve-CatalogRef([string]$Relative) { return [IO.Path]::GetFullPath((Join-Path (Join-Path $repo 'catalog') $Relative.Replace('/', '\'))) }

function Resolve-EvidenceRef([string]$EvidenceRoot, [string]$Ref) {
    $direct = [IO.Path]::GetFullPath((Join-Path $EvidenceRoot $Ref.Replace('/', '\')))
    if (Test-Path -LiteralPath $direct -PathType Leaf) { return $direct }
    return [IO.Path]::GetFullPath((Join-Path (Join-Path $EvidenceRoot 'evidence') $Ref.Replace('/', '\')))
}

# Semantic audit check (schema 2). Returns nothing; throws on the first inconsistency.
# $Audit: parsed audit object. $BundleHash: hash the audit must bind to. $EvidenceRoot: folder used to resolve evidence
# references (the real catalog folder, or a fixture folder). Evidence files are read to verify their own binding and runs.
function Test-Issue5AuditSemantics($Audit, [string]$BundleHash, [string]$EvidenceRoot) {
    if ($Audit.schema_version -ne 2) { throw 'AUDIT_SCHEMA: expected schema_version 2' }
    if ($Audit.package.bundle_sha256 -cne $BundleHash) { throw 'AUDIT_BUNDLE: audit does not bind the current bundle' }
    if ($Audit.p5.issue_close -ne $false) { throw 'AUDIT_ISSUE: audit must keep the issue open' }
    $required = @('knowledge_precheck','T01','T02','T03','T04','T05','T06','T07','T08','T09','T10')
    $results = $Audit.p4_current_bundle.case_results
    $allPass = $true
    foreach ($case in $required) {
        $entry = $results.$case
        if ($null -eq $entry) { throw ('AUDIT_CASE: missing case result ' + $case) }
        $status = [string]$entry.status
        if ([string]::IsNullOrWhiteSpace($status)) { throw ('AUDIT_CASE: empty status ' + $case) }
        if ($status -like 'NOT_RUN*') { $allPass = $false }
        $evidencePath = Resolve-EvidenceRef $EvidenceRoot ([string]$entry.evidence)
        if (-not (Test-Path -LiteralPath $evidencePath -PathType Leaf)) { throw ('AUDIT_EVIDENCE: missing evidence file for ' + $case + ': ' + $entry.evidence) }
        if ($status -like 'PASS*') {
            $ev = Read-JsonAbs $evidencePath
            $evBundle = if ($ev.PSObject.Properties.Name -contains 'bundle_sha256') { [string]$ev.bundle_sha256 } else { [string]$ev.package.bundle_sha256 }
            if ($evBundle -cne $BundleHash) { throw ('AUDIT_EVIDENCE_BUNDLE: ' + $case + ' evidence is bound to a different bundle') }
            if (-not ([string]$ev.status -like 'PASS*')) { throw ('AUDIT_EVIDENCE_STATUS: ' + $case + ' claimed PASS but evidence status is ' + $ev.status) }
            if ($case -ne 'knowledge_precheck') {
                $robin = $ev.generated_robin
                if ($null -eq $robin -or [int]$robin.code_blocks -lt 1 -or $robin.raw_unmodified -ne $true) { throw ('AUDIT_EVIDENCE_ROBIN: ' + $case + ' PASS requires an unmodified generated Robin block') }
                $pad = $ev.pad
                if ($null -eq $pad -or [string]::IsNullOrWhiteSpace([string]$pad.run1) -or [string]::IsNullOrWhiteSpace([string]$pad.run2)) { throw ('AUDIT_EVIDENCE_RUNS: ' + $case + ' PASS requires two recorded PAD runs') }
                foreach ($runRef in @([string]$pad.run1, [string]$pad.run2)) {
                    $runPath = [IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $evidencePath) $runRef.Replace('/', '\')))
                    if (-not (Test-Path -LiteralPath $runPath -PathType Leaf)) { $runPath = [IO.Path]::GetFullPath((Join-Path $EvidenceRoot $runRef.Replace('../','').Replace('/', '\'))) }
                    if (-not (Test-Path -LiteralPath $runPath -PathType Leaf)) { throw ('AUDIT_EVIDENCE_RUNS: ' + $case + ' run record missing: ' + $runRef) }
                    $run = Read-JsonAbs $runPath
                    if ([string]$run.run_status -cne 'success') { throw ('AUDIT_EVIDENCE_RUNS: ' + $case + ' run record is not success: ' + $runRef) }
                }
            } else {
                if ([int]$ev.response.robin_blocks -ne 0) { throw 'AUDIT_PRECHECK: precheck must not generate Robin' }
            }
        } else { $allPass = $false }
    }
    foreach ($case in @('T01','T04','T10')) {
        $ref = [string]$Audit.p4_current_bundle.independent_retests.results.$case
        if ([string]::IsNullOrWhiteSpace($ref)) { throw ('AUDIT_INDEPENDENT: missing independent retest reference for ' + $case) }
        $path = Resolve-EvidenceRef $EvidenceRoot $ref
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw ('AUDIT_INDEPENDENT: missing independent evidence ' + $ref) }
        $ev = Read-JsonAbs $path
        if ($ev.independent_retest -ne $true -or [string]$ev.bundle_sha256 -cne $BundleHash -or -not ([string]$ev.status -like 'PASS*')) { throw ('AUDIT_INDEPENDENT: ' + $case + ' independent evidence is not a same-version PASS') }
    }
    $negRef = [string]$Audit.p4_current_bundle.negative_suite.evidence
    $negPath = Resolve-EvidenceRef $EvidenceRoot $negRef
    if (-not (Test-Path -LiteralPath $negPath -PathType Leaf)) { throw 'AUDIT_NEGATIVE: negative suite evidence missing' }
    $neg = Read-JsonAbs $negPath
    if ([string]$neg.bundle_sha256 -cne $BundleHash -or [int]$neg.response.pre_elements -ne 0 -or -not ([string]$neg.status -like 'PASS_NEGATIVE*')) { throw 'AUDIT_NEGATIVE: negative suite must be a same-version fail-closed pass' }
    $claimsComplete = ([string]$Audit.status -like 'complete*') -or ([string]$Audit.p4_current_bundle.status -like 'COMPLETE*')
    if ($claimsComplete -and -not $allPass) { throw 'AUDIT_OVERALL: overall completion claimed while a required case is not PASS' }
    if (-not $claimsComplete -and -not ([string]$Audit.status -like 'partial*')) { throw 'AUDIT_OVERALL: non-complete audit must be partial' }
}

$coverage = Read-Json 'catalog\coverage.json'
$auditRelative = [string]$coverage.current_package.audit
$audit = Read-Json ('catalog\' + $auditRelative.Replace('/','\'))
$precheckRelative = [string]$coverage.current_package.knowledge_precheck
$precheck = Read-Json ('catalog\' + $precheckRelative.Replace('/','\'))
$stageExpired = Read-Json 'catalog\evidence\t01-current-bundle-stage-expired-20260911.json'
$bundleHash = Hash 'copilot\knowledge\PAD-Robin-Knowledge-Bundle.txt'
$instructionHash = Hash 'copilot\agent-instructions.txt'

Check ($bundleHash -ceq $coverage.current_package.knowledge_bundle_sha256) 'coverage bundle hash matches file'
Check ($instructionHash -ceq $coverage.current_package.instruction_sha256) 'coverage instruction hash matches file'
foreach ($field in @('knowledge_precheck','t01_prepared','t01_stage_current','evidence','static_check')) {
    $relative = $coverage.current_package.$field
    Check (-not [string]::IsNullOrWhiteSpace($relative)) ('coverage field exists: ' + $field)
    Check (Test-Path -LiteralPath (Join-Path $repo ('catalog\' + $relative)) -PathType Leaf) ('coverage path exists: ' + $field)
}
$statusRecord = Read-Json ('catalog\' + ([string]$coverage.current_package.evidence).Replace('/','\'))
Check ($statusRecord.version.knowledge_bundle_sha256 -ceq $bundleHash) 'status record binds current bundle'
Check ($statusRecord.status -ceq $coverage.current_package.status) 'coverage status equals status record'
Check ($statusRecord.issue_state -ceq 'OPEN') 'status record keeps issue open'

Test-Issue5AuditSemantics $audit $bundleHash (Join-Path $repo 'catalog')
$checks += 1
Check ($audit.package.instruction_sha256 -ceq $instructionHash) 'audit binds current instruction'
Check (($audit.status -like 'partial*') -or ($audit.status -like 'complete*')) 'audit status is partial or complete'
if ($audit.status -like 'complete*') { Check ($statusRecord.status -like 'complete*') 'status record agrees with complete audit' } else { Check ($statusRecord.status -like 'partial*') 'status record agrees with partial audit' }

Check ($precheck.status -ceq 'PASS_REFERENCE_ONLY') 'precheck is reference-only'
Check ($precheck.chat.sent -eq $true -and $precheck.chat.response_observed -eq $true) 'precheck was sent and observed'
Check ($precheck.chat.full_instruction_in_body -eq $true) 'precheck used the full instruction body'
Check ([string]$precheck.package.bundle_sha256 -ceq $bundleHash) 'precheck binds current bundle'
Check ($precheck.response.robin_blocks -eq 0 -and $precheck.checks.generated_robin -eq $false) 'precheck generated no Robin'

Check ($stageExpired.status -ceq 'STAGED_STATE_EXPIRED') 'expired stage is explicit'
Check ($null -eq $stageExpired.current_edge_observation.matching_t01_tab_id -and $stageExpired.current_edge_observation.matching_t01_tab_visible -eq $false) 'expired stage is not treated as current'
Check ($stageExpired.actions_taken.Count -eq 0) 'expired-stage observation made no UI actions'

$acceptance = [IO.File]::ReadAllText((Join-Path $repo 'catalog\generated\acceptance-t01-t10\README.md'), $utf8)
$firstBundleLike = [regex]::Matches($acceptance, '[0-9a-f]{64}') | Where-Object { $_.Value -cne $instructionHash } | Select-Object -First 1
Check ($acceptance.Contains($bundleHash)) 'acceptance table contains current bundle hash'
Check ($null -ne $firstBundleLike -and $firstBundleLike.Value -ceq $bundleHash) 'acceptance README names the current bundle before any historical bundle hash'
$fullCase = 'T01' + [char]0x301c + 'T10'
Check ($acceptance.Contains($fullCase)) 'acceptance table retains full case scope'

# Negative fixtures: each must be rejected by the semantic audit check with the expected error prefix.
$fixtureRoot = Join-Path $PSScriptRoot 'fixtures\issue5'
$manifest = Read-JsonAbs (Join-Path $fixtureRoot 'negative-fixtures.json')
foreach ($fx in $manifest.fixtures) {
    $fxAudit = Read-JsonAbs (Join-Path $fixtureRoot ([string]$fx.audit))
    $fxRoot = Join-Path $fixtureRoot ([string]$fx.evidence_root)
    $message = ''
    try { Test-Issue5AuditSemantics $fxAudit ([string]$fx.bundle_sha256) $fxRoot } catch { $message = $_.Exception.Message }
    Check ($message -like ([string]$fx.expected_error_prefix + '*')) ('negative fixture rejected: ' + $fx.name + ' (' + $message + ')')
}
Write-Output ('PASS: ' + $checks + ' Issue #5 current-status integrity checks; no Copilot/PAD actions.')
