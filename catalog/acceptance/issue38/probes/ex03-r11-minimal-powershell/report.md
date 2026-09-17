# EX03 r9/r10 pipeline boundary and r11 local source

## Conclusion

Both live failures are already present in the earliest preserved response-code representation. r9's complete 197-line rendered code DOM is byte-identical to its raw code-copy. r10's copied full response contains its raw code-copy byte-for-byte. Later code-copy, repository save, Robin action extraction, and PAD-string decoding preserve the two broken expressions; they do not remove the type qualifiers.

The known-good independent teaching Robin decodes exactly to its support script and parses with 0 errors. An intentionally corrupted copy preserves both corruptions through extraction/decoding and fails the PowerShell parser with 19 errors. The extractor therefore requires no repair.

## Local successor change

The unsent `20260917-excel-r11` local source changes the actual embedded implementation, not only an inspection instruction. It removes the three fragile static-member fragments and reduces the embedded script from 88 to 58 lines (5011 to 3300 UTF-8 bytes without the final newline). It keeps exact normalized FullName selection, source and destination string checks, original NumberFormat restoration in an inner `finally`, empty PrefixCharacter, non-formula checks, and COM cleanup.

Before:

```powershell
if ([string]::Equals([IO.Path]::GetFullPath([string]$candidate.FullName), $targetPath, [StringComparison]::OrdinalIgnoreCase)) {
if ($afterPrefixCharacter -cne $beforePrefixCharacter -or -not [string]::IsNullOrEmpty($afterPrefixCharacter)) {
```

After:

```powershell
$targetPath = [IO.Path]::GetFullPath($targetPath)
if ([IO.Path]::GetFullPath([string]$candidate.FullName) -ieq $targetPath) { $matches += $candidate }
if ([string]$cell.PrefixCharacter -cne '') { throw (...) }
```

This record is local preparation only. Copilot send, EX03 integrated execution, and GitHub write are all 0. PAD save/re-copy and the dedicated synthetic run remain pending at this point.
