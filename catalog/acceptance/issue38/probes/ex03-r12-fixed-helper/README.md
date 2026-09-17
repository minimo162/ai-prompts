# EX03 r12 fixed-helper path prototype

This directory is a separate, local-only non-live path. It does not replace
`20260917-excel-r12`, the existing inline-RunScript usage, or any frozen request,
expected value, evidence, or acceptance decision.

## Placement

Keep all three runtime files at this exact directory on the current verifier
machine:

```text
C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\probes\ex03-r12-fixed-helper\
  EX03-R12-Fixed-StringTransfer.ps1
  invocation.json
  launcher.ps1
```

Before any future PAD use, the verifier must calculate SHA-256 from the local
bytes and compare it with `manifest.json`. The launcher contains the same fixed
helper and invocation SHA-256 values. Neither value may be taken from a Copilot
response or changed to match generated output.

## Intended future use

1. Preserve the existing flow order: output guard, source reads, seven JSON
   payload files plus `mode.json`, then open the verifier-prepared work copy.
2. Use the exact contents of `launcher.ps1` as the Run PowerShell Script body;
   do not embed the 200-line helper body in generated Robin.
3. The launcher checks file presence and both fixed hashes before invoking the
   helper. A missing or changed file exits before the helper can access Excel.
4. Only the existing exact success JSON may pass to the numeric-write and
   SaveAs gates. Missing or different output remains a failure.

The helper reads values only from the existing JSON files. Fixed EX03 routing
is isolated in verifier-owned `invocation.json`; the helper itself contains no
fixed EX03 path, sheet, cell, source value, or expected value. The r12 teaching
bundle is unchanged and does not include this invocation.

## Current verification boundary

The real helper has only been parsed and inspected statically. The launcher is
exercised with harmless temporary stubs that can create only a marker file.
There is no real helper execution, Excel COM access, Copilot generation, PAD
save/re-copy/Run, artifact comparison, or EX03 acceptance in this prototype.
Execution policy, permissions, and existing safety guards are unchanged.
