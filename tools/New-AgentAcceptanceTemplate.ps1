# Creates a NOT_RUN operator record. Does not fabricate verification or approve a release.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$CandidateDirectory,[Parameter(Mandatory=$true)][ValidateSet('nonlive','native_pad','live_m365','business_e2e','corporate_pc','usability','quality','comparison','documentation')][string]$Kind,[Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
$candidate=Get-AgentRelease (Get-AgentFullPath $CandidateDirectory)
$output=Get-AgentFullPath $OutputPath;Assert-AgentNoReparse $output
if(Test-Path -LiteralPath $output){throw 'ACCEPTANCE_RECORD_EXISTS: Records must be new.'}
if(-not $output.EndsWith('.acceptance.json') -or $output.StartsWith((Get-AgentFullPath $CandidateDirectory)+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'ACCEPTANCE_RECORD_PATH: Use a .acceptance.json path outside the package.'}
$metrics=[ordered]@{}
switch($Kind){
 business_e2e {$metrics=@{input_count=$null;output_count=$null;duplicate_ids=$null;input_preserved=$null;ui_operated=$null}}
 usability {$metrics=@{first_use=$null;completed=$null;oral_intervention=$null}}
 quality {$metrics=@{human_reviewed_ground_truth=$null;clear_accuracy=$null;review_recall=$null}}
 comparison {$metrics=@{same_quality_threshold=$null;same_50_rows=$null;human_time_reduction=$null;direct_copilot_human_seconds=$null;fixed_flow_human_seconds=$null;agent_human_seconds=$null;elapsed_seconds=$null;pc_occupied_seconds=$null}}
}
Write-AgentJson $output ([ordered]@{schema_version=1;record_id=[guid]::NewGuid().ToString('N');kind=$Kind;status='NOT_RUN';candidate_hashes=$candidate.hashes;simulated=$null;requirements=@();cases=@();host_id='';participant_id='';corporate=$null;administrator=$null;metrics=$metrics;attachments=@();notes='実施した範囲と証拠だけを記録してください。未実施をPASSに変更しないでください。'})
Write-Output $output
