$ErrorActionPreference='Stop'
# Compile the production native adapter, but instantiate ONLY the fake backend.
Add-Type -Path @((Join-Path $PSScriptRoot '../tools/PadClipboardLease.cs'),(Join-Path $PSScriptRoot 'PadClipboardLeaseTests.cs')) -ReferencedAssemblies System.Windows.Forms
$count=[PadClipboardLeaseTests]::Run()
"PASS: $count clipboard lease scenarios; native adapter compiled, no OS clipboard or PAD calls"
