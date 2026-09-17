# EX03-r12-G1 generation-corruption investigation

## Scope and preserved state

This record analyzes only artifacts already committed at checkpoint
`debc1b9b84157b11693afc38d47bce844684473f`. No Copilot request, browser
capture, PAD/Excel operation, generated-payload edit, successor candidate, full
regression, or GitHub write was performed.

The existing decision
`FAIL_GENERATED_ROBIN_MISMATCH_AND_POWERSHELL_PARSE_ERROR_STOP_BEFORE_PAD`
remains valid. The original `generation-safety-audit.json` is preserved; this
record qualifies its four-error parser attribution without rewriting it.

## Earliest preserved stage containing the corruption

The fixed source artifacts contain the required token once and do not contain
the corrupt token:

- sent bundle SHA-256
  `ddee43a1eddc966f62095b63a23b135df184f3cbe0ded635cbf72520e6744b97`:
  `ConvertTo-Json -Compress` = 1, `$result | press` = 0;
- prepared normal Robin SHA-256
  `7bde8bb20bb7f347c97722d77a4141bf8348bb40d97aaca435e01998e8b9d3a3`:
  required = 1, corrupt = 0;
- standalone teaching script SHA-256
  `314b687ce8d1848558d80340b414d32c8d3baca2c5e699541db0eb062f96ba1c`:
  required = 1, corrupt = 0.

| Preserved stage | Direct observation | Required token | Corrupt token | Result |
| --- | --- | ---: | ---: | --- |
| Response original | `copilot-response.visible.txt`, SHA-256 `4bdb76e57c1bd023b07589e7a4cc6bcaad3e8a729eb4f62d9951a61bd0eeea7f`, visible line 383 / code line 177 | 0 | 1 | corruption already present |
| Code copy | `code-copy.html`, SHA-256 `0cf545692d75d163b7c87cc5c6f29c99d4d459136fc54d2d483d890ed19af821`; HTML-decoded 272 code lines have canonical SHA-256 `64b6c7de822a448a4696910cc683c77ebfc57920c91aa966851947e136b5a366` | 0 | 1 | copied content preserves response code |
| Saved Robin | `generated.robin`, 272 lines, SHA-256 `64b6c7de822a448a4696910cc683c77ebfc57920c91aa966851947e136b5a366` | 0 | 1 | byte-identical to HTML-decoded code copy |
| Correctly extracted script | r12 prefix/suffix extraction plus observed Robin escape decoding, 137 lines, SHA-256 `8748c1265597e0e422d3c7e725a16e26bb470b561fb9593c2836ba6bfe8963ee`, script line 137 | 0 | 1 | extraction preserves saved content |

The missing fragment is therefore first observable in the preserved response
original. It was not introduced by code copying, local saving, or script
extraction. At the acceptance-pipeline level this is a generated-response
failure. The available artifacts do not distinguish model token generation
from Microsoft 365 response assembly/rendering, so that internal boundary and
the reason for the particular `press` remainder are unconfirmed.

Expected teaching code (`prepared normal` Robin line 181 / teaching script
line 141):

```powershell
[Console]::Out.Write([string]($result | ConvertTo-Json -Compress))
```

Response, copied and saved code (Robin code line 177), then correctly extracted
script line 137:

```powershell
[Console]::Out.Write([string]($result | press)
```

This change has two separate properties:

1. `ConvertTo-Json -Compress` was replaced by `press`. Command discovery is not
   a PowerShell parser check, and the payload was not executed, so no runtime
   claim about `press` is made.
2. One of the two closing parentheses was also lost. That is the actual syntax
   error in the correctly extracted generated script.

## The four recorded parser errors

`generation-safety-audit.json` used
`Prepare-Issue38Ex03R8IndependentSource.py::extract_action()`. That routine
blindly removes four characters from every continuation line. The current r12
Robin continuation lines are not all prefixed with four flow-indent spaces, so
the extraction changed valid script text before parsing.

The four errors recorded by that old path are:

| # | ErrorId | Line:column | Token | Code supplied to parser | Classification |
| ---: | --- | --- | --- | --- | --- |
| 1 | `MissingEndParenthesisInExpression` | 137:43 | empty | `sole]::Out.Write([string]($result | press)` | contains the real missing `)`, but `[Con` was also removed by the extractor |
| 2 | `MissingEndCurlyBrace` | 133:5 | `{` | `lly {` | extractor artifact: `finally {` lost `fina` |
| 3 | `MissingEndCurlyBrace` | 126:3 | `{` | `h {` | extractor artifact: `catch {` lost `catc` |
| 4 | `MissingEndCurlyBrace` | 9:1 | `{` | `{` | extractor artifact: `try {` lost `try ` |

Applying exactly that old extraction and parser to the uncorrupted prepared
teaching Robin reproduces the same three curly-brace errors at 137:5 (`lly {`),
130:3 (`h {`), and 9:1 (`{`). This control proves those three errors are not
generated-payload defects.

Using the r12 builder's non-deindenting
`Build-Issue38Ex03CandidateR12.py::embedded_script()` for both Robins, followed
by the same `parse_powershell()` parser, gives:

- generated Robin: one error,
  `MissingEndParenthesisInMethodCall`, line 137, column 47, empty token, code
  `[Console]::Out.Write([string]($result | press)`;
- prepared teaching Robin: zero errors; its extracted 141-line script SHA-256
  is `9dcb0c6d86c94c2be32e95d1312343b8594ab7734844652b93fe3019d36146c5`
  and equals the standalone teaching script after removing only its final LF.

Thus the true generated script has one syntax error, not four. The separate
content/fidelity defect (`ConvertTo-Json -Compress` becoming `press`) remains
and independently keeps the r12 result failed.

## Four blank-line deletions

All four deleted lines are empty lines inside the embedded script. They contain
no string characters or PowerShell tokens, and the adjacent non-empty lines
remain separated by a newline.

| Prepared Robin line | Teaching script line | Before / after the empty line | Effect |
| ---: | ---: | --- | --- |
| 67 | 27 | payload type loop / `$targetPath = ...` | line-fidelity failure only |
| 123 | 83 | inner `finally` close / `if ($null -ne $writeError)` | line-fidelity failure only |
| 142 | 102 | write-error branch close / value-type check | line-fidelity failure only |
| 156 | 116 | write loop close / NORMAL result branch | line-fidelity failure only |

Deleting only these four empty lines from the uncorrupted teaching control and
running the same static parser produces zero errors. They shift subsequent line
numbers and violate the required exact adaptation, but do not change string
content, join tokens, or cause the generated script's syntax error.

## Confirmed cause boundary

Confirmed:

- the sent same-version source contains the required code;
- the preserved rendered response already contains the corrupt code and four
  missing empty lines;
- the HTML code copy and saved Robin are exact for the 272 copied code lines;
- correct extraction does not introduce or remove the corrupt fragment;
- the old four-error count includes three extraction artifacts;
- the correctly extracted generated payload has one missing-parenthesis parser
  error plus the independent command-fragment fidelity defect.

Not confirmed:

- whether corruption occurred in model generation or later Microsoft 365
  response assembly/rendering;
- why `press` was emitted;
- any general clipboard, browser, or transport behavior outside this captured
  response.

## One minimal successor design (proposal only)

Do not ask Copilot to reproduce the 141-line fixed PowerShell body. Distribute
one verifier-controlled, versioned `.ps1` helper containing the mechanically
adapted fixed EX03 string-transfer logic, and make generated Robin contain only
the existing data-read/JSON-handoff actions plus a short SHA-gated invocation
of that helper.

Required distribution:

1. the fixed helper `.ps1`, stored outside the Copilot teaching bundle and
   frozen by full SHA-256 in the candidate manifest;
2. the same-version instruction/bundle describing only the helper interface
   and the short invocation contract, not reproducing the helper body;
3. a manifest entry fixing helper path, SHA-256, expected stdout gate, and the
   rule that absence/SHA mismatch stops before workbook mutation.

Use sequence:

1. the verifier places the helper at the fixed local path and independently
   checks its full SHA-256;
2. Copilot generates the reduced Robin once; its unmodified copy must match the
   allowed data-slot adaptation and exact short launcher;
3. PAD save/re-copy must match before execution;
4. the launcher rechecks the helper SHA, invokes it, and the existing exact
   success gate controls numeric writes and SaveAs.

Acceptance impact:

- fixed request, target cells, values/types, expected output, original/outside
  cell/formula/format checks, two-Run limit, and stop rules do not change;
- helper presence and exact SHA become an additional precondition;
- helper missing/SHA mismatch and launcher mismatch are new fail-closed
  negatives that must be proven before an integrated run;
- the analyzer must use the same non-deindenting extraction for generated and
  teaching Robins so parser evidence describes the actual payload;
- no prior probe or r12 result transfers as acceptance for such a successor.

This is a design recommendation only. No helper, candidate version, instruction,
bundle, or acceptance requirement was created or changed in this investigation.
