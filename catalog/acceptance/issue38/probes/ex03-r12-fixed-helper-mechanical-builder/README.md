# EX03 fixed-helper mechanical Robin builder P1

This is a local, fixed-EX03 prototype separate from the A4 Copilot generation
route. The builder does not create A5, send to Copilot, edit the A4 response,
or run PAD or Excel. Separately authorized live evidence, when present, is kept
under `trials/` and does not change that builder boundary.

## Current entry and limited acceptance (2026-09-19)

推奨アーキテクチャは「自然言語要求 → WIRING SPEC → validator → deterministic Robin builder → PAD」。現時点のWIRING SPECは**検証者管理**です。自然言語からWIRING SPECを自動生成・受入する部分は未検証で、任意の要求を自動実行できる入口ではありません。

The validator currently lives inside [Build.py](Build.py):
`validate_fixed_sources()` / `validate_wiring()` run before rendering, and
`audit_robin()` checks the assembled result. There is no separate general-purpose
validator CLI. Fixed A4 WIRING, captured C01-C12 components, assembly rules,
helper, invocation, and launcher are the inputs; the A4 Copilot output is not.

At evidence checkpoint `3d593a6ada96af805e7800c6a7daff7b3cfc479d`, this fixed
EX03 mechanical-builder path is **LIMITED_ACCEPTANCE_FIXED_EX03**:

| Existing evidence | Accepted observation |
|---|---|
| [LIVE2 result](trials/EX03-R12-FIXED-HELPER-MECHANICAL-P1-LIVE2/result.json) | One normal Run PASS |
| [LIVE3 normal result](trials/EX03-R12-FIXED-HELPER-MECHANICAL-P1-LIVE3/normal/result.json) | One fresh normal Run PASS; values/types/positions/effective format match LIVE2 |
| [LIVE3 output-guard result](trials/EX03-R12-FIXED-HELPER-MECHANICAL-P1-LIVE3/existing-output-guard/result.json) | One Run after normal full PASS; `OUTPUT_EXISTS_NO_RUN`, no write/helper/SaveAs branch entry, protected files unchanged |

These are two separate normal trials and one guard trial, not a relabelled
Copilot two-Run acceptance. Both normal trials cover the fixed 12 text/number
targets, 468 outside cells and formulas, 480 effective-format cells / 48 rows /
30 columns, original SHAs, and F6 text `100%` with original format, empty prefix,
and no formula. Guard type comparisons are `NOT_EVALUATED`.

[Current report](../../report.md) and [case matrix](../../case-matrix.json)
record the scope and fixed identities. A1-A3 refusals, A4 missing comparisons /
damaged launcher, and formal r12 FAIL remain separate. No Copilot-path PASS is
inherited by this builder, and these live results do not make Copilot generation
PASS. The original [non-live result](RESULT.md) and [verification](verification.json)
retain their original static-only decisions.

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

Before a separately authorized normal live PAD Run, the verifier must read
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

The separate LIVE3 existing-output guard trial deliberately retained the normal
output and its eight handoff files. That trial's [preflight](trials/EX03-R12-FIXED-HELPER-MECHANICAL-P1-LIVE3/existing-output-guard/preflight.json)
and [before/after hashes](trials/EX03-R12-FIXED-HELPER-MECHANICAL-P1-LIVE3/existing-output-guard/hashes-after-run.json)
define that exception; it is not permission to overwrite a collision.

## Scope boundary

The original non-live result proves deterministic mechanical assembly and the static
8 JSON-file writes, 5 numeric writes, 2 readback rectangles, and 12 JSON
value/type comparisons. Runtime limited acceptance comes only from the separate
LIVE2/LIVE3 evidence above. The fixed expected-value file is read only as
bytes for a SHA-256 preservation check; its grader values are neither parsed
nor emitted by the builder.

- The saved Robin has no independently observed stderr PAD variable; empty stderr is not proven.
- Only the fixed synthetic text/number cells and the 3x2 / 2x3 input rectangles are covered. Blank, Boolean, date, error, formula-result, object, other shapes, arbitrary strings, paths, PCs, and PAD/Excel versions are not accepted by extension.
- Natural-language-to-WIRING generation/acceptance and Issue #38's other cases remain outside this mechanical path's acceptance. Their prior scoped results remain in the case matrix.
- The old raw 558 FAIL records remain unchanged. Later effective-format comparisons report zero differences; raw serialization/comparison and effective formatting are separate judgments.
- This documentation decision does not close Issue #38 or change the fixed request, expected values, or formal delivery conditions.

## Placement decision and later tools entry

Keep the implementation at this path for now; do not move or duplicate it into
`tools/`. `Build.py` resolves the repository with `Path(__file__).resolve().parents[5]`
and fixes its output path here. [The focused tests](../../../../../tests/Test-Issue38Ex03FixedHelperMechanicalBuilder.py)
and [LiveTrial.py](LiveTrial.py) import this location; [Live3Trial.py](Live3Trial.py)
pins the builder SHA. Moving changes path resolution, while an independent copy
would create two implementation identities without live evidence for the second.

The history is retained at `fd2cc2c` (builder), `dc927db` (LIVE1 stop),
`f38a69d` (LIVE2), and `3d593a6` (LIVE3). A later formal tools entry can be a thin
wrapper that loads this single implementation, with explicit repository-root
handling and a separate review of path/byte identity and evidence links.
That wrapper is a proposal only: it is not implemented or accepted here, and
no historical SHA or trial record should be rewritten to introduce it.
