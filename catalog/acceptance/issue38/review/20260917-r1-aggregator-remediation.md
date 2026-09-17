# Independent review R1: acceptance aggregator remediation

## Scope and boundary

- Base commit: `3eadd54e3401f50d920918dec4b573db1536af7c`
- Changed scope: `tools/Finalize-Issue38Ex03R11FileAux.py` and its dedicated regression test only.
- No Copilot submission, PAD/Excel run, candidate version creation, fixed request or expected-value change, or GitHub write was performed.
- The frozen r11 evidence and all prior decisions remain records of their original observations.

The review attachment objects were not exposed to this task session. The four mutations described in R1 were therefore encoded directly as in-memory regressions without editing the preserved JSON files.

## Reproduction and correction

Before the correction, all four R1 mutations were incorrectly accepted while their top-level PASS/MATCH state remained present:

1. typed-transfer output SHA replaced with another value;
2. typed-transfer mappings replaced with an empty array;
3. effective-format output SHA replaced with another value;
4. effective-format bounds and difference-count objects replaced with empty objects.

The aggregator now derives the fixed EX03 contract from `spec.json` and `expected.json`, then validates required keys and binds every accepted record to the same case, Run, result workbook, fixed input files, mappings, coordinates, expected typed values, workbook bounds, and counts. Empty collections no longer pass through vacuous `all()` or empty-dictionary equality checks. The two-Run semantic record is also bound to both preserved artifacts.

The historical `EX02_EXCEL_EFFECTIVE_FORMAT_COMPARISON` kind string in the frozen native-format reports is retained. Those records are bound to EX03 by their fixed EX03 template/output paths and hashes, sheet set, and exact bounds rather than by rewriting original evidence.

## Verification contract

- Positive: the existing Run1 and Run2 records must both pass the corrected validator.
- Negative: each of the four R1 mutations must raise `ValueError`.
- Additional fail-closed coverage: missing required keys, wrong case/Run, wrong source/reference, wrong target coordinate, wrong two-Run artifact SHA, and missing two-Run checked-cell count must be rejected.
- Read-only: validation must leave all files in both preserved Run directories byte-identical.

## Frozen data identities

The following Git objects from the base commit are the preservation anchors and must remain unchanged by this remediation:

- r11 candidate tree `copilot/versions/20260917-excel-r11`: `ef3b9a1a3721e951363b3ce09858ec4098d5b158`
- FILE-AUX1 evidence tree: `249efc40b8b94901fc5ed65a5157f6dbffe4c6eb`
- formal r11-G1 tree: `f0dc62eb4ac786c5a07ada89ea5eba273e1246c2`
- fixed spec blob: `efa9b662d3ed007059645eb3ea86ef640efcaeb0`
- fixed expected-values blob: `6daac6896166afb3138cf6e6d7108584a957be7a`
- fixed EX03 request blob: `9ee08ff30b16ca2cbe4124ca96037b2409a121c0`

## R1 observations intentionally left open

These are outside this narrowly authorized correction and are not resolved by the aggregator change:

1. Seven JSON values are interpolated into PowerShell single-quoted literals. The actual PAD JSON encoding and apostrophe behavior remain unverified; the fixed evidence must not be generalized to arbitrary strings.
2. The generated Robin has no separately recorded RunScript-success/`ScriptError` gate before numeric writes and SaveAs. Whether a PowerShell `throw` always stops this PAD environment before save remains unverified.
3. The frozen r11 manifest records 87 LF-only lines for the PAD re-copy while the later measurement is 57. The frozen manifest is not overwritten; a correction record and any builder adjustment belong to a later separately authorized version.

