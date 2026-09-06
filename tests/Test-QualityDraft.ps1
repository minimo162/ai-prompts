$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\quality-draft-'+[guid]::NewGuid().ToString('N'))));[void][IO.Directory]::CreateDirectory($root)
$fixture=Join-Path $PSScriptRoot 'fixtures\inquiries-v1';$expected=Read-AgentJson (Join-Path $fixture 'expected-draft.json')
$manifest=New-AgentCsvManifest @((Join-Path $fixture 'inquiries-50.csv'));$results=New-AgentCsvResults $manifest
for($i=0;$i -lt $results.Count;$i++){$results[$i].category=if($expected.rows[$i].category){$expected.rows[$i].category}else{'その他'};$results[$i].status=if($expected.rows[$i].needs_review){'needs_review'}else{'success'};$results[$i].reason='Synthetic scorer fixture, not real model evidence'}
$receipt=Export-AgentCsvResults $root $manifest $results $expected.categories
$output=Join-Path $root 'score.json'
& (Join-Path $PSScriptRoot '..\tools\Score-AgentCsvQuality.ps1') -ExpectedPath (Join-Path $fixture 'expected-draft.json') -ResultPath $receipt.artifacts[0].path -OutputPath $output | Out-Null
$score=Read-AgentJson $output
if($score.status -cne 'DRAFT_ONLY' -or $score.human_reviewed_ground_truth -or $score.clear_count -ne 40 -or $score.review_count -ne 10 -or $score.clear_accuracy -ne 1 -or $score.review_recall -ne 1){throw 'Draft scorer must not imply human approval'}
$changed=Read-AgentJson $receipt.artifacts[0].path;$changed.rows[0].original_id='unknown';$changedPath=Join-Path $root 'changed.json';Write-AgentJson $changedPath $changed
$errorText='';try{& (Join-Path $PSScriptRoot '..\tools\Score-AgentCsvQuality.ps1') -ExpectedPath (Join-Path $fixture 'expected-draft.json') -ResultPath $changedPath -OutputPath (Join-Path $root 'invalid-score.json') | Out-Null}catch{$errorText=$_.Exception.Message}
if($errorText -notlike 'QUALITY_IDS:*'){throw 'Unknown result ID must fail'}
Write-Output ('PASS: draft fixture 50 rows, 40 clear/10 review; no human approval inferred; unknown ID rejected. Evidence: '+$root)
