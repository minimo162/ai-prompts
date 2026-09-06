[CmdletBinding()]
param(
    [string]$SourcePath='',
    [string]$EvidencePath=''
)
$ErrorActionPreference='Stop'
if(-not $SourcePath){$SourcePath=Join-Path $PSScriptRoot '..\App.ps1'}
$env:PSModulePath=Join-Path $PSHOME 'Modules'
$taskApp='';$taskAppHash='';$taskAfterHash='';$taskEvidenceFile='';$taskFailureRecord=$null;$taskSourceFunctionCount=0
$taskTestPath=$PSCommandPath;$taskTestHash=(Get-FileHash -LiteralPath $taskTestPath).Hash.ToLowerInvariant()
$taskPassed=New-Object 'Collections.Generic.List[string]'
$taskReport=[ordered]@{kind='copilot_planner_v2_parser_tests';status='failed';engine='native Windows PowerShell 5.1 x64 STA';source_path='';source_sha256_before='';source_sha256_after='';source_unchanged=$null;test_sha256=$taskTestHash;test_unchanged=$null;test_count=0;tests=@();source_function_definitions_loaded=0;empty_line_wire='exact AGENT_EMPTY_V2 request_id only';raw_empty_body_rows_rejected=$true;lone_nbsp_body_rows_rejected=$true;provider_calls=0;browser_calls=0;pad_calls=0;authority_created=$false;failure=$null;started_utc=[DateTime]::UtcNow.ToString('o')}
try {
    if($EvidencePath){$taskEvidenceFile=[IO.Path]::GetFullPath($EvidencePath)}
    $taskApp=[IO.Path]::GetFullPath($SourcePath);$taskReport.source_path=$taskApp
    if($taskEvidenceFile -and ($taskEvidenceFile -ieq $taskApp -or $taskEvidenceFile -ieq $taskTestPath)){throw 'TEST_EVIDENCE: Evidence must not replace a source or test file.'}
    if($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1 -or -not [Environment]::Is64BitProcess -or [Threading.Thread]::CurrentThread.ApartmentState -ne 'STA'){throw 'TEST_ENGINE: Native PS5.1 x64 STA required.'}
    $taskAppHash=(Get-FileHash -LiteralPath $taskApp).Hash.ToLowerInvariant();$taskReport.source_sha256_before=$taskAppHash
    $taskTokens=$null;$taskErrors=$null;$taskAppAst=[Management.Automation.Language.Parser]::ParseFile($taskApp,[ref]$taskTokens,[ref]$taskErrors)
    if($taskErrors.Count){throw 'TEST_PARSE: Source syntax is invalid.'}
    # Load every function definition from the actual source AST. Never execute
    # source top-level statements, import a fragment, or establish a runtime Home.
    $taskDefinitions=@($taskAppAst.FindAll({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst]},$true))
    $taskNames=New-Object 'Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach($taskDefinition in $taskDefinitions){
        if(-not $taskNames.Add($taskDefinition.Name)){throw 'TEST_SOURCE: Function definitions must have unique names.'}
        . ([scriptblock]::Create($taskDefinition.Extent.Text))
    }
    $taskSourceFunctionCount=$taskDefinitions.Count
    $taskParsers=@($taskDefinitions|Where-Object Name -ceq 'ConvertFrom-AgentCopilotPlannerV2')
    if($taskParsers.Count -ne 1){throw 'TEST_SOURCE: Actual source must define exactly one Planner V2 parser.'}
    $taskAst=$taskParsers[0]
$taskPassed=New-Object 'Collections.Generic.List[string]';$taskId='00000000000000000000000000000051';$taskOtherId='00000000000000000000000000000052'
function New-TestMeta([string]$State='ACT',[object]$Message='ok') { return (ConvertTo-Json -InputObject ([ordered]@{request_id=$taskId;state=$State;message=$Message;artifacts=@()}) -Depth 100 -Compress) }
function New-TestFrames([string]$Metadata,[object[]]$BodyRows=@('WAIT 0'),[string]$Id=$taskId) {
 $meta='AGENT_META_V2 '+$Id+"`n"+$Metadata+"`nAGENT_META_END_V2 "+$Id
 $rows=@('AGENT_ROBIN_V2 '+$Id)+@($BodyRows)+@(('AGENT_ROBIN_END_V2 '+$Id),('AGENT_END_'+$Id))
 return ,@($meta,($rows -join "`n"))
}
function Assert-Accepted([string]$Name,[object[]]$Frames,[string]$ExpectedRobin,[string]$Id=$taskId) {
 $json=ConvertFrom-AgentCopilotPlannerV2 -Frames $Frames -RequestId $Id
 if($json -isnot [string] -or $json.Length -gt 1048576){throw ('TEST_OUTPUT: '+$Name)}
 $plan=Get-AgentPlannerResponse $json $Id
 if($plan.robin -cne $ExpectedRobin){throw ('TEST_CONTENT: '+$Name)}
 $taskPassed.Add($Name)
 return $plan
}
function Assert-Rejected([string]$Name,[scriptblock]$Action){try{$null=& $Action}catch{if($_.Exception.Message -notlike 'RESPONSE_INVALID:*'){throw};$taskPassed.Add($Name);return};throw ('TEST_ACCEPTED_INVALID: '+$Name)}
$taskMeta=New-TestMeta
$null=Assert-Accepted 'act_minimal' (New-TestFrames $taskMeta) 'WAIT 0'
foreach($taskState in @('DONE','ASK_USER','BLOCKED')){
 $taskStateMeta=New-TestMeta $taskState
 $null=Assert-Accepted ('nonact_zero_rows_'+$taskState) (New-TestFrames $taskStateMeta @()) ''
 Assert-Rejected ('nonact_raw_blank_'+$taskState) {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskStateMeta @('')) $taskId}
 Assert-Rejected ('nonact_empty_sentinel_'+$taskState) {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskStateMeta @('AGENT_EMPTY_V2 '+$taskId)) $taskId}
 Assert-Rejected ('nonact_nonempty_body_'+$taskState) {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskStateMeta @('WAIT 0')) $taskId}
}
$taskPretty=([pscustomobject](ConvertFrom-Json $taskMeta)|ConvertTo-Json -Depth 8).Replace("`r`n","`n")
$null=Assert-Accepted 'metadata_multiple_physical_rows' (New-TestFrames $taskPretty) 'WAIT 0'
$taskSpecial='  日本語 e'+[char]0x0301+' '+[char]0x00E9+' "quote" C:\path\ %FileContents% '+[char]9+'  '
$null=Assert-Accepted 'ordinary_whitespace_quotes_backslashes_percent_unicode_exact' (New-TestFrames $taskMeta @($taskSpecial)) $taskSpecial
$taskEmpty='AGENT_EMPTY_V2 '+$taskId
foreach($taskCase in @(
 [pscustomobject]@{name='leading_empty_sentinel';wire=@($taskEmpty,'WAIT 0');raw="`nWAIT 0"},
 [pscustomobject]@{name='trailing_empty_sentinel';wire=@('WAIT 0',$taskEmpty);raw="WAIT 0`n"},
 [pscustomobject]@{name='consecutive_empty_sentinels';wire=@('WAIT 0',$taskEmpty,$taskEmpty,'WAIT 1');raw="WAIT 0`n`n`nWAIT 1"},
 [pscustomobject]@{name='leading_and_trailing_empty_sentinels';wire=@($taskEmpty,'WAIT 0',$taskEmpty);raw="`nWAIT 0`n"}
)){$null=Assert-Accepted $taskCase.name (New-TestFrames $taskMeta $taskCase.wire) $taskCase.raw}
Assert-Rejected 'act_zero_body' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta @()) $taskId}
Assert-Rejected 'act_raw_empty_body' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta @('')) $taskId}
Assert-Rejected 'act_one_sentinel_only' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta @($taskEmpty)) $taskId}
Assert-Rejected 'act_two_sentinels_only' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta @($taskEmpty,$taskEmpty)) $taskId}
Assert-Rejected 'raw_empty_between_actions' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta @('WAIT 0','','WAIT 1')) $taskId}
Assert-Rejected 'empty_marker_wrong_nonce' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta @('WAIT 0',('AGENT_EMPTY_V2 '+$taskOtherId))) $taskId}
Assert-Rejected 'empty_marker_missing_nonce' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta @('WAIT 0','AGENT_EMPTY_V2')) $taskId}
Assert-Rejected 'empty_marker_extra_text' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta @('WAIT 0',($taskEmpty+' extra'))) $taskId}
$taskNbsp=[string][char]160
Assert-Rejected 'lone_nbsp_body_row_rejected_not_normalized' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta @('WAIT 0',$taskNbsp,'WAIT 1')) $taskId}
$taskNbspText='SET Value TO '+(ConvertTo-AgentRobinLiteral ('a'+$taskNbsp+'b'))
$null=Assert-Accepted 'nbsp_inside_normal_literal_preserved' (New-TestFrames $taskMeta @($taskNbspText)) $taskNbspText
$null=Assert-Accepted 'ordinary_space_row_not_normalized' (New-TestFrames $taskMeta @('WAIT 0',' ','WAIT 1')) "WAIT 0`n `nWAIT 1"
$taskQuotedMarker='SET Value TO '+(ConvertTo-AgentRobinLiteral ('AGENT_EMPTY_V2 '+$taskOtherId+' AGENT_AICALL_FAILED'))
$null=Assert-Accepted 'marker_text_inside_robin_literal_is_not_protocol' (New-TestFrames $taskMeta @($taskQuotedMarker)) $taskQuotedMarker
foreach($taskMarker in @('AGENT_META_V2 ','AGENT_META_END_V2 ','AGENT_ROBIN_V2 ','AGENT_ROBIN_END_V2 ','AGENT_END_')){Assert-Rejected ('reserved_'+$taskMarker.Trim()) {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta @('WAIT 0',($taskMarker+$taskOtherId))) $taskId}}
foreach($taskBadMeta in @(
 [pscustomobject]@{name='unknown_robin_metadata';text=$taskMeta.TrimEnd('}')+',"robin":"WAIT 1"}'},
 [pscustomobject]@{name='unknown_metadata_property';text=$taskMeta.TrimEnd('}')+',"other":true}'},
 [pscustomobject]@{name='duplicate_request_id';text=$taskMeta.Replace('"state":"ACT"','"request_id":"'+$taskId+'","state":"ACT"')},
 [pscustomobject]@{name='case_duplicate_request_id';text=$taskMeta.Replace('"state":"ACT"','"REQUEST_ID":"'+$taskId+'","state":"ACT"')},
 [pscustomobject]@{name='case_wrong_request_key';text=$taskMeta.Replace('"request_id":','"REQUEST_ID":')},
 [pscustomobject]@{name='wrong_request_value';text=$taskMeta.Replace($taskId,$taskOtherId)},
 [pscustomobject]@{name='false_state';text=$taskMeta.Replace('"state":"ACT"','"state":false')},
 [pscustomobject]@{name='lowercase_state';text=$taskMeta.Replace('"state":"ACT"','"state":"act"')},
 [pscustomobject]@{name='state_array';text=$taskMeta.Replace('"state":"ACT"','"state":["ACT"]')},
 [pscustomobject]@{name='nonstring_message';text=$taskMeta.Replace('"message":"ok"','"message":7')},
 [pscustomobject]@{name='whitespace_message';text=$taskMeta.Replace('"message":"ok"','"message":" "')},
 [pscustomobject]@{name='nonarray_artifacts';text=$taskMeta.Replace('"artifacts":[]','"artifacts":"x"')},
 [pscustomobject]@{name='nonstring_artifact';text=$taskMeta.Replace('"artifacts":[]','"artifacts":[7]')},
 [pscustomobject]@{name='trailing_comma';text=$taskMeta.Replace('"artifacts":[]','"artifacts":[],')},
 [pscustomobject]@{name='json_comment';text=$taskMeta.Replace('"state":"ACT"','/*x*/"state":"ACT"')},
 [pscustomobject]@{name='trailing_json';text=$taskMeta+'{}'},
 [pscustomobject]@{name='null_metadata';text='null'},
 [pscustomobject]@{name='array_metadata';text='[]'}
)){Assert-Rejected $taskBadMeta.name {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskBadMeta.text) $taskId}}
$taskCall=[ordered]@{ai_call_id='00000000000000000000000000000061';operation='classify';input_path='C:\diagnostic\input.txt';instructions='分類';labels=@('review','normal');timeout_seconds=120}
$taskJob=[pscustomobject]@{job_id='00000000000000000000000000000062';target='C:\diagnostic\input.txt'};$taskRunId='00000000000000000000000000000063';$taskRun='C:\diagnostic\runs\'+$taskRunId
$taskTemplate=Get-AgentAiCallTemplate $taskCall.ai_call_id $taskJob $taskRun $taskRunId $taskApp 'C:\diagnostic'
$taskWithCall=$taskMeta.TrimEnd('}')+',"ai_calls":['+(ConvertTo-Json -InputObject $taskCall -Depth 8 -Compress)+']}'
$taskCallPlan=Assert-Accepted 'declared_ai_call_exact_template_preserved' (New-TestFrames $taskWithCall @($taskTemplate.robin)) $taskTemplate.robin
if(($taskCallPlan.ai_calls|ConvertTo-Json -Depth 8 -Compress) -cne ((ConvertFrom-Json $taskWithCall).ai_calls|ConvertTo-Json -Depth 8 -Compress) -or -not $taskCallPlan.robin.Contains('AGENT_AICALL_FAILED')){throw 'TEST_AICALL: Declared metadata or template changed.'}
$null=Assert-Accepted 'optional_ai_calls_empty' (New-TestFrames ($taskMeta.TrimEnd('}')+',"ai_calls":[]}')) 'WAIT 0'
$taskNoCallPlan=Assert-Accepted 'optional_ai_calls_omitted_stays_omitted' (New-TestFrames $taskMeta @($taskTemplate.robin)) $taskTemplate.robin
if(@($taskNoCallPlan.PSObject.Properties.Name) -ccontains 'ai_calls'){throw 'TEST_AICALL: Missing metadata was inferred.'}
foreach($taskBadCall in @(
 [pscustomobject]@{name='ai_calls_false';text=$taskMeta.TrimEnd('}')+',"ai_calls":false}'},
 [pscustomobject]@{name='ai_calls_case_wrong_key';text=$taskWithCall.Replace('"ai_calls":','"AI_CALLS":')},
 [pscustomobject]@{name='ai_call_nested_duplicate';text=$taskWithCall.Replace('"operation":"classify"','"operation":"classify","operation":"classify"')},
 [pscustomobject]@{name='ai_call_nested_case_duplicate';text=$taskWithCall.Replace('"operation":"classify"','"operation":"classify","OPERATION":"classify"')},
 [pscustomobject]@{name='ai_call_unknown_field';text=$taskWithCall.Replace('"operation":"classify"','"operation":"classify","unexpected":true')},
 [pscustomobject]@{name='ai_call_float_timeout';text=$taskWithCall.Replace('"timeout_seconds":120','"timeout_seconds":120.0')},
 [pscustomobject]@{name='ai_call_false_timeout';text=$taskWithCall.Replace('"timeout_seconds":120','"timeout_seconds":false')},
 [pscustomobject]@{name='ai_call_nonstring_label';text=$taskWithCall.Replace('"review"','7')},
 [pscustomobject]@{name='nonact_nonempty_ai_calls';text=$taskWithCall.Replace('"state":"ACT"','"state":"DONE"')}
)){Assert-Rejected $taskBadCall.name {$r=if($taskBadCall.name -ceq 'nonact_nonempty_ai_calls'){@()}else{@($taskTemplate.robin)};ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskBadCall.text $r) $taskId}}
# Recheck numeric metadata with a valid ACT body, so rejection is about metadata.
Assert-Rejected 'ai_call_float_timeout_with_act_body' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames ($taskWithCall.Replace('"timeout_seconds":120','"timeout_seconds":120.0')) @($taskTemplate.robin)) $taskId}
Assert-Rejected 'ai_call_false_metadata_with_act_body' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames ($taskWithCall.Replace('"timeout_seconds":120','"timeout_seconds":false')) @($taskTemplate.robin)) $taskId}
$taskGoodFrames=New-TestFrames $taskMeta
Assert-Rejected 'observed_backtick_after_metadata_end' {$f=New-TestFrames $taskMeta;$f[0]+="`n"+[char]96;ConvertFrom-AgentCopilotPlannerV2 $f $taskId}
Assert-Rejected 'null_frames' {ConvertFrom-AgentCopilotPlannerV2 $null $taskId}
Assert-Rejected 'single_frame' {ConvertFrom-AgentCopilotPlannerV2 @($taskGoodFrames[0]) $taskId}
Assert-Rejected 'extra_frame' {ConvertFrom-AgentCopilotPlannerV2 (@($taskGoodFrames)+@($taskGoodFrames[1])) $taskId}
Assert-Rejected 'wrong_frame_type' {ConvertFrom-AgentCopilotPlannerV2 @($taskGoodFrames[0],7) $taskId}
Assert-Rejected 'swapped_frames' {ConvertFrom-AgentCopilotPlannerV2 @($taskGoodFrames[1],$taskGoodFrames[0]) $taskId}
Assert-Rejected 'header_extra_space' {ConvertFrom-AgentCopilotPlannerV2 @($taskGoodFrames[0].Replace('AGENT_META_V2 ','AGENT_META_V2  '),$taskGoodFrames[1]) $taskId}
Assert-Rejected 'extra_after_final_marker' {ConvertFrom-AgentCopilotPlannerV2 @($taskGoodFrames[0],($taskGoodFrames[1]+"`nextra")) $taskId}
Assert-Rejected 'trailing_lf_after_final_marker' {ConvertFrom-AgentCopilotPlannerV2 @($taskGoodFrames[0],($taskGoodFrames[1]+"`n")) $taskId}
Assert-Rejected 'wrong_end_marker_nonce' {ConvertFrom-AgentCopilotPlannerV2 @($taskGoodFrames[0],$taskGoodFrames[1].Replace(('AGENT_END_'+$taskId),('AGENT_END_'+$taskOtherId))) $taskId}
Assert-Rejected 'metadata_raw_cr' {ConvertFrom-AgentCopilotPlannerV2 @($taskGoodFrames[0].Replace("`n","`r`n"),$taskGoodFrames[1]) $taskId}
Assert-Rejected 'robin_raw_cr' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta @("WAIT 0`r")) $taskId}
Assert-Rejected 'robin_raw_nul' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta @('WAIT '+[char]0)) $taskId}
Assert-Rejected 'metadata_escaped_nul' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames ($taskMeta.Replace('"message":"ok"','"message":"\u0000"'))) $taskId}
$taskEmoji=[char]::ConvertFromUtf32(0x1F642)
$null=Assert-Accepted 'valid_literal_surrogate_pair_body' (New-TestFrames $taskMeta @($taskEmoji)) $taskEmoji
$taskEscapedEmojiMeta=$taskMeta.Replace('"message":"ok"','"message":"\uD83D\uDE42"')
$taskEmojiPlan=Assert-Accepted 'valid_escaped_surrogate_pair_metadata' (New-TestFrames $taskEscapedEmojiMeta) 'WAIT 0'
if($taskEmojiPlan.message -cne $taskEmoji){throw 'TEST_UNICODE: Escaped pair changed.'}
$null=Assert-Accepted 'literal_backslash_u_not_unicode_escape' (New-TestFrames ($taskMeta.Replace('"message":"ok"','"message":"\\ud800"'))) 'WAIT 0'
$taskNewlinePlan=Assert-Accepted 'legal_escaped_metadata_newlines_preserved' (New-TestFrames ($taskMeta.Replace('"message":"ok"','"message":"a\r\nb"'))) 'WAIT 0'
if($taskNewlinePlan.message -cne "a`r`nb"){throw 'TEST_UNICODE: Legal metadata newline changed.'}
foreach($taskBadEscape in @('\uD800','\uDC00','\uD800x\uDC00','\uD800\\n\uDC00','\uD800\u0041')){Assert-Rejected ('invalid_escaped_unicode_'+$taskBadEscape) {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames ($taskMeta.Replace('"message":"ok"',('"message":"'+$taskBadEscape+'"')))) $taskId}}
Assert-Rejected 'literal_high_surrogate' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta @([string][char]0xD800)) $taskId}
Assert-Rejected 'literal_low_surrogate' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta @([string][char]0xDC00)) $taskId}
Assert-Rejected 'surrogate_split_across_rows' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta @([string][char]0xD800,[string][char]0xDC00)) $taskId}
$null=Assert-Accepted 'robin_64000_units' (New-TestFrames $taskMeta @('x'*64000)) ('x'*64000)
Assert-Rejected 'robin_64001_units' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta @('x'*64001)) $taskId}
$task250=@(1..250|ForEach-Object{'WAIT 0'});$null=Assert-Accepted 'robin_250_rows' (New-TestFrames $taskMeta $task250) ($task250 -join "`n")
Assert-Rejected 'robin_251_rows' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskMeta (@($task250)+@('WAIT 0'))) $taskId}
$taskManyEmpty=@('WAIT 0')+@(1..249|ForEach-Object{$taskEmpty});$null=Assert-Accepted '249_empty_markers_wire_overhead' (New-TestFrames $taskMeta $taskManyEmpty) ('WAIT 0'+("`n"*249))
$taskLongId='a'*128;$taskLongIdMeta=$taskMeta.Replace($taskId,$taskLongId);$taskLongIdEmpty='AGENT_EMPTY_V2 '+$taskLongId
$null=Assert-Accepted '128_character_nonce_with_empty_marker_overhead' (New-TestFrames $taskLongIdMeta (@('WAIT 0')+@(1..249|ForEach-Object{$taskLongIdEmpty})) $taskLongId) ('WAIT 0'+("`n"*249)) $taskLongId
Assert-Rejected '129_character_nonce' {ConvertFrom-AgentCopilotPlannerV2 $taskGoodFrames ('a'*129)}
Assert-Rejected 'nonce_trailing_lf' {ConvertFrom-AgentCopilotPlannerV2 $taskGoodFrames ($taskId+"`n")}
# The former diagnostic's 16384-row ceiling must not enter production metadata.
$null=Assert-Accepted 'metadata_single_row_above_16384' (New-TestFrames (New-TestMeta 'ACT' ('x'*20000))) 'WAIT 0'
$taskDoneBase=New-TestMeta 'DONE' 'x';$taskAtMeta=New-TestMeta 'DONE' ('x'*(1048576-64-$taskDoneBase.Length+1));$taskAtMeta=(' '*64)+$taskAtMeta
if($taskAtMeta.Length -ne 1048576){throw 'TEST_BOUNDARY: Metadata fixture calculation differs.'}
$null=Assert-Accepted 'metadata_exact_1mib' (New-TestFrames $taskAtMeta @()) ''
Assert-Rejected 'metadata_over_1mib' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames ($taskAtMeta+' ') @()) $taskId}
$taskSmallFinal=ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskDoneBase @()) $taskId
$taskAtFinalMeta=New-TestMeta 'DONE' ('x'*(1048576-$taskSmallFinal.Length+1))
$taskAtFinal=ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames $taskAtFinalMeta @()) $taskId
if($taskAtFinal.Length -ne 1048576){throw 'TEST_BOUNDARY: Final JSON fixture calculation differs.'};$taskPassed.Add('final_json_exact_1mib')
Assert-Rejected 'final_json_over_1mib' {ConvertFrom-AgentCopilotPlannerV2 (New-TestFrames (New-TestMeta 'DONE' ('x'*(1048576-$taskSmallFinal.Length+2))) @()) $taskId}
$taskCommands=@($taskAst.FindAll({param($n)$n -is [Management.Automation.Language.CommandAst]},$true)|ForEach-Object{$_.GetCommandName()})
foreach($taskForbidden in @('Test-AgentRobin','Invoke-AgentPad','Invoke-AgentCopilot','New-AgentAiCallTemplates','Write-AgentJson','Invoke-AgentRun')){if($taskCommands -ccontains $taskForbidden){throw 'TEST_AUTHORITY: Parser must not execute or create file authority.'}}
$taskPassed.Add('no_execution_or_file_authority_commands')

    $taskReport.status='passed'
} catch {
    $taskFailureRecord=$_
    $taskReport.failure=[ordered]@{exception_type=$_.Exception.GetType().FullName;message=$_.Exception.Message}
} finally {
    try {
        if($taskAppHash){
            $taskAfterHash=(Get-FileHash -LiteralPath $taskApp).Hash.ToLowerInvariant()
            $taskReport.source_sha256_after=$taskAfterHash;$taskReport.source_unchanged=($taskAfterHash -ceq $taskAppHash)
            if(-not $taskReport.source_unchanged){$taskReport.status='failed';$taskReport.failure=[ordered]@{exception_type='SourceHashMismatch';message='TEST_SOURCE_CHANGED: Source changed during validation.'}}
        }
        $taskReport.test_unchanged=((Get-FileHash -LiteralPath $taskTestPath).Hash.ToLowerInvariant() -ceq $taskTestHash)
        if(-not $taskReport.test_unchanged){$taskReport.status='failed';$taskReport.failure=[ordered]@{exception_type='TestHashMismatch';message='TEST_TEST_CHANGED: Test script changed during validation.'}}
    } catch {
        $taskReport.status='failed';$taskReport.source_unchanged=$false
        $taskReport.failure=[ordered]@{exception_type=$_.Exception.GetType().FullName;message=('TEST_PRESERVATION: '+$_.Exception.Message)}
        if($null -eq $taskFailureRecord){$taskFailureRecord=$_}
    }
    $taskReport.test_count=$taskPassed.Count;$taskReport.tests=@($taskPassed);$taskReport.source_function_definitions_loaded=$taskSourceFunctionCount;$taskReport.finished_utc=[DateTime]::UtcNow.ToString('o')
    $taskJson=ConvertTo-Json -InputObject $taskReport -Depth 12 -Compress
    # Emit failure evidence even if the optional file cannot be created.
    if($taskReport.status -cne 'passed' -or -not $taskEvidenceFile){$taskJson}
    if($taskEvidenceFile){
        # Historical evidence is immutable. CreateNew cannot replace any file.
        try {
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($taskEvidenceFile))|Out-Null
            $taskStream=[IO.File]::Open($taskEvidenceFile,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
            try{$taskBytes=[Text.Encoding]::UTF8.GetBytes($taskJson);$taskStream.Write($taskBytes,0,$taskBytes.Length);$taskStream.Flush($true)}finally{$taskStream.Dispose()}
        } catch {
            $taskReport.status='failed';$taskReport.failure=[ordered]@{exception_type=$_.Exception.GetType().FullName;message=('TEST_EVIDENCE: '+$_.Exception.Message)}
            ConvertTo-Json -InputObject $taskReport -Depth 12 -Compress
            throw
        }
    }
}
if($taskReport.status -cne 'passed'){
    if($taskFailureRecord){throw $taskFailureRecord}
    throw 'TEST_FAILED: Parser validation or source-preservation check failed; evidence was emitted.'
}
[ordered]@{status='passed';test_count=$taskPassed.Count;source_sha256=$taskAppHash;source_unchanged=$taskReport.source_unchanged;test_sha256=$taskTestHash;evidence_path=$taskEvidenceFile;provider_calls=0}|ConvertTo-Json -Compress
