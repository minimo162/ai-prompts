$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library -OfflineTest
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\number-conversion-'+[guid]::NewGuid().ToString('N'))));[void][IO.Directory]::CreateDirectory($root);$job=[pscustomobject]@{target=$root};$checks=0
function Accept($text){$null=Test-AgentRobin $text $root $job;$script:checks++}
function Reject($text,$code){$message='';try{$null=Test-AgentRobin $text $root $job}catch{$message=$_.Exception.Message};if($message -notlike ($code+':*')){throw ('Unexpected: '+$message)};$script:checks++}
$q='$'+"'''";$end="'''"
$prefix='SET Source TO '+$q+'12.5'+$end+"`n"
$convert="Text.ToNumber Text: Source Number=> Amount`n"
$format='Text.FromNumber Number: Amount DecimalPlaces: 2 UseThousandsSeparator: False FormattedNumber=> Formatted'
Accept ($prefix+$convert+$format)
Accept ([IO.File]::ReadAllText((Join-Path $PSScriptRoot '..\catalog\actions\text-to-number\decimal.robin')))
Reject $convert ROBIN_VARIABLE
Reject ("Variables.CreateNewList List=> Source`n"+$convert) ROBIN_TYPE
Reject ("SET Source TO 1`n"+$convert) ROBIN_TYPE
Reject $format ROBIN_VARIABLE
Reject ('SET Amount TO '+$q+'12.5'+$end+"`n"+$format) ROBIN_TYPE
Reject ($prefix+$convert+$format.Replace('DecimalPlaces: 2','DecimalPlaces: 99')) ROBIN_ACTION
Reject ($prefix+$convert+$format.Replace('UseThousandsSeparator: False','UseThousandsSeparator: True')) ROBIN_ACTION
Reject 'Text.ToNumber Text: 9999999999999999999999999999.5 Number=> Amount' ROBIN_NUMBER
Reject 'Text.ToNumber Text: NaN Number=> Amount' ROBIN_VARIABLE
Reject ($prefix+"LOOP Amount FROM 1 TO 2 STEP 1`n    "+$convert+"END") ROBIN_LOOP
Write-Output "PASS: $checks number-conversion contract checks; no PAD/Copilot invoked."
