# Explicit repair of a crashed three-file publication. Never changes ACLs or user data.
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$PublicationEvidenceDirectory,
 [Parameter(Mandatory=$true)][string]$DestinationDirectory,
 [Parameter(Mandatory=$true)][string]$EvidenceDirectory,
 [Parameter(Mandatory=$true)][string]$ExpectedBackupRelease,
 [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$ExpectedAppHash,
 [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$ExpectedHtmlHash,
 [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$ExpectedCmdHash
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
$origin=Get-AgentFullPath $PublicationEvidenceDirectory;$destination=Get-AgentFullPath $DestinationDirectory;$evidence=Get-AgentFullPath $EvidenceDirectory
foreach($path in @($origin,$destination,$evidence)){Assert-AgentNoReparse $path}
if([IO.Directory]::Exists($evidence) -or [IO.File]::Exists($evidence) -or $evidence.StartsWith($destination+'\',[StringComparison]::OrdinalIgnoreCase) -or $evidence.StartsWith($origin+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'RESTORE_EVIDENCE: Use a new separate evidence directory.'}
$before=Read-AgentJson (Join-Path $origin 'before.json')
try{$publisher=Get-Process -Id $before.publisher_pid -ErrorAction Stop}catch{$publisher=$null}
if($null -ne $publisher -and $publisher.StartTime.ToUniversalTime().ToString('o') -ceq $before.publisher_started){throw 'RESTORE_BUSY: Original publisher is still running.'}
if((Get-AgentFullPath $before.destination_path) -ine $destination){throw 'RESTORE_TARGET: Destination differs from the original publication record.'}
$backup=Assert-AgentPathUnder (Join-Path $origin 'backup') $origin
$release=Get-AgentRelease $backup
if($release.release -cne $ExpectedBackupRelease -or $before.destination.release -cne $ExpectedBackupRelease){throw 'RESTORE_BACKUP: Backup identity differs.'}
$names=@('App.ps1','index.html','業務エージェント.cmd')
$expected=@{'App.ps1'=$ExpectedAppHash;'index.html'=$ExpectedHtmlHash;'業務エージェント.cmd'=$ExpectedCmdHash}
$streams=@{};$payloads=@{};$acls=@{}
$report=[ordered]@{status='refused';destination=$destination;backup_release=$ExpectedBackupRelease;expected_current_hashes=$expected;writes=0;metadata_preserved=$false;error='';started_utc=[DateTime]::UtcNow.ToString('o')}
function Hash-RestoreBytes([byte[]]$Bytes){$sha=[Security.Cryptography.SHA256]::Create();try{return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}}
[void][IO.Directory]::CreateDirectory($evidence)
try {
 foreach($name in $names){
  $path=Join-Path $destination $name;Assert-AgentNoReparse $path
  $acls[$name]=(Get-Acl -LiteralPath $path).Sddl
  if($acls[$name] -cne $before.acl.$name){throw 'RESTORE_ACL: ACL/owner changed since publication; not modifying it.'}
  $stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None);$streams[$name]=$stream
  if($stream.Length -gt 10485760){throw 'RESTORE_SIZE: Unexpected file size.'}
  $bytes=New-Object byte[] ([int]$stream.Length);$offset=0
  while($offset -lt $bytes.Length){$read=$stream.Read($bytes,$offset,$bytes.Length-$offset);if($read -eq 0){throw 'RESTORE_READ: Incomplete read.'};$offset+=$read}
  if((Hash-RestoreBytes $bytes) -cne $expected[$name]){throw 'RESTORE_CHANGED: Destination changed before lock.'}
  $payloads[$name]=[IO.File]::ReadAllBytes((Join-Path $backup $name))
  if((Hash-RestoreBytes $payloads[$name]) -cne $release.hashes.$name){throw 'RESTORE_BACKUP: Backup changed during read.'}
 }
 Write-AgentJson (Join-Path $evidence 'before.json') @{destination=$destination;backup_release=$release;current_hashes=$expected;acl=$acls}
 foreach($name in $names){$stream=$streams[$name];$bytes=$payloads[$name];$stream.Position=0;$stream.SetLength($bytes.Length);$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true);$report.writes++}
 $report.status='written'
}catch{$report.error=$_.Exception.Message;if($report.writes -gt 0){$report.status='unknown'}}
finally{
 foreach($stream in $streams.Values){$stream.Dispose()}
 if($report.status -ceq 'written'){
  try{
   $actual=Get-AgentRelease $destination
   if($actual.release -cne $ExpectedBackupRelease){throw 'RESTORE_VERIFY: Restored set differs.'}
   foreach($name in $names){if((Get-Acl -LiteralPath (Join-Path $destination $name)).Sddl -cne $acls[$name]){throw 'RESTORE_ACL: Metadata changed.'}}
   $report.metadata_preserved=$true;$report.status='restored'
  }catch{$report.status='unknown';$report.error=$_.Exception.Message}
 }
 $report.finished_utc=[DateTime]::UtcNow.ToString('o');Write-AgentJson (Join-Path $evidence 'result.json') $report
}
$report|ConvertTo-Json -Depth 10
if($report.status -cne 'restored'){throw 'RESTORE_FAILED: See the new immutable recovery record.'}
