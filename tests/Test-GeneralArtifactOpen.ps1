$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library -OfflineTest
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\general-open-'+[guid]::NewGuid().ToString('N'))));$null=Initialize-AgentHome $root
$jobId=[guid]::NewGuid().ToString('N');$run=Join-Path (Get-AgentJobDirectory $root $jobId) ('runs\'+[guid]::NewGuid().ToString('N'));[void][IO.Directory]::CreateDirectory((Join-Path $run 'artifacts'))
$path=Join-Path $run 'artifacts\result.txt';[IO.File]::WriteAllText($path,'result')
$observed=Get-AgentObservedArtifacts ([pscustomobject]@{status='success';artifacts=@($path)}) $run
$job=[pscustomobject]@{job_id=$jobId;status='done';goal='fixture';artifacts=@(Get-AgentArtifactView $observed);observed_artifacts=$observed;history=@()}
Save-AgentJob (Get-AgentJobDirectory $root $jobId) $job
$id=$job.artifacts[0].artifact_id;$checks=0;$script:openCalls=0;$script:opened=''
function Check($value,$name){if(-not $value){throw ('FAIL: '+$name)};$script:checks++}
function Reject($action,$code){$message='';try{& $action}catch{$message=$_.Exception.Message};Check ($message -like ($code+':*')) $message}
function Start-Process {param($FilePath);$script:openCalls++;$script:opened=$FilePath}
Check (Test-AgentId $id) 'Server-owned opaque ID generated'
Check ($job.artifacts[0].open_supported) 'Text view exposes open capability'
Reject {Open-AgentArtifact $root $jobId $id} ARTIFACT_OPEN_OFFLINE
Check ($script:openCalls -eq 0) 'Offline mode never launches an associated app'
$script:AgentOfflineTest=$false
Open-AgentArtifact $root $jobId $id
Check ($script:openCalls -eq 1 -and $script:opened -ceq $path) 'Verified exact file reaches launch boundary'
Check ((Get-AgentJob $root $jobId).artifacts[0].artifact_id -ceq $id) 'ID persists after reload'
Reject {Open-AgentArtifact $root $jobId ('f'*32)} ARTIFACT_SCOPE
$otherId=[guid]::NewGuid().ToString('N')
Save-AgentJob (Get-AgentJobDirectory $root $otherId) ([pscustomobject]@{job_id=$otherId;status='done';artifacts=@();observed_artifacts=@();history=@()})
Reject {Open-AgentArtifact $root $otherId $id} ARTIFACT_SCOPE
Reject {Open-AgentArtifact $root '' $id} INVALID_ID
[IO.File]::WriteAllText($path,'changed')
Reject {Open-AgentArtifact $root $jobId $id} ARTIFACT_CHANGED
[IO.File]::Delete($path)
Reject {Open-AgentArtifact $root $jobId $id} ARTIFACT_CHANGED
[IO.File]::WriteAllText($path,'result')
$job.observed_artifacts=@($observed[0],$observed[0]);Save-AgentJob (Get-AgentJobDirectory $root $jobId) $job
Reject {Open-AgentArtifact $root $jobId $id} ARTIFACT_SCOPE
$job.observed_artifacts=@($observed[0]);$other=Join-Path $root 'outside.txt';[IO.File]::WriteAllText($other,'result');$job.observed_artifacts[0].path=$other;$job.artifacts[0].path=$other;Save-AgentJob (Get-AgentJobDirectory $root $jobId) $job
Reject {Open-AgentArtifact $root $jobId $id} INVALID_PATH
$scriptFile=Join-Path $run 'artifacts\example.ps1';[IO.File]::WriteAllText($scriptFile,'result');$job.observed_artifacts[0].path=$scriptFile;$job.artifacts=@(Get-AgentArtifactView $job.observed_artifacts);Save-AgentJob (Get-AgentJobDirectory $root $jobId) $job
Check (-not $job.artifacts[0].open_supported) 'Executable extension is not exposed as openable'
Reject {Open-AgentArtifact $root $jobId $id} ARTIFACT_FORMAT
Check ($script:openCalls -eq 1) 'Every rejected request leaves launch count unchanged'
$legacy=Get-AgentArtifactView @([pscustomobject]@{path=$path;label='old result'})
Check ($null -eq $legacy.PSObject.Properties['artifact_id']) 'Legacy metadata is not silently granted new IDs'
Write-Output "PASS: $checks general artifact checks; launch boundary mocked."
