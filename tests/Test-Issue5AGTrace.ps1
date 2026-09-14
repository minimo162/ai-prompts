[CmdletBinding()]
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$utf8 = [Text.Encoding]::UTF8
$checks = 0

function Check([bool]$Value, [string]$Name) {
    if (-not $Value) { throw ('FAIL: ' + $Name) }
    $script:checks++
}

function FullPath([string]$RelativePath) {
    return [IO.Path]::GetFullPath((Join-Path $Root ($RelativePath.Replace('/', '\'))))
}

function Read-Json([string]$RelativePath) {
    $path = FullPath $RelativePath
    Check (Test-Path -LiteralPath $path -PathType Leaf) ('file exists: ' + $RelativePath)
    return ([IO.File]::ReadAllText($path, $utf8) | ConvertFrom-Json)
}

$tracePath = 'catalog/evidence/issue5-a-g-trace-20260914g.json'
$trace = Read-Json $tracePath
$coverage = Read-Json 'catalog/coverage.json'
$index = Read-Json 'catalog/index.json'
$audit = Read-Json 'catalog/evidence/issue5-completion-audit-20260913.json'
$package = Read-Json 'catalog/evidence/current-package-status-20260913.json'
$liveRead = Read-Json 'catalog/evidence/issue-live-read-20260914l.json'

Check ($trace.schema_version -eq 1) 'trace schema version'
Check ($trace.status -eq 'PARTIAL_REQUIRED_TRACEABILITY_GAPS') 'trace remains partial'
Check ($trace.issue_scope.issue_state -eq 'OPEN') 'issue remains open'
Check ($trace.issue_scope.pr_31 -eq 'MERGED') 'PR #31 merge preserved'
Check ($trace.issue_scope.baseline_main -eq 'c52f954164eb75fcaa37116a44c7454bca3a5073') 'main commit preserved'
Check ($trace.issue_scope.package_version -eq '20260913e') 'package version'
Check ($trace.issue_scope.instruction_sha256 -eq '6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c') 'instruction hash'
Check ($trace.issue_scope.bundle_sha256 -eq '79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12') 'bundle hash'
Check ($trace.issue_scope.manifest_sha256 -eq 'dc597d10bba19de00b1c32d161d5b8eb82d7503b2eea27b81e73456ad48f5008') 'manifest hash'
Check ($trace.method.raw_preservation -eq $true) 'raw preservation enabled'
Check ($trace.method.same_version_generation_resend -eq $false) 'no same-version resend'
Check ($trace.method.strict_t10_bytes -eq 'NOT_PROVEN') 'T10 strict remains not proven'
Check ($trace.live_issue_read -eq 'catalog/evidence/issue-live-read-20260914l.json') 'trace registers live issue read'
Check ($liveRead.issues.'5'.state -eq 'OPEN' -and $liveRead.issues.'27'.state -eq 'OPEN') 'live Issue #5/#27 remain open'
Check ($liveRead.pull_requests.'31'.state -eq 'MERGED' -and $liveRead.pull_requests.'31'.merge_commit -eq 'c52f954164eb75fcaa37116a44c7454bca3a5073') 'live PR #31 merge is preserved'
Check ($liveRead.write_actions.issue_comments_posted -eq $false -and $liveRead.write_actions.issue_bodies_changed -eq $false -and $liveRead.write_actions.push_performed -eq $false) 'live read performed without external writes'

$categoryNames = @($trace.categories.PSObject.Properties.Name | Sort-Object)
Check (($categoryNames -join ',') -eq 'A,B,C,D,E,F,G') 'exact A-G category set'
foreach ($categoryProperty in $trace.categories.PSObject.Properties) {
    $category = $categoryProperty.Value
    Check (-not [string]::IsNullOrWhiteSpace([string]$category.title)) ($categoryProperty.Name + ' title')
    Check ($category.status -notmatch '^(PASS|COMPLETE|ACCEPTED_ALL)$') ($categoryProperty.Name + ' does not claim full acceptance')
    Check (@($category.knowledge_sources).Count -gt 0) ($categoryProperty.Name + ' knowledge source')
    Check (@($category.checks).Count -gt 0) ($categoryProperty.Name + ' checks')
    Check (@($category.gaps).Count -gt 0) ($categoryProperty.Name + ' explicit gaps')
    foreach ($source in @($category.knowledge_sources)) {
        Check (Test-Path -LiteralPath (FullPath $source) -PathType Leaf) ($categoryProperty.Name + ' knowledge exists: ' + $source)
    }
    foreach ($checkItem in @($category.checks)) {
        Check (-not [string]::IsNullOrWhiteSpace([string]$checkItem.id)) ($categoryProperty.Name + ' check id')
        Check ($checkItem.status -notmatch '^(PASS|COMPLETE|ACCEPTED_ALL)$') ($checkItem.id + ' does not claim full acceptance')
        Check (@($checkItem.evidence).Count -gt 0) ($checkItem.id + ' evidence links')
        foreach ($evidence in @($checkItem.evidence)) {
            Check (Test-Path -LiteralPath (FullPath $evidence) -PathType Leaf) ($checkItem.id + ' evidence exists: ' + $evidence)
        }
    }
}

Check ($coverage.final_a_g_trace -eq $tracePath.Replace('catalog/', '')) 'coverage registers A-G trace'
Check ($index.final_a_g_trace -eq $tracePath.Replace('catalog/', '')) 'index registers A-G trace'
Check ($audit.final_a_g_trace -eq $tracePath.Replace('catalog/', '')) 'completion audit registers A-G trace'
Check ($package.final_a_g_trace -eq $tracePath.Replace('catalog/', '')) 'current package registers A-G trace'
Check ($audit.final_evidence_audit.status -eq 'PARTIAL_REQUIRED_TRACEABILITY_GAPS') 'completion audit remains partial'
Check (@($audit.final_evidence_audit.required_gaps).Count -gt 0) 'completion audit keeps required gaps'

$t04 = $trace.current_t04_trace
Check ($t04.status -eq 'CANDIDATE_PARTIAL_PRESERVED') 'T04 candidate status preserved'
Check ($t04.robin_sha256 -eq 'dd4f39f0700cfb5a9275dfc9912c89bd8d886d72972c9eb74223acf30343569d') 'T04 Robin hash preserved'
Check ($t04.run1_output -eq 'NOT_CAPTURED') 'T04 Run1 remains not captured'
Check ($t04.run2_values -eq 'VERIFIED') 'T04 Run2 values verified'
Check ($t04.new_pair -eq 'NOT_STARTED_CURRENT_PAD_DESIGNER_WINDOW_UNOBSERVABLE_CUA_NO_NATIVE_APP_BINDING') 'T04 new pair not started while window unobservable'
$t04Comparison = Read-Json ($t04.comparison)
Check ($t04Comparison.status -eq 'PASS_CURRENT_20260914E_INDEPENDENT_T04_GENERATION_PAD_TWO_RUNS_PARTIAL') 'T04 comparison remains partial'
Check ($t04Comparison.generation.dom_code.sha256 -eq $t04.robin_sha256) 'T04 Robin hash agrees with comparison'
Check ($t04Comparison.execution.run1.output_snapshot -eq 'NOT_CAPTURED') 'T04 comparison preserves Run1 not captured'
Check (Test-Path -LiteralPath (FullPath $t04.comparison) -PathType Leaf) 'T04 comparison evidence exists'
Check (Test-Path -LiteralPath (FullPath $t04.reconciliation) -PathType Leaf) 'T04 reconciliation evidence exists'
Check (Test-Path -LiteralPath (FullPath $t04.window_observation) -PathType Leaf) 'T04 window observation exists'
Check (Test-Path -LiteralPath (FullPath $t04.latest_window_observation) -PathType Leaf) 'T04 latest window observation exists'
$latestWindow = Read-Json ($t04.latest_window_observation)
Check ($latestWindow.result -eq 'BLOCKED_CURRENT_PAD_WINDOW_UNOBSERVABLE_CUA_NO_NATIVE_APP_BINDING') 'T04 latest window result is blocked without native binding'
Check (@($latestWindow.computer_use_snapshot.apps).Count -eq 0) 'T04 latest Computer Use native app list is empty'
Check (@($latestWindow.pad_process_snapshot | Where-Object {$_.main_window_handle -ne 0 -or $_.main_window_title -ne ''}).Count -eq 0) 'T04 latest PAD processes have no visible HWND/title'
Check (@($latestWindow.launch_attempts | Where-Object {$_.method -eq 'registered_designer_protocol' -and $_.result -eq 'ACCESS_DENIED' -and $_.visible_window_created -eq $false}).Count -eq 1) 'T04 latest protocol launch was denied without visible window'
Check ($latestWindow.launch_attempt.method -eq 'explorer_shell_apps_folder_console' -and $latestWindow.launch_attempt.visible_window_created -eq $false -and $latestWindow.launch_attempt.result -eq 'NO_NEW_VISIBLE_PAD_PROCESS') 'T04 latest explorer launch produced no visible PAD process'

Check ($trace.decision.a_to_g_complete -eq $false) 'A-G complete flag remains false'
Check ($trace.decision.issue_close_authorized -eq $false) 'issue close remains unauthorized'
Check ($trace.decision.pr_ready -eq $false) 'PR readiness remains false'

Write-Output ('PASS: ' + $checks + ' Issue #5 A-G trace checks; partial/open, T04 Run1 NOT_CAPTURED, and T10 strict NOT_PROVEN preserved.')
