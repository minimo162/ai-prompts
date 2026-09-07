$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library -OfflineTest
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\bounded-loop-'+[guid]::NewGuid().ToString('N'))));[void][IO.Directory]::CreateDirectory($root);$job=[pscustomobject]@{target=$root};$checks=0
function Accept($text){$null=Test-AgentRobin $text $root $job;$script:checks++}
function Reject($text,$prefix){$message='';try{$null=Test-AgentRobin $text $root $job}catch{$message=$_.Exception.Message};if($message -notlike ($prefix+':*')){throw ('Unexpected result: '+$message)};$script:checks++}
$count=[IO.File]::ReadAllText((Join-Path $PSScriptRoot '..\catalog\flows\bounded-loop\default.robin'))
$sum=[IO.File]::ReadAllText((Join-Path $PSScriptRoot '..\catalog\flows\bounded-loop\sum-index.robin'))
Accept $count;Accept $sum
Reject ($count.Replace('STEP 1','STEP 0')) ROBIN_LOOP
Reject ($count.Replace('STEP 1','STEP -1')) ROBIN_LOOP
Reject ($count.Replace('FROM 1 TO 3','FROM 3 TO 1')) ROBIN_LOOP
Reject ($count.Replace('TO 3','TO 1001')) ROBIN_LIMIT
Reject ($count.Replace('    Variables.IncreaseVariable Value: NewVar2 IncrementValue: 1','    SET LoopIndex TO 0')) ROBIN_LOOP
Reject ($count.Replace('Value: NewVar2','Value: LoopIndex')) ROBIN_LOOP
Reject ('LOOP Index FROM 1 TO 2 STEP 1'+"`n    LOOP Index FROM 1 TO 2 STEP 1`n    END`nEND") ROBIN_LOOP
Reject ('LOOP Outer FROM 1 TO 100 STEP 1'+"`n    LOOP Inner FROM 1 TO 100 STEP 1`n    END`nEND") ROBIN_LIMIT
Reject ('LOOP Index FROM 1 TO 31 STEP 1'+"`n    WAIT 1`nEND") ROBIN_LIMIT
$quoted='$'+"'''text'''"
Reject ('SET Total TO '+$quoted+"`nVariables.IncreaseVariable Value: Total IncrementValue: 1") ROBIN_TYPE
Reject 'Variables.IncreaseVariable Value: Missing IncrementValue: 1' ROBIN_VARIABLE
Reject "SET Total TO 0`nVariables.IncreaseVariable Value: Total IncrementValue: Missing" ROBIN_VARIABLE
Reject 'SET Total TO 99999999999999999999999999999999' ROBIN_NUMBER
Reject ("SET Total TO 0`nLOOP Index FROM 1 TO 2 STEP 1`n    SET Total TO "+$quoted+"`nEND") ROBIN_TYPE
Reject "LOOP Index FROM 1 TO 2 STEP 1`nELSE`nEND" ROBIN_BLOCK
Accept ("LOOP Index FROM 1 TO 2 STEP 1`n    SET Created TO "+$quoted+"`nEND`nIF Created = "+$quoted+" THEN`n    WAIT 0`nEND")
$output=ConvertTo-AgentRobinLiteral (Join-Path $root 'artifacts\output.txt')
Reject ("SET Total TO 0`nLOOP Index FROM 1 TO 2 STEP 1`n    File.WriteText File: "+$output+" TextToWrite: Total AppendNewLine: False IfFileExists: File.IfFileExists.Append Encoding: File.FileEncoding.UTF8`nEND") ROBIN_LOOP
function Read-AgentAiCallTemplates {return [pscustomobject]@{robin='KNOWN_CALL';ai_call_id=('a'*32)}}
[IO.File]::WriteAllText((Join-Path $root 'aicall-templates.json'),'[]')
Reject "LOOP Index FROM 1 TO 2 STEP 1`n    KNOWN_CALL`nEND" ROBIN_LOOP
Write-Output "PASS: $checks bounded Robin loop checks; no PAD/Copilot invoked."
