$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../App.ps1') -Mode Library -OfflineTest
Add-Type -AssemblyName System.IO.Compression
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('../.work/document-observation-'+[guid]::NewGuid().ToString('N'))))
[void][IO.Directory]::CreateDirectory((Join-Path $root 'artifacts'))
$checks=0
function Check($condition,$message){if(-not $condition){throw $message};$script:checks++}
function Reject($action){$failed=$false;try{& $action|Out-Null}catch{$failed=$true};Check $failed 'Expected document inspection rejection'}
function Package([string]$Name,$Parts){
 $Parts=$Parts.Clone();$type=[IO.Path]::GetExtension($Name).ToLowerInvariant()
 $main=@{'.docx'=@('word/document.xml','application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml');'.xlsx'=@('xl/workbook.xml','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml');'.pptx'=@('ppt/presentation.xml','application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml')}[$type]
 $Parts['[Content_Types].xml']='<Types><Override PartName="/'+$main[0]+'" ContentType="'+$main[1]+'"/></Types>'
 $Parts['_rels/.rels']='<Relationships><Relationship Id="main" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="'+$main[0]+'"/></Relationships>'
 $path=Join-Path $root ('artifacts\'+$Name);$stream=[IO.File]::Open($path,[IO.FileMode]::CreateNew);$zip=New-Object IO.Compression.ZipArchive($stream,[IO.Compression.ZipArchiveMode]::Create)
 try{foreach($part in $Parts.GetEnumerator()){$entry=$zip.CreateEntry($part.Key);$writer=New-Object IO.StreamWriter($entry.Open(),(New-Object Text.UTF8Encoding($false)));try{$writer.Write([string]$part.Value)}finally{$writer.Dispose()}}}finally{$zip.Dispose();$stream.Dispose()};return $path
}
$word='<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Alpha 100%</w:t><w:tab/><w:t>Beta</w:t><w:br/><w:t>Gamma</w:t></w:r></w:p></w:body></w:document>'
$docx=Package 'result.docx' @{'word/document.xml'=$word}
$doc=Get-AgentDocumentContent $docx
$value=$doc.content|ConvertFrom-Json
Check ($value.parts[0].text -ceq "Alpha 100%`tBeta`nGamma`n") 'Word text/separators must be preserved'
Check ($doc.kind -ceq 'docx_text' -and $doc.complete) 'Word inspection scope'
Check ($doc.sha256 -ceq (Get-AgentHash $docx)) 'Inspection binds to exact snapshot bytes'
$observed=Get-AgentObservedArtifacts ([pscustomobject]@{status='success';artifacts=@($docx)}) $root
Check ($observed[0].inspection_kind -ceq 'docx_text' -and $observed[0].text_status -ceq 'complete') 'Binary artifact gets scoped text evidence'
Check ($observed[0].inspection_limitations -like '*layout*') 'Unverified layout remains explicit'
$limited=Get-AgentObservedArtifacts ([pscustomobject]@{status='success';artifacts=@($docx)}) $root 4
Check ($limited[0].truncated -and $limited[0].text_status -ceq 'truncated') 'Document samples honor the shared character budget'
$bad=Package 'external.docx' @{'word/document.xml'=$word;'word/_rels/document.xml.rels'='<Relationships><Relationship Id="r1" Target="https://example.invalid/template" TargetMode="External"/></Relationships>'}
Reject {Get-AgentDocumentContent $bad}
$macro=Package 'macro.docx' @{'word/document.xml'=$word;'word/vbaProject.bin'='not executable test data'}
Reject {Get-AgentDocumentContent $macro}
$dtd=Package 'dtd.docx' @{'word/document.xml'='<!DOCTYPE x [<!ENTITY example "expanded">]><x>&example;</x>'}
Reject {Get-AgentDocumentContent $dtd}
$field=Package 'field.docx' @{'word/document.xml'=$word.Replace('<w:t>Alpha 100%</w:t>','<w:instrText>DDEAUTO test-only</w:instrText>')}
Reject {Get-AgentDocumentContent $field}
$connection=Package 'connection.docx' @{'word/document.xml'=$word;'customXml/item1.xml'='<connection/>'}
Reject {Get-AgentDocumentContent $connection}
$sheet='<worksheet><sheetData><row><c r="A1" t="s"><v>0</v></c><c r="B1" t="inlineStr"><is><t>100%</t></is></c></row></sheetData></worksheet>'
$book=@{'xl/workbook.xml'='<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Data" r:id="r1"/></sheets></workbook>';'xl/_rels/workbook.xml.rels'='<Relationships><Relationship Id="r1" Target="worksheets/sheet1.xml"/></Relationships>';'xl/worksheets/sheet1.xml'=$sheet;'xl/sharedStrings.xml'='<sst><si><t>Alpha</t></si></sst>'}
$xlsx=Package 'result.xlsx' $book;$data=(Get-AgentDocumentContent $xlsx).content|ConvertFrom-Json
Check ($data.sheets[0].name -ceq 'Data' -and $data.sheets[0].cells[0].value -ceq 'Alpha' -and $data.sheets[0].cells[1].value -ceq '100%') 'Spreadsheet relationships and text forms'
$book['xl/worksheets/sheet1.xml']=$sheet.Replace('<v>0</v>','<f>WEBSERVICE("https://example.invalid")</f><v>0</v>')
$formula=Package 'formula.xlsx' $book;Reject {Get-AgentDocumentContent $formula}
$pptx=Package 'result.pptx' @{'ppt/presentation.xml'='<p:presentation xmlns:p="urn:p" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId r:id="second"/><p:sldId r:id="first"/></p:sldIdLst></p:presentation>';'ppt/_rels/presentation.xml.rels'='<Relationships><Relationship Id="first" Target="slides/slide1.xml"/><Relationship Id="second" Target="slides/slide2.xml"/></Relationships>';'ppt/slides/slide1.xml'='<slide><p><t>One</t></p></slide>';'ppt/slides/slide2.xml'='<slide><p><t>Two</t></p></slide>'}
$slides=(Get-AgentDocumentContent $pptx).content|ConvertFrom-Json
Check ($slides.slide_count -eq 2 -and $slides.slides[0].text -ceq "Two`n" -and $slides.slides[1].text -ceq "One`n") 'Use presentation relationship order, not ZIP entry order'
$pdf=Join-Path $root 'artifacts\result.pdf';[IO.File]::Copy((Join-Path $PSScriptRoot '../catalog/fixtures/pdf/source-a.pdf'),$pdf)
Reject {Get-AgentObservedArtifacts ([pscustomobject]@{status='success';artifacts=@($pdf)}) $root}
$dir=Join-Path $root 'control\inspection';[void][IO.Directory]::CreateDirectory($dir);$readback=Join-Path $dir 'native.txt'
[IO.File]::WriteAllText($readback,'Native PDF text',(New-Object Text.UTF8Encoding($true)))
$binding=@{path=$pdf;role='output';text_path=$readback;text_sha256=Get-AgentHash $readback;file_sha256=Get-AgentHash $pdf}
$observation=[pscustomobject]@{status='success';artifacts=@($pdf);document_inspections=@($binding)}
$result=Get-AgentObservedArtifacts $observation $root
Check ($result[0].content -ceq 'Native PDF text' -and $result[0].inspection_kind -ceq 'pdf_text') 'PDF readback requires the exact controller binding'
[IO.File]::WriteAllText($readback,'changed');Reject {Get-AgentObservedArtifacts $observation $root}
$binding.text_sha256=Get-AgentHash $readback;$binding.text_path=Join-Path $root 'outside.txt';[IO.File]::WriteAllText($binding.text_path,'changed')
Reject {Get-AgentObservedArtifacts $observation $root}
$long=Join-Path $root 'artifacts\large.docx';$f=[IO.File]::Create($long);try{$f.SetLength(33554433)}finally{$f.Dispose()};Reject {Get-AgentDocumentContent $long}
$stagedPlan=@{documents=@{reads=@{$docx=$true}}};$code='Word.LaunchWord.LaunchAndOpen Path: '+(ConvertTo-AgentRobinLiteral $docx.Replace('\','/'))+' Visible: True ReadOnly: True Instance=> W'
$execution=Get-AgentDocumentExecutionRobin $code $stagedPlan $root
Check ($execution -like '*control*inputs*') 'Slash aliases must not bypass input staging'
$stagedPlan.documents.source_hashes=@{$docx=('0'*64)}
Reject {Get-AgentDocumentExecutionRobin $code $stagedPlan $root}
$stagedPlan.documents.source_hashes=@{$docx=(Get-AgentHash $docx)}
$literalLine='SET Label TO '+(ConvertTo-AgentRobinLiteral $docx)
$execution=Get-AgentDocumentExecutionRobin ($code+"`r`n"+$literalLine) $stagedPlan $root
Check ($execution.Contains($literalLine)) 'Staging must not replace identical path text in business literals'
Check (Test-AgentArtifactOpenSupported $observed[0]) 'Scoped DOCX evidence enables the result button'
$csvPath=Join-Path $root 'artifacts\table.csv';[IO.File]::WriteAllText($csvPath,"Name,Amount`r`nAlpha,-12.5`r`n",(New-Object Text.UTF8Encoding($true)))
$csvArtifact=[pscustomobject]@{path=$csvPath;sha256=Get-AgentHash $csvPath;text_status='complete';inspection_kind='utf8_text'}
Assert-AgentArtifactOpenContent $csvArtifact;$checks++
[IO.File]::WriteAllText($csvPath,"Name,Amount`r`nAlpha,=1+1`r`n",(New-Object Text.UTF8Encoding($true)));$csvArtifact.sha256=Get-AgentHash $csvPath
Reject {Assert-AgentArtifactOpenContent $csvArtifact}
Write-Output "PASS: $checks document observation checks; synthetic package/readback boundaries, no live apps."
