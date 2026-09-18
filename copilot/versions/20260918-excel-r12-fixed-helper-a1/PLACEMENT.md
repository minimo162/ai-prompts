# 20260918-excel-r12-fixed-helper-a1 placement and generation boundary

Candidate route: `EX03-R12-FIXED-HELPER-COPILOT-A1`. This is a local non-live preparation. It is not
formal EX03-r12 acceptance and inherits no T2 PASS.

## Verifier preplacement

Before a separately authorized Copilot send, the verifier places or confirms
these existing files. Copilot must not create or modify them.

| Role | Exact path | Required SHA-256 |
| --- | --- | --- |
| helper | `C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\probes\ex03-r12-fixed-helper\EX03-R12-Fixed-StringTransfer.ps1` | `08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135` |
| fixed invocation | `C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\probes\ex03-r12-fixed-helper\trials\EX03-R12-FIXED-HELPER-P1-T1\invocation.json` | `92ea864a7e43cec61b4215592a3bae9b8b31109af4e18d3ff0a79dcb15fc5ad6` |

The invocation fixes `work.xlsx`, the JSON handoff directory, seven text
targets, and their routing. Its dedicated runtime takes precedence over the
frozen request's `runs\EX03-attempt1` work/output paths for this alternate route.
This candidate therefore does **not** test automatic generation of execution
configuration from a Japanese request and does not claim formal request-path
compliance.

The verifier also prepares the fixed template copy at the invocation's
`target_workbook`, confirms that the dedicated output is absent, and retains the
unchanged input fixtures, request, spec, and expected records.

## Copilot input and generated scope

If a later goal authorizes one send, use the unchanged fixed EX03 request,
the complete `agent-instructions.txt`, and attach exactly
`knowledge/PAD-Robin-Fixed-Helper-Bundle.txt` from this candidate ID.

Copilot generates only:

- the existing-output guard and input/JSON/work setup before RunScript;
- one RunScript containing the bundle's fixed launcher source;
- the exact-success/NORMAL gate, numeric writes, SaveAs, close/reopen, and
  twelve value/type comparisons after RunScript.

Copilot does not generate the helper body, invocation JSON, fixture contents,
expected values, or verifier comparisons. It copies the fixed launcher including
the verifier-owned SHA literals, but does not derive or change those literals.

## Validator-only references

- fixed launcher: `catalog/acceptance/issue38/probes/ex03-r12-fixed-helper/trials/EX03-R12-FIXED-HELPER-P1-T1/launcher.ps1` / `1e9750385455999460e9b1dce754e2a649d4837ae1939cd444376fc360a25ee1`
- executed T2 PAD re-copy: `catalog/acceptance/issue38/probes/ex03-r12-fixed-helper/trials/EX03-R12-FIXED-HELPER-P1-T2/pad-recopy-before-run.robin` / `da54e5f4388cd0bb896ee00e534e9d81a444f5b950ac1f1bf006f8ea788ad4aa`

The T2 re-copy is not an attachment or teaching answer. It is retained only for
post-generation structure and launcher comparison. The teaching fragments in
the bundle use a different one-input 2x2 scenario and contain neither the fixed
EX03 completed answer nor grading values.

## Current boundary

Copilot send, PAD save/re-copy, PAD/Excel Run, candidate acceptance, full
regression, and GitHub write are all not run by this preparation.
