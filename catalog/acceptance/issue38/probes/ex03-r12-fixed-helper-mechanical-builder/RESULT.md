# EX03 fixed-helper mechanical builder P1 result

## Decision

`PASS_LIMITED_NON_LIVE_MECHANICAL_BUILD_ONLY_NOT_COPILOT_OR_PAD_ACCEPTANCE`

The fixed A4 WIRING SPEC, all C01-C12 component blocks, the four source-line
assembly rules, and the original fixed launcher produced one deterministic
Robin without using or editing the A4 Copilot-generated Robin.

Generated Robin SHA-256:
`3d9c1671a5debc6f0247cef8c5e0d414dc07246a7cb7ce0ac6245fb860967e47`

## Positive checks

- Regeneration with the unchanged spec is byte-identical for both the Robin and
  `verification.json`.
- JSON file writes: 8 (7 text sources plus mode).
- Numeric writes: 5.
- Typed readback rectangles: 2.
- Source/saved JSON value-type comparisons: 12.
- Every input cell, DataTable index, target cell, readback index, and comparison
  variable reference matches the fixed WIRING SPEC.
- The output guard precedes input reads, JSON writes, editable work open, and
  helper launch.
- SaveAs occurs once, only after both exact-success and NORMAL gates.
- Both failure branches close Work without SaveAs.
- The decoded launcher, after restoring its required terminal LF, matches fixed
  SHA-256 `a286179f8fb7f8febc87f1915cf10965ee0a50769251ecb17573c00926c174d5`.
- Focused mechanical-builder tests: 11/11 PASS.
- Existing A4 focused tests: 10/10 PASS.

## Negative checks

All negative inputs were rejected by `build()` before a caller could create an
output file:

- missing text mapping;
- missing comparison mapping;
- duplicate source mapping;
- duplicate target mapping;
- a single-token launcher alteration with a different SHA.

## Boundary

Copilot sends, PAD save/re-copy, PAD runs, Excel runs, and GitHub writes are all
zero. Full regression was not run. This result does not establish PAD import,
runtime behavior, Copilot generation, or EX03 acceptance.
