# Verifies immutable artifacts and every original cell; does not judge semantic quality.
param([Parameter(Mandatory=$true)][string]$InputPath,[Parameter(Mandatory=$true)][string]$MeasurementPath,[Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
$output=Get-AgentFullPath $OutputPath;Assert-AgentNoReparse $output
if(Test-Path -LiteralPath $output){throw 'VERIFY_OUTPUT_EXISTS'}
$measurement=Read-AgentJson (Get-AgentFullPath $MeasurementPath)
$source=Read-AgentCsvSource (Get-AgentFullPath $InputPath);$cells=ConvertFrom-AgentCsv $source.text
$artifacts=@($measurement.artifacts)
if($artifacts.Count -ne 4){throw 'VERIFY_ARTIFACT_COUNT'}
foreach($artifact in $artifacts){
 if((Get-AgentHash $artifact.path) -cne $artifact.sha256 -or (Get-Item -LiteralPath $artifact.path).Length -ne $artifact.bytes){throw 'VERIFY_ARTIFACT_CHANGED'}
}
$results=@($artifacts|Where-Object name -CEQ 'results.json')
if($results.Count -ne 1){throw 'VERIFY_RESULT_IDENTITY'}
$actual=Read-AgentJson $results[0].path
if($actual.sources.Count -ne 1 -or $actual.sources[0].sha256 -cne $source.sha256 -or $actual.rows.Count -ne ($cells.Count-1)){throw 'VERIFY_SOURCE_IDENTITY'}
$seen=New-Object 'Collections.Generic.HashSet[int]'
foreach($row in $actual.rows){
 $n=[int]$row.row_number
 if($n -lt 1 -or $n -ge $cells.Count -or -not $seen.Add($n)){throw 'VERIFY_ROW_IDENTITY'}
 $wanted=@($cells[$n].values)
 if($row.values.Count -ne $wanted.Count){throw 'VERIFY_CELL_COUNT'}
 for($i=0;$i -lt $wanted.Count;$i++){if($row.values[$i] -cne $wanted[$i]){throw 'VERIFY_ORIGINAL_CELL'}}
 if($row.original_id -cne $wanted[0] -or $row.original_text -cne $wanted[1]){throw 'VERIFY_ORIGINAL_FIELDS'}
}
Write-AgentJson $output @{schema_version=1;kind='measurement_integrity';status='PASS';input_sha256=$source.sha256;result_sha256=$results[0].sha256;rows=$actual.rows.Count;artifacts=$artifacts.Count;all_original_cells_preserved=$true;semantic_quality='NOT_EVALUATED';human_approval=$false}
Write-Output $output
