# EX03 fixed-helper mechanical Robin builder P1

This is a local, fixed-EX03 prototype separate from the A4 Copilot generation
route. It does not create A5, send to Copilot, edit the A4 response, or run PAD
or Excel.

## Inputs and output

`Build.py` reads the existing A4 files without modifying them:

- `wiring-spec.json` (`c62ec6951bdd36e895acfc937d7a1f390e75e8d984b26a9531cc2c88d970f58c`)
- A4 bundle C01-C12 (`62695ca3c007ab291732657ddaeca66723a57115d151efc7b1730ef5341c514c`)
- `assembly-rules.json` (`57305c13d9bff292d7c7c2bc3e3152bcd75b85fd1bd800679df1671f79c7bc6e`)
- unchanged helper, A4 invocation, and original A4 launcher

The fixed launcher is read from `launcher.ps1`, encoded into the captured C06
wrapper, decoded again, restored with one terminal LF, and required to match
SHA-256 `a286179f8fb7f8febc87f1915cf10965ee0a50769251ecb17573c00926c174d5`.

The committed output is
`generated/EX03-R12-FIXED-HELPER-MECHANICAL-P1.robin`, SHA-256
`3d9c1671a5debc6f0247cef8c5e0d414dc07246a7cb7ce0ac6245fb860967e47`.
It is UTF-8/LF with a terminal LF.

## Use

From the repository root, reproduce both the Robin and `verification.json` in
memory and require byte identity:

```powershell
python catalog/acceptance/issue38/probes/ex03-r12-fixed-helper-mechanical-builder/Build.py --check
```

`--write` is only for initializing an absent output. It uses exclusive create
and refuses to overwrite either committed artifact.

Run the focused positive and negative tests with:

```powershell
python tests/Test-Issue38Ex03FixedHelperMechanicalBuilder.py
```

The builder validates all fixed coordinates and variable references before it
renders any output. Missing mappings, duplicate sources or targets, and a
modified launcher are rejected before output creation. Replacements are limited
to the parameter names declared in `ALLOWED_PARAMETERS`; component and assembly
rule SHAs are checked first.

## User-operation impact

For local verification, the only added operation is the `--check` command
above. If a later, separately authorized PAD trial uses this artifact, the user
would still need to import the unmodified Robin into the dedicated flow and
perform the existing save/re-copy/run gates. None of those live operations is
performed or accepted here.

## Scope boundary

The non-live result proves deterministic mechanical assembly and the static
8 JSON-file writes, 5 numeric writes, 2 readback rectangles, and 12 JSON
value/type comparisons. It does not prove PAD import syntax, PAD save/re-copy,
helper execution through this generated Robin, Excel results, Copilot
generation, or EX03 acceptance. The fixed expected-value file is read only as
bytes for a SHA-256 preservation check; its grader values are neither parsed
nor emitted by the builder.
