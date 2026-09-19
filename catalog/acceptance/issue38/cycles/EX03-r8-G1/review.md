# EX03 r8 G1 live acceptance review

## Outcome

The single authorized normal-M365 Copilot send completed without refusal and produced one 197-line Robin candidate. The exact generated candidate was pasted once, unmodified, into a new dedicated Power Fx OFF PAD flow. PAD parsed it as 110 actions and 45 variables and saved it.

Acceptance stopped before Run1. The saved flow's re-copy was not byte-equivalent after line-ending normalization: 30 RunScript payload lines changed. Each generated single backslash before a square bracket became a doubled backslash in the PAD re-copy. Representative changes are:

```text
generated:         \[ordered\]@{ Source = \'Data1\[0\]\[0\]\'; ... }
PAD re-copy:       \\[ordered\\]@{ Source = \'Data1\\[0\\]\\[0\\]\'; ... }

generated:     $excel = \[Runtime.InteropServices.Marshal\]::GetActiveObject(...)
PAD re-copy:   $excel = \\[Runtime.InteropServices.Marshal\\]::GetActiveObject(...)
```

The authoritative r8 PAD-recopied teaching source contains bracket-only PowerShell expressions, for example `[ordered]`, `Data1[0][0]`, and `[Runtime.InteropServices.Marshal]`; it does not contain these generated backslashes. No generated text was repaired. No PAD run was requested.

## Fixed evidence

- generated Robin: `generated.robin`, SHA-256 `711bd5b3a5eb1cba48f6872cd5aa8f718ab3534de4d0e069d5fd1eb7b9d1ed89`
- raw PAD clipboard re-copy: SHA-256 `1707abd1a159bba8365d675582e6ee36578b8b50ccd482c6cc6d9157f6d259f6`
- LF-normalized PAD re-copy: `pad-recopy-before-run1.robin`, SHA-256 `3340cd988d6ed76dc249edc833be33869c530d0b37ddf223807ac86eaef9329f`
- full 30-line comparison: `pad-recopy-diff.json`
- protected files: 199 checked, 0 changed
- runtime output: absent
- work copy SHA equals template SHA: `881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21`

## Decision

EX03 r8 G1 is not accepted. Run1 and Run2 are `NOT_RUN` under the fixed stop rule. The existing-output live guard remains unconfirmed, and the legacy 558-difference failure remains preserved. No GitHub write was made.
