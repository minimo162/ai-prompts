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
$liveRead = Read-Json 'catalog/evidence/issue-live-read-20260914m.json'
foreach ($record in @($coverage, $index, $audit, $package)) {
    Check ($record.c_cell_value_read_supplement.evidence -eq 'catalog/evidence/c-cell-read-20260914v/acceptance.json') 'current aggregate points to C scalar proof'
    Check (@($record.c_cell_value_read_supplement.remaining_required).Count -eq 2) 'current aggregate retains two required gaps'
}
Check (@($audit.final_evidence_audit.required_gaps).Count -eq 2) 'completion audit has only T04 and T10 required gaps'

Check ($trace.schema_version -eq 1) 'trace schema version'
Check ($trace.status -eq 'PARTIAL_REQUIRED_TRACEABILITY_GAPS') 'trace remains partial'
Check ($trace.issue_scope.issue_state -eq 'OPEN') 'issue remains open'
Check ($trace.issue_scope.pr_31 -eq 'MERGED') 'PR #31 merge preserved'
Check ($trace.issue_scope.pr_32 -eq 'MERGED') 'PR #32 merge preserved'
Check ($trace.issue_scope.baseline_main -eq 'c52f954164eb75fcaa37116a44c7454bca3a5073') 'main commit preserved'
Check ($trace.issue_scope.current_main -eq '7cc2c18b2a7f521f770c47c48cbbf4715d228979') 'current main commit recorded'
Check ($trace.issue_scope.package_version -eq '20260913e') 'package version'
Check ($trace.issue_scope.instruction_sha256 -eq '6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c') 'instruction hash'
Check ($trace.issue_scope.bundle_sha256 -eq '79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12') 'bundle hash'
Check ($trace.issue_scope.manifest_sha256 -eq 'dc597d10bba19de00b1c32d161d5b8eb82d7503b2eea27b81e73456ad48f5008') 'manifest hash'
Check ($trace.method.raw_preservation -eq $true) 'raw preservation enabled'
Check ($trace.method.same_version_generation_resend -eq $false) 'no same-version resend'
Check ($trace.method.strict_t10_bytes -eq 'NOT_PROVEN') 'T10 strict remains not proven'
Check ($trace.live_issue_read -eq 'catalog/evidence/issue-live-read-20260914m.json') 'trace registers current live issue read'
Check (Test-Path -LiteralPath (FullPath $trace.live_issue_read) -PathType Leaf) 'current live issue read exists'
Check ($trace.method.classification_contract.required_evidence_gap -and $trace.method.classification_contract.optional_unconfirmed -and $trace.method.classification_contract.external_blocked) 'gap classification contract exists'
Check ($liveRead.issues.'5'.state -eq 'OPEN' -and $liveRead.issues.'27'.state -eq 'OPEN') 'live Issue #5/#27 remain open'
Check ($liveRead.pull_requests.'31'.state -eq 'MERGED' -and $liveRead.pull_requests.'31'.merge_commit -eq 'c52f954164eb75fcaa37116a44c7454bca3a5073') 'live PR #31 merge is preserved'
Check ($liveRead.pull_requests.'32'.state -eq 'MERGED' -and $liveRead.pull_requests.'32'.merge_commit -eq '7cc2c18b2a7f521f770c47c48cbbf4715d228979') 'live PR #32 merge is current'
Check ($liveRead.current_main.local_head -eq $trace.issue_scope.current_main -and $liveRead.current_main.origin_main -eq $trace.issue_scope.current_main -and $liveRead.current_main.synchronized -eq $true) 'live read binds synchronized current main'
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

$decisions = @($trace.requirement_decisions)
Check ($decisions.Count -eq 7) 'exactly one requirement decision per A-G category'
Check ((@($decisions | ForEach-Object { $_.category } | Sort-Object) -join ',') -eq 'A,B,C,D,E,F,G') 'requirement decisions cover A-G'
foreach ($decision in $decisions) {
    Check (-not [string]::IsNullOrWhiteSpace([string]$decision.required_status)) ('required status is explicit: ' + $decision.category)
    Check ($null -ne $decision.required_evidence_gaps -and $null -ne $decision.optional_unconfirmed -and $null -ne $decision.external_blocked) ('gap classes are explicit: ' + $decision.category)
    $requiredText = (@($decision.required_evidence_gaps | ForEach-Object { if ($_.id) { $_.id } else { $_ } }) -join ' | ')
    foreach ($optional in @($decision.optional_unconfirmed)) {
        Check (-not ($requiredText -like ('*' + [string]$optional + '*'))) ('optional boundary is not promoted to required: ' + $decision.category)
    }
}
$cDecision = @($decisions | Where-Object category -eq 'C')[0]
Check (@($cDecision.required_evidence_gaps).Count -eq 0 -and $cDecision.required_status -eq 'SATISFIED_MEASURED_SUBSET') 'required C is satisfied only by the measured supplement'
$cResolved = @($cDecision.resolved_requirements | Where-Object id -eq 'C-datatable-cell-value-read')
Check ($cResolved.Count -eq 1 -and $cResolved[0].evidence -eq 'catalog/evidence/c-cell-read-20260914v/acceptance.json') 'C resolution points to native cell-read evidence'
& (Join-Path $PSScriptRoot 'Test-CDataTableCellRead.ps1') -Root $Root
$eDecision = @($decisions | Where-Object category -eq 'E')[0]
Check (@($eDecision.required_evidence_gaps | Where-Object id -eq 'E-independent-t04-run1-artifact').Count -eq 1) 'required E Run1 artifact gap stays required'
Check (@($eDecision.external_blocked | Where-Object id -eq 'E-pad-designer-observation').Count -eq 1) 'E live Designer dependency stays externally blocked'
$fDecision = @($decisions | Where-Object category -eq 'F')[0]
Check (@($fDecision.required_evidence_gaps | Where-Object id -eq 'F-t10-strict-raw-bytes').Count -eq 1) 'required F T10 byte gap stays required'

Check ($coverage.final_a_g_trace -eq $tracePath.Replace('catalog/', '')) 'coverage registers A-G trace'
Check ($index.final_a_g_trace -eq $tracePath.Replace('catalog/', '')) 'index registers A-G trace'
Check ($audit.final_a_g_trace -eq $tracePath.Replace('catalog/', '')) 'completion audit registers A-G trace'
Check ($package.final_a_g_trace -eq $tracePath.Replace('catalog/', '')) 'current package registers A-G trace'
Check ($coverage.a_g_requirement_decisions -eq 'evidence/issue5-a-g-trace-20260914g.json#requirement_decisions' -and $index.a_g_requirement_decisions -eq $coverage.a_g_requirement_decisions) 'coverage/index register requirement decision section'
Check ($audit.a_g_requirement_decisions -eq $coverage.a_g_requirement_decisions -and $package.a_g_requirement_decisions -eq $coverage.a_g_requirement_decisions) 'audit/status register requirement decision section'
Check ($coverage.live_issue_read -eq 'evidence/issue-live-read-20260914m.json') 'coverage registers current live issue read'
Check ($index.live_issue_read -eq 'evidence/issue-live-read-20260914m.json') 'index registers current live issue read'
Check ($audit.live_issue_read -eq 'evidence/issue-live-read-20260914m.json') 'completion audit registers current live issue read'
Check ($package.live_issue_read -eq 'evidence/issue-live-read-20260914m.json') 'current package registers current live issue read'
Check ($package.current_main_commit -eq '7cc2c18b2a7f521f770c47c48cbbf4715d228979' -and $audit.current_main_commit -eq $package.current_main_commit) 'aggregate current main commit agrees'
foreach ($aggregate in @('catalog/coverage.json', 'catalog/index.json', 'catalog/evidence/current-package-status-20260913.json', 'catalog/evidence/issue5-completion-audit-20260913.json')) {
    $aggregateText = [IO.File]::ReadAllText((FullPath $aggregate), $utf8)
    Check ($aggregateText.Contains('evidence/t04-independent-current-pad-session-diagnostic-20260914s.json')) ('aggregate registers T04 session diagnostic: ' + $aggregate)
}
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
Check (Test-Path -LiteralPath (FullPath $t04.session_diagnostic) -PathType Leaf) 'T04 session diagnostic exists'
$sessionDiagnostic = Read-Json $t04.session_diagnostic
Check ($sessionDiagnostic.quser.session_id -eq 1 -and $sessionDiagnostic.quser.session_name -eq 'console' -and $sessionDiagnostic.quser.state -eq 'Active') 'T04 session diagnostic confirms active console session'
Check (@($sessionDiagnostic.target_processes_after_refresh | Where-Object { $_.pid -in @(25804,31664) -and $_.session_id -eq 1 -and $_.responding -eq $true -and $_.main_window_handle -eq 0 -and $_.main_window_title -eq '' }).Count -eq 2) 'T04 session diagnostic preserves both hidden PAD targets'
Check ($sessionDiagnostic.computer_system_query.status -eq 'ACCESS_DENIED' -and $sessionDiagnostic.computer_system_query.user_name -eq 'NOT_CAPTURED') 'T04 session diagnostic labels inaccessible computer-system query'
Check ($sessionDiagnostic.mutation_guard.read_only -eq $true -and $sessionDiagnostic.mutation_guard.process_kill_or_restart -eq $false -and $sessionDiagnostic.mutation_guard.flow_binding_or_run -eq $false) 'T04 session diagnostic remains read-only'
$latestWindow = Read-Json ($t04.latest_window_observation)
if ($latestWindow.computer_use_snapshot.PSObject.Properties.Name -contains 'apps') {
    Check (@($latestWindow.computer_use_snapshot.apps).Count -eq 0) 'T04 latest Computer Use native app list is empty'
} else {
    Check ($latestWindow.computer_use_snapshot.apps_count -eq 0 -and $latestWindow.computer_use_snapshot.native_app_binding -eq 'UNAVAILABLE') 'T04 latest diagnostic Computer Use native app list is empty'
}
if ($latestWindow.result -eq 'READ_ONLY_PAD_WINDOW_DIAGNOSTIC_CASE_A') {
    Check ($latestWindow.classification.case -eq 'A') 'T04 diagnostic classified as case A'
    Check ($latestWindow.top_level_window_counts.all -eq 0 -and $latestWindow.top_level_window_counts.visible -eq 0) 'T04 diagnostic found no top-level windows'
    Check ($latestWindow.foreground_window.hwnd -eq 0 -and $latestWindow.foreground_window.owner_pid -eq 0) 'T04 diagnostic found no foreground window'
    Check (@($latestWindow.session_comparison.unique_session_ids).Count -eq 1 -and $latestWindow.session_comparison.unique_session_ids[0] -eq 1) 'T04 diagnostic sessions are comparable and all session 1'
    Check (@($latestWindow.reopen_conditions).Count -eq 3 -and $latestWindow.reopen_conditions[1] -match 'nonzero HWND') 'T04 diagnostic keeps bounded reopen conditions'
    Check ($latestWindow.mutation_guard.process_refresh_only -eq $true -and $latestWindow.mutation_guard.process_kill_or_restart -eq $false -and $latestWindow.mutation_guard.flow_binding_or_run -eq $false) 'T04 diagnostic is read-only with no PAD mutation'
} elseif ($latestWindow.result -eq 'PAD_CLOSED_AND_RELAUNCHED_NEW_PROCESS') {
    Check ($latestWindow.close_and_relaunch.old_processes_after_close.Count -eq 0) 'T04 prior PAD processes are absent after explicit close'
    Check ($latestWindow.close_and_relaunch.new_process_recheck.new_pids_present -eq $true) 'T04 new PAD processes remain present after launch'
    Check ($latestWindow.close_and_relaunch.new_processes_initial[0].main_window_title -eq 'Power Automate') 'T04 new Console title was observed at launch'
    Check ($latestWindow.close_and_relaunch.new_processes_initial[0].main_window_handle -ne 0) 'T04 new Console nonzero HWND was observed at launch'
    Check ($latestWindow.flow_and_run_actions.paste_save_run_invoked -eq $false -and $latestWindow.flow_and_run_actions.third_run_started -eq $false) 'T04 close/relaunch did not invoke flow or run actions'
} elseif ($latestWindow.result -eq 'BLOCKED_CURRENT_PAD_WINDOW_UNOBSERVABLE_AFTER_RELAUNCH') {
    Check ($latestWindow.relaunch_reference -eq 'catalog/evidence/t04-independent-current-pad-window-observation-20260914n.json') 'T04 recheck links the explicit close/relaunch evidence'
    Check (@($latestWindow.process_snapshot | Where-Object {$_.pid -in @(25804,31664) -and $_.responding -eq $true}).Count -eq 2) 'T04 relaunched PAD processes remain responding'
    Check (@($latestWindow.process_snapshot | Where-Object {$_.main_window_handle -ne 0 -or $_.main_window_title -ne ''}).Count -eq 0) 'T04 recheck has no stable visible HWND/title'
    Check ($latestWindow.flow_and_run_actions.paste_save_run_invoked -eq $false -and $latestWindow.flow_and_run_actions.third_run_started -eq $false) 'T04 recheck did not invoke flow or run actions'
} elseif ($latestWindow.result -eq 'BLOCKED_CURRENT_PAD_UIA_ROOT_EMPTY_AFTER_RELAUNCH') {
    Check ($latestWindow.source_observation -eq 'catalog/evidence/t04-independent-current-pad-window-observation-20260914o.json') 'T04 UIA recheck links the prior Computer Use recheck'
    Check ($latestWindow.uia_snapshot.root_children_count_by_pid.'25804' -eq 0 -and $latestWindow.uia_snapshot.root_children_count_by_pid.'31664' -eq 0) 'T04 relaunched PAD processes have zero UIA root windows'
    Check (@($latestWindow.uia_snapshot.matching_top_level_windows).Count -eq 0) 'T04 UIA recheck has no matching top-level windows'
    Check (@($latestWindow.process_snapshot | Where-Object {$_.main_window_handle -ne 0 -or $_.main_window_title -ne ''}).Count -eq 0) 'T04 UIA recheck processes have no visible HWND/title'
    Check ($latestWindow.flow_and_run_actions.paste_save_run_invoked -eq $false -and $latestWindow.flow_and_run_actions.third_run_started -eq $false) 'T04 UIA recheck did not invoke flow or run actions'
} elseif ($latestWindow.result -eq 'BLOCKED_CURRENT_PAD_CUA_NO_NATIVE_APP_AFTER_REINIT') {
    Check ($latestWindow.computer_use_snapshot.runtime -eq 'reinitialized') 'T04 CUA runtime was reinitialized before recheck'
    Check (@($latestWindow.computer_use_snapshot.apps).Count -eq 0 -and $latestWindow.computer_use_snapshot.native_app_binding -eq 'UNAVAILABLE') 'T04 CUA remains without native app binding after reinit'
    Check (@($latestWindow.process_snapshot | Where-Object {$_.responding -eq $true -and $_.main_window_handle -eq 0 -and $_.main_window_title -eq ''}).Count -eq 2) 'T04 relaunched PAD processes remain hidden after CUA reinit'
    Check (@($latestWindow.source_observations).Count -eq 2) 'T04 CUA recheck retains prior UIA and CUA sources'
    Check ($latestWindow.flow_and_run_actions.paste_save_run_invoked -eq $false -and $latestWindow.flow_and_run_actions.third_run_started -eq $false) 'T04 CUA recheck did not invoke flow or run actions'
} elseif ($latestWindow.result -eq 'READ_ONLY_PAD_WINDOW_DIAGNOSTIC_CASE_B') {
    Check ($latestWindow.classification.case -eq 'B') 'T04 latest diagnostic classified as case B'
    Check ($latestWindow.top_level_window_counts.visible -gt 0) 'T04 case B has normal visible windows'
    $designerTarget = @($latestWindow.target_process_snapshot_after_refresh | Where-Object { $_.process -eq 'PAD.Designer' })[0]
    Check ($null -ne $designerTarget -and $designerTarget.main_window_handle -eq 0 -and $designerTarget.main_window_title -eq '') 'T04 case B Designer remains without stable HWND/title'
    $designerUia = @($latestWindow.uia_snapshot | Where-Object { $_.pid -eq $designerTarget.pid })[0]
    Check ($null -ne $designerUia -and $designerUia.root_children_count -eq 0) 'T04 case B Designer UIA root remains empty'
    Check ($latestWindow.mutation_guard.process_refresh_only -eq $true -and $latestWindow.mutation_guard.window_input_or_click -eq $false -and $latestWindow.mutation_guard.flow_binding_or_run -eq $false) 'T04 case B remains read-only'
} else {
    Check ($latestWindow.result -eq 'BLOCKED_CURRENT_PAD_WINDOW_UNOBSERVABLE_CUA_NO_NATIVE_APP_BINDING') 'T04 latest window result is blocked without native binding'
    Check (@($latestWindow.pad_process_snapshot | Where-Object {$_.main_window_handle -ne 0 -or $_.main_window_title -ne ''}).Count -eq 0) 'T04 latest PAD processes have no visible HWND/title'
    Check (@($latestWindow.launch_attempts | Where-Object {$_.method -eq 'registered_designer_protocol' -and $_.result -eq 'ACCESS_DENIED' -and $_.visible_window_created -eq $false}).Count -eq 1) 'T04 latest protocol launch was denied without visible window'
    Check ($latestWindow.launch_attempt.method -eq 'explorer_shell_apps_folder_console' -and $latestWindow.launch_attempt.visible_window_created -eq $false -and $latestWindow.launch_attempt.result -eq 'NO_NEW_VISIBLE_PAD_PROCESS') 'T04 latest explorer launch produced no visible PAD process'
    Check ($latestWindow.uia_snapshot.root_children_count -eq 0 -and @($latestWindow.uia_snapshot.matching_top_level_windows).Count -eq 0) 'T04 latest UIA has no top-level window'
}

Check ($trace.decision.a_to_g_complete -eq $false) 'A-G complete flag remains false'
Check ($trace.decision.issue_close_authorized -eq $false) 'issue close remains unauthorized'
Check ($trace.decision.pr_ready -eq $false) 'PR readiness remains false'

Write-Output ('PASS: ' + $checks + ' Issue #5 A-G trace checks; partial/open, T04 Run1 NOT_CAPTURED, and T10 strict NOT_PROVEN preserved.')
