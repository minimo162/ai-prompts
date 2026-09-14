[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
& node (Join-Path $PSScriptRoot 'Test-T10ByteComparator.mjs')
if ($LASTEXITCODE -ne 0) { throw 'T10 byte comparator failed.' }
