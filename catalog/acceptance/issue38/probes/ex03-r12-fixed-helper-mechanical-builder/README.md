# EX03 fixed-helper mechanical Robin builder P1

This is a local, fixed-EX03 prototype separate from the A4 Copilot generation
route. The builder does not create A5, send to Copilot, edit the A4 response,
or run PAD or Excel. Separately authorized live evidence, when present, is kept
under `trials/` and does not change that builder boundary.

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

For non-live local verification, the only added operation is the `--check`
command above. A separately authorized PAD trial still requires the unmodified
Robin in the dedicated flow and the existing save/re-copy/run gates. Such a
trial is recorded independently under `trials/`; its result is not part of the
builder's static acceptance claim.

### Live PAD preplacement: A4 json_root

Before a separately authorized live PAD Run, the verifier must read
`json_root` from the fixed A4 `invocation.json` and
`runtime.a4_json_root_absolute` from `wiring-spec.json`. The two absolute paths
must be identical and must resolve to the synthetic test runtime directory
`catalog/acceptance/issue38/runs/EX03-attempt1/a4-helper-json`.

If that fixed directory is absent, the verifier creates that directory only.
It must not delete existing files or change permissions. Before Run, the
verifier checks that all eight fixed destinations (`source-1.json` through
`source-7.json` and `mode.json`) have that directory as their parent, then
writes, reads back, and removes one uniquely named temporary probe. The
directory must be empty and writable afterward. The verifier also requires the
fixed output to be absent and `work.xlsx` to remain byte-identical to the fixed
template.

The verifier preplaces only the directory. The saved PAD flow creates the eight
JSON files during the Run; the verifier does not precreate or populate them.

## Scope boundary

The non-live result proves deterministic mechanical assembly and the static
8 JSON-file writes, 5 numeric writes, 2 readback rectangles, and 12 JSON
value/type comparisons. It does not prove PAD import syntax, PAD save/re-copy,
helper execution through this generated Robin, Excel results, Copilot
generation, or EX03 acceptance. The fixed expected-value file is read only as
bytes for a SHA-256 preservation check; its grader values are neither parsed
nor emitted by the builder.
