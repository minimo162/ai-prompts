# Maintainer-only acceptance evaluator. A matching report is evidence, never a publishing command.
[CmdletBinding()]
param([ValidateSet('Evaluate','Library')][string]$Mode='Evaluate',[string]$CandidateDirectory,[string]$EvidenceDirectory,[string]$OutputPath)
$ErrorActionPreference='Stop'
$acceptanceMode=$Mode
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
function Test-AcceptanceBool($Object,[string]$Name,[bool]$Expected){$v=Get-AgentProperty $Object $Name $null;return $v -is [bool] -and $v -eq $Expected}
function Test-AcceptanceNumber($Object,[string]$Name,[double]$Minimum,[double]$Maximum){$v=Get-AgentProperty $Object $Name $null;return ($v -is [int] -or $v -is [long] -or $v -is [double] -or $v -is [decimal]) -and $v -ge $Minimum -and $v -le $Maximum}
function Test-AcceptanceComparison($Metrics){
 if(-not(Test-AcceptanceBool $Metrics same_quality_threshold $true) -or -not(Test-AcceptanceBool $Metrics same_50_rows $true)){return $false}
 foreach($name in @('direct_copilot_human_seconds','fixed_flow_human_seconds')){if(-not(Test-AcceptanceNumber $Metrics $name 0.001 31536000)){return $false}}
 if(-not(Test-AcceptanceNumber $Metrics agent_human_seconds 0 31536000) -or -not(Test-AcceptanceNumber $Metrics human_time_reduction 0.3 1)){return $false}
 $baseline=[Math]::Min($Metrics.direct_copilot_human_seconds,$Metrics.fixed_flow_human_seconds)
 $reduction=($baseline-$Metrics.agent_human_seconds)/$baseline
 return $reduction -ge 0.3 -and [Math]::Abs($reduction-$Metrics.human_time_reduction) -lt 0.000001
}
function Get-AgentAcceptanceLayers([string]$Id){
 $special=@{'8.6'=@('quality');'8.7'=@('comparison');'10.2'=@('live_m365','business_e2e');'10.3'=@('nonlive');'10.4'=@('native_pad');'10.7'=@('native_pad');'11.1'=@('corporate_pc');'11.3'=@('business_e2e','native_pad');'11.8'=@('live_m365','business_e2e');'11.9'=@('usability');'12.1'=@('nonlive');'12.2'=@('nonlive');'12.3'=@('live_m365');'12.4'=@('live_m365');'12.5'=@('corporate_pc');'12.6'=@('live_m365','business_e2e');'12.7'=@('documentation');'13.1'=@('nonlive');'13.2'=@('nonlive');'13.3'=@('corporate_pc');'13.4'=@('business_e2e');'13.5'=@('corporate_pc');'13.6'=@('corporate_pc');'13.7'=@('nonlive','corporate_pc');'14.1'=@('nonlive');'14.2'=@('nonlive');'14.3'=@('nonlive');'14.4'=@('nonlive');'14.6'=@('nonlive','business_e2e');'14.7'=@('documentation')}
 if($special.ContainsKey($Id)){return ,$special[$Id]};return ,@('business_e2e')
}
function Test-AgentAcceptanceEvidence($Candidate,[object[]]$Records,[string[]]$RequirementIds){
 $blockers=New-Object 'Collections.Generic.List[string]';$accepted=@();$kinds=@('nonlive','native_pad','live_m365','business_e2e','corporate_pc','usability','quality','comparison','documentation');$seen=New-Object 'Collections.Generic.HashSet[string]'
 foreach($record in $Records){
  $id=[string](Get-AgentProperty $record 'record_id' 'invalid-record')
  if($id -cnotmatch '^[a-f0-9]{32}$' -or -not $seen.Add($id) -or (Get-AgentProperty $record 'requirements' $null) -isnot [Array]){$blockers.Add($id+': invalid or duplicate record identity/schema');continue}
  if((Get-AgentProperty $record 'schema_version' 0) -isnot [int] -or $record.schema_version -ne 1 -or $kinds -cnotcontains (Get-AgentProperty $record 'kind' '') -or (Get-AgentProperty $record 'status' '') -cne 'PASS'){$blockers.Add($id+': not a passing supported record');continue}
  $hashes=Get-AgentProperty $record 'candidate_hashes' $null;$match=$true
  foreach($name in @('App.ps1','index.html','業務エージェント.cmd')){if((Get-AgentProperty $hashes $name '') -cne $Candidate.hashes.$name){$match=$false}}
  if(-not $match){$blockers.Add($id+': candidate hash mismatch');continue}
  if(-not(Test-AcceptanceBool $record attachments_verified $true)){$blockers.Add($id+': missing verified evidence attachments');continue}
  if($record.kind -cnotin @('nonlive','documentation') -and -not(Test-AcceptanceBool $record simulated $false)){$blockers.Add($id+': simulated evidence cannot satisfy a live gate');continue}
  $accepted+=,$record
 }
 $coverage=@()
 foreach($id in $RequirementIds){
  $layers=Get-AgentAcceptanceLayers $id;$missing=@()
  foreach($kind in $layers){if(@($accepted | Where-Object {$_.kind -ceq $kind -and @((Get-AgentProperty $_ 'requirements' @())) -ccontains $id}).Count -eq 0){$missing+=$kind}}
  $coverage+=[pscustomobject]@{requirement=$id;required_layers=$layers;status=$(if($missing.Count){'UNVERIFIED'}else{'EVIDENCE_PRESENT'});missing_layers=$missing}
  if($missing.Count){$blockers.Add($id+': missing '+($missing -join ','))}
 }
 $business=@($accepted | Where-Object kind -CEQ 'business_e2e')
 foreach($count in @(1,50,100)){
  if(@($business | Where-Object { $m=Get-AgentProperty $_ 'metrics' $null;(Test-AcceptanceNumber $m input_count $count $count) -and (Test-AcceptanceNumber $m output_count $count $count) -and (Test-AcceptanceNumber $m duplicate_ids 0 0) -and (Test-AcceptanceBool $m input_preserved $true) -and (Test-AcceptanceBool $m ui_operated $true) }).Count -eq 0){$blockers.Add('business size '+$count+': exact counts, input preservation and UI evidence missing')}
 }
 $environment=@($accepted | Where-Object {$_.kind -cin @('corporate_pc','business_e2e') -and (Get-AgentProperty $_ 'host_id' '') -match '^[a-f0-9]{32}$' -and (Get-AgentProperty $_ 'participant_id' '') -match '^[a-f0-9]{32}$'})
 if(@($environment | ForEach-Object host_id | Select-Object -Unique).Count -lt 2 -or @($environment | ForEach-Object participant_id | Select-Object -Unique).Count -lt 2){$blockers.Add('two distinct PCs and participants are required')}
 if(@($environment | Where-Object { $_.kind -ceq 'corporate_pc' -and (Test-AcceptanceBool $_ corporate $true) -and (Test-AcceptanceBool $_ administrator $false) }).Count -eq 0){$blockers.Add('non-administrator corporate PC acceptance missing')}
 $usability=@($accepted | Where-Object {$_.kind -ceq 'usability' -and (Get-AgentProperty $_ 'participant_id' '') -match '^[a-f0-9]{32}$' -and (Test-AcceptanceBool (Get-AgentProperty $_ 'metrics' $null) first_use $true)} | Group-Object participant_id | ForEach-Object {$_.Group[0]})
 $independent=@($usability | Where-Object {$m=Get-AgentProperty $_ 'metrics' $null;(Test-AcceptanceBool $m completed $true) -and (Test-AcceptanceBool $m oral_intervention $false)})
 if($usability.Count -lt 5 -or $independent.Count -lt 4){$blockers.Add('five first-use participants and four independent completions are required')}
 $quality=@($accepted | Where-Object {$_.kind -ceq 'quality' -and (Test-AcceptanceBool (Get-AgentProperty $_ 'metrics' $null) human_reviewed_ground_truth $true) -and (Test-AcceptanceNumber (Get-AgentProperty $_ 'metrics' $null) clear_accuracy 0.9 1) -and (Test-AcceptanceNumber (Get-AgentProperty $_ 'metrics' $null) review_recall 1 1)})
 if($quality.Count -eq 0){$blockers.Add('human-reviewed quality targets missing')}
 $comparison=@($accepted | Where-Object {$_.kind -ceq 'comparison' -and (Test-AcceptanceComparison (Get-AgentProperty $_ 'metrics' $null))})
 if($comparison.Count -eq 0){$blockers.Add('same-quality 50-row comparison and 30 percent human-time reduction missing')}
 foreach($case in @('native_save_failure','paste_delay','foreground_change','clipboard_preservation')){
  if(@($accepted | Where-Object {$_.kind -ceq 'native_pad' -and @((Get-AgentProperty $_ 'cases' @())) -ccontains $case}).Count -eq 0){$blockers.Add('native PAD case missing: '+$case)}
 }
 foreach($case in @('authentication_expiry','post_send_timeout','long_response','multiple_turns')){
  if(@($accepted | Where-Object {$_.kind -ceq 'live_m365' -and @((Get-AgentProperty $_ 'cases' @())) -ccontains $case}).Count -eq 0){$blockers.Add('live M365 case missing: '+$case)}
 }
 return [pscustomobject]@{schema_version=1;candidate=$Candidate;status=$(if($blockers.Count){'NOT_READY'}else{'READY_FOR_REVIEW'});release_approved=$false;accepted_records=$accepted.Count;coverage=$coverage;blockers=@($blockers.ToArray())}
}
if($acceptanceMode -ceq 'Evaluate'){
 $candidate=Get-AgentRelease (Get-AgentFullPath $CandidateDirectory)
 $evidenceRoot=Get-AgentFullPath $EvidenceDirectory;Assert-AgentNoReparse $evidenceRoot
 $output=Get-AgentFullPath $OutputPath;Assert-AgentNoReparse $output
 if([IO.File]::Exists($output) -or $output.EndsWith('.acceptance.json') -or $output.StartsWith((Get-AgentFullPath $CandidateDirectory)+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'ACCEPTANCE_OUTPUT: Use a new report path outside the candidate.'}
 $catalog=Read-AgentJson (Join-Path $PSScriptRoot '..\docs\issues-8-14-acceptance.json');$ids=@($catalog.issues | ForEach-Object {$_.acceptance | ForEach-Object id})
 $records=@()
 foreach($file in @(Get-ChildItem -LiteralPath $evidenceRoot -Filter '*.acceptance.json' -File)){
  $path=Assert-AgentPathUnder $file.FullName $evidenceRoot;$record=Read-AgentJson $path;$verified=$true
  $attachments=@((Get-AgentProperty $record 'attachments' @()));if($attachments.Count -eq 0){$verified=$false}
  foreach($attachment in $attachments){try{if([IO.Path]::IsPathRooted($attachment.relative_path)){throw 'ABSOLUTE_ATTACHMENT'};$asset=Assert-AgentPathUnder (Join-Path $evidenceRoot $attachment.relative_path) $evidenceRoot;if((Get-AgentHash $asset) -cne $attachment.sha256){$verified=$false}}catch{$verified=$false}}
  $record | Add-Member -NotePropertyName attachments_verified -NotePropertyValue $verified -Force;$records+=,$record
 }
 $report=Test-AgentAcceptanceEvidence $candidate $records $ids
 Write-AgentJson $output $report
 $report | Select-Object status,release_approved,accepted_records,@{n='blocker_count';e={$_.blockers.Count}} | ConvertTo-Json
 if($report.status -cne 'READY_FOR_REVIEW'){exit 2}
}
