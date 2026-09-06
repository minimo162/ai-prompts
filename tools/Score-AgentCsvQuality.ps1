# Deterministic comparison only; this does not assess reasons semantically or invent human approval.
param([Parameter(Mandatory=$true)][string]$ExpectedPath,[Parameter(Mandatory=$true)][string]$ResultPath,[Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
$qualityResultPath=$ResultPath
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
$ResultPath=$qualityResultPath
$expected=Read-AgentJson (Get-AgentFullPath $ExpectedPath);$actual=Read-AgentJson (Get-AgentFullPath $ResultPath)
$output=Get-AgentFullPath $OutputPath;Assert-AgentNoReparse $output;if(Test-Path -LiteralPath $output){throw 'QUALITY_OUTPUT_EXISTS'}
if($expected.schema_version -ne 1 -or $actual.schema_version -ne 1 -or $actual.sources.Count -ne 1 -or $actual.sources[0].sha256 -cne $expected.input_sha256){throw 'QUALITY_INPUT: Source identity differs.'}
$wanted=New-Object 'Collections.Generic.Dictionary[string,object]' ([StringComparer]::Ordinal)
foreach($row in $expected.rows){if($wanted.ContainsKey($row.id)){throw 'QUALITY_IDS: Duplicate expected ID.'};$wanted.Add($row.id,$row)}
if($actual.rows.Count -ne $wanted.Count){throw 'QUALITY_IDS: Count mismatch.'}
$clear=0;$correct=0;$reviews=0;$reviewed=0;$rows=@()
foreach($row in $actual.rows){
 if(-not $wanted.ContainsKey($row.original_id)){throw 'QUALITY_IDS: Unknown or duplicate result ID.'}
 $gold=$wanted[$row.original_id];[void]$wanted.Remove($row.original_id)
 if($gold.text -cne $row.original_text){throw 'QUALITY_TEXT: Original text differs.'}
 if($gold.needs_review){$reviews++;$ok=$row.result.status -ceq 'needs_review';if($ok){$reviewed++}}
 else{$clear++;$ok=$row.result.category -ceq $gold.category -and $row.result.status -ceq 'success';if($ok){$correct++}}
 $rows+=[pscustomobject]@{id=$row.original_id;matches_draft=$ok;actual_category=$row.result.category;actual_status=$row.result.status}
}
$approved=$expected.human_reviewed -is [bool] -and $expected.human_reviewed -and $expected.reviewer_id -cmatch '^[a-f0-9]{32}$' -and -not [string]::IsNullOrWhiteSpace($expected.reviewed_utc)
$accuracy=if($clear){$correct/[double]$clear}else{0};$recall=if($reviews){$reviewed/[double]$reviews}else{0}
Write-AgentJson $output @{schema_version=1;kind='quality_comparison';status=$(if(-not $approved){'DRAFT_ONLY'}elseif($accuracy -ge 0.9 -and $recall -eq 1){'PASS'}else{'FAIL'});human_reviewed_ground_truth=$approved;clear_count=$clear;clear_correct=$correct;review_count=$reviews;review_correct=$reviewed;clear_accuracy=$accuracy;review_recall=$recall;input_sha256=$expected.input_sha256;result_sha256=Get-AgentHash $ResultPath;rows=$rows;reason_quality='requires_human_review'}
Write-Output $output
