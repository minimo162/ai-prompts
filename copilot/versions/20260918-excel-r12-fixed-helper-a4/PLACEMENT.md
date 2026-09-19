# 20260918-excel-r12-fixed-helper-a4 placement and runtime design

Route: `EX03-R12-FIXED-HELPER-COPILOT-A4`. This is local preparation only. If a later turn is
separately authorized, send `submitted-body.txt` unchanged and attach exactly
`knowledge/PAD-Robin-Fixed-Helper-A4-Bundle.txt`.

## Fixed runtime

| Role | Path | SHA-256 |
| --- | --- | --- |
| unchanged helper | `C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\probes\ex03-r12-fixed-helper\EX03-R12-Fixed-StringTransfer.ps1` | `08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135` |
| A4 verifier invocation | `C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\probes\ex03-r12-fixed-helper-a4\invocation.json` | `5c5a2008f55296a48f63fa65178aab971e4212455bb2af58e33149bdcaec40d8` |
| A4 launcher | `C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\probes\ex03-r12-fixed-helper-a4\launcher.ps1` | `a286179f8fb7f8febc87f1915cf10965ee0a50769251ecb17573c00926c174d5` |
| fixed work | `C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\runs\EX03-attempt1\work.xlsx` | verifier preplaces the fixed request copy |
| A4 JSON root | `C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\runs\EX03-attempt1\a4-helper-json` | verifier precreates; flow writes 7 source JSON files and mode.json |
| fixed output | `C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\runs\EX03-attempt1\照合結果.xlsx` | must be absent before the flow; C02 guards and C10 SaveAs uses this path |

The invocation targets the same work opened by C05. C04 writes into the exact
json_root read by the unchanged helper through C06. Exact-success plus NORMAL
must pass before five numeric writes or SaveAs. Readback and comparison then use
the fixed two rectangles and twelve positions in `wiring-spec.json`.

No complete Robin, Copilot response, PAD/Excel run, acceptance result, or grader
values were created for A4.
