# EX02-R5-G2 acceptance review

## Outcome

The separately authorized G2 cycle used the unchanged `20260915-excel-r5` instruction, bundle, request, fixtures, grader-only expected values, and acceptance contract. Normal M365 Copilot produced one 87-line Code Copy with no extra token. Its unmodified paste created 87 PAD actions, saved successfully, and re-copied exactly after line-ending normalization.

Both positive PAD runs completed the SaveAs, close, read-only reopen, and reread sequence. The twelve PAD JSON identity variables were visibly `True` in each run. The independent typed-transfer evidence maps every fixed source coordinate to its target coordinate and grader-only expected typed value; both runs are 12/12 with no mismatch. The two outputs differ as ZIP binaries but match semantically across 480 checked cells.

The separate negative changes only `Target A!D4` from numeric `12.5` to text `"12.5"`. Its rendered target range is byte-identical to Run2, while both typed verifiers detect exactly that one target mismatch. The positive Run2 output remains unchanged.

## Acceptance boundary

The Copilot-generated, unmodified PAD path passes within the fixed EX02 text/number scope. This does not generalize to blank, boolean, date, error, formula-result, object, another PAD version, or another PC. Neither the successful unit probe nor an external checker is substituted for the generated-flow run evidence.

Full EX02 acceptance remains false. The unchanged legacy oracle continues to report 558 differences: 48 row dimensions, 30 column dimensions, and 480 styles. The Excel-native supplemental comparison reports 480 style cells matching within its recorded scope, but it excludes dimensions and other required classes and therefore does not override the legacy gate.

## Primary evidence

- `live-send.json`, `generation-result.json`, `generation-safety-audit.json`
- `code-copy-raw.robin`, `generated.robin`, `pad-import-and-recopy.json`
- `run1/run.json`, `run1/typed-transfer.json`, `run1/comparison.json`, `run1/native-styles.json`
- `run2/run.json`, `run2/typed-transfer.json`, `run2/comparison.json`, `run2/native-styles.json`
- `two-run-comparison.json`
- `negative/build-evidence.json`, `negative/typed-transfer.json`, `negative/comparison.json`, `negative/native-styles-vs-positive.json`, `negative/render-equivalence.json`
- `protected-files-after.json`, `acceptance-status.json`, `verification.json`
