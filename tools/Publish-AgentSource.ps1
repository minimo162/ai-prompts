# Development-only publication helper. Not part of the three-file application.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SourceDirectory,
    [Parameter(Mandatory=$true)][string]$DestinationDirectory,
    [Parameter(Mandatory=$true)][string]$EvidenceDirectory,
    [Parameter(Mandatory=$true)][string]$ExpectedSourceRelease,
    [Parameter(Mandatory=$true)][string]$ExpectedDestinationRelease
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2.0
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
$source=Get-AgentFullPath $SourceDirectory
$destination=Get-AgentFullPath $DestinationDirectory
$evidence=Get-AgentFullPath $EvidenceDirectory
if($source -ieq $destination -or $evidence -ieq $source -or $evidence -ieq $destination -or $evidence.StartsWith($destination+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'PUBLISH_PATH: Distinct source, destination and evidence paths required.'}
foreach($path in @($source,$destination,$evidence)){Assert-AgentNoReparse $path}
if(Test-Path -LiteralPath $evidence){throw 'PUBLISH_EVIDENCE: Fresh evidence directory required.'}
$names=@('App.ps1','index.html','業務エージェント.cmd')
foreach($name in $names){Assert-AgentNoReparse (Join-Path $source $name);Assert-AgentNoReparse (Join-Path $destination $name)}
$items=@(Get-ChildItem -LiteralPath $destination -Force)
if($items.Count -ne 3 -or @($items|Where-Object {$_.PSIsContainer -or $names -cnotcontains $_.Name}).Count){throw 'PUBLISH_DESTINATION: Exactly three existing distribution files required.'}
$new=Get-AgentRelease $source;$old=Get-AgentRelease $destination
if($new.release -cne $ExpectedSourceRelease -or $old.release -cne $ExpectedDestinationRelease){throw 'PUBLISH_PIN: Release changed before publication.'}
if([version]$new.version -lt [version]$old.version){throw 'PUBLISH_VERSION: Downgrade refused.'}
# Open all files before the first destination write. This preserves their file objects,
# owner and ACL, and prevents normal readers from seeing a partially written package.
# Process/OS crashes are not transactional: retain the backup for explicit recovery.
$streams=@{};$payloads=@{};$originals=@{};$acls=@{}
$report=[ordered]@{status='failed';source_release=$new.release;old_release=$old.release;destination=$destination;writes=0;rollback_attempted=$false;rollback_verified=$false;metadata_preserved=$false;crash_atomic=$false;error='';started_utc=[DateTime]::UtcNow.ToString('o')}
$changed=$false
function Read-PublishStream($Stream){
    if($Stream.Length -gt 10485760){throw 'PUBLISH_SIZE: Distribution file exceeds 10 MiB.'}
    $bytes=New-Object byte[] ([int]$Stream.Length);$Stream.Position=0;$offset=0
    while($offset -lt $bytes.Length){$count=$Stream.Read($bytes,$offset,$bytes.Length-$offset);if($count -eq 0){throw 'PUBLISH_READ: Unexpected EOF.'};$offset+=$count}
    return ,$bytes
}
function Get-PublishBytesHash([byte[]]$Bytes){
    $hash=[Security.Cryptography.SHA256]::Create()
    try{return ([BitConverter]::ToString($hash.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}finally{$hash.Dispose()}
}
function Write-PublishStream($Stream,[byte[]]$Bytes){
    $Stream.Position=0;$Stream.SetLength($Bytes.Length);$Stream.Write($Bytes,0,$Bytes.Length);$Stream.Flush($true)
}
[IO.Directory]::CreateDirectory($evidence)|Out-Null
$claim=[IO.File]::Open((Join-Path $evidence 'publish.claim'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
$claim.Dispose()
try {
    foreach($name in $names){
        $payloads[$name]=[IO.File]::ReadAllBytes((Join-Path $source $name))
        if((Get-PublishBytesHash $payloads[$name]) -cne $new.hashes.$name){throw 'PUBLISH_SOURCE: Source changed.'}
        $path=Join-Path $destination $name
        $acls[$name]=(Get-Acl -LiteralPath $path).Sddl
        $streams[$name]=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
        $originals[$name]=Read-PublishStream $streams[$name]
        if((Get-PublishBytesHash $originals[$name]) -cne $old.hashes.$name){throw 'PUBLISH_DESTINATION: Destination changed before lock.'}
    }
    $backup=Join-Path $evidence 'backup';[IO.Directory]::CreateDirectory($backup)|Out-Null
    foreach($name in $names){[IO.File]::WriteAllBytes((Join-Path $backup $name),$originals[$name])}
    Write-AgentJson (Join-Path $evidence 'before.json') @{source=$new;destination=$old;acl=$acls}
    foreach($name in $names){
        if($new.hashes.$name -ceq $old.hashes.$name){continue}
        $changed=$true;$report.writes++
        Write-PublishStream $streams[$name] $payloads[$name]
    }
    foreach($name in $names){if((Get-PublishBytesHash (Read-PublishStream $streams[$name])) -cne $new.hashes.$name){throw 'PUBLISH_VERIFY: Written bytes differ.'}}
    $report.status='published'
} catch {
    $report.error=$_.Exception.Message
    if($changed){
        $report.rollback_attempted=$true
        try {
            foreach($name in $names){Write-PublishStream $streams[$name] $originals[$name]}
            foreach($name in $names){if((Get-PublishBytesHash (Read-PublishStream $streams[$name])) -cne $old.hashes.$name){throw 'PUBLISH_ROLLBACK: Old bytes differ.'}}
            $report.rollback_verified=$true
        } catch {$report.status='unknown';$report.error+='; rollback: '+$_.Exception.Message}
    }
} finally {
    foreach($stream in $streams.Values){$stream.Dispose()}
    try {
        $same=$true;foreach($name in $acls.Keys){if((Get-Acl -LiteralPath (Join-Path $destination $name)).Sddl -cne $acls[$name]){$same=$false}}
        $report.metadata_preserved=$same
        if(-not $same){$report.status='unknown';$report.error+='; PUBLISH_ACL: Metadata differs.'}
        $final=Get-AgentRelease $destination;$report.final_release=$final.release
        $expectedFinal=if($report.status -ceq 'published'){$new.release}else{$old.release}
        if($final.release -cne $expectedFinal){$report.status='unknown';$report.error+='; PUBLISH_FINAL: Release differs.'}
    } catch {$report.status='unknown';$report.error+='; '+$_.Exception.Message}
    $report.finished_utc=[DateTime]::UtcNow.ToString('o')
    Write-AgentJson (Join-Path $evidence 'result.json') $report
}
$report|ConvertTo-Json -Depth 6
if($report.status -cne 'published'){throw 'PUBLISH_FAILED: See immutable publication evidence.'}
