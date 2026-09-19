#!/usr/bin/env python3
"""Seal the local r11 cause analysis and bounded PAD validation evidence."""

from __future__ import annotations

from datetime import datetime
import difflib
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "catalog/acceptance/issue38/probes/ex03-r11-minimal-powershell"
VERSION = ROOT / "copilot/versions/20260917-excel-r11"

INPUTS = {
    "analysis": PROBE / "analysis.json",
    "old_script": ROOT
    / "copilot/versions/20260917-excel-r10/support/EX03-R10-Independent-FormatSandwich.ps1.txt",
    "new_script": PROBE / "independent-minimal-format-sandwich.ps1.txt",
    "prepared_robin": PROBE / "independent-candidate.robin",
    "pad_recopy": PROBE / "independent-pad-recopy.robin",
    "pad_capture": PROBE / "independent-pad-capture.json",
    "negative": PROBE / "broken-extraction-negative.robin",
    "synthetic_pad_capture": PROBE / "synthetic-pad-capture.json",
    "synthetic_preflight": PROBE / "synthetic-pad-run-preflight.json",
    "synthetic_run": PROBE / "synthetic-pad-run.json",
    "synthetic_artifact": PROBE / "synthetic-artifact-verification.json",
    "synthetic_result": PROBE / "runtime/result.xlsx",
    "manifest": VERSION / "manifest.json",
    "instruction": VERSION / "agent-instructions.txt",
    "bundle": VERSION / "knowledge/PAD-Robin-Knowledge-Bundle.txt",
    "r9_generated": ROOT / "catalog/acceptance/issue38/cycles/EX03-r9-G1/generated.robin",
    "r10_generated": ROOT / "catalog/acceptance/issue38/cycles/EX03-r10-G1/generated.robin",
    "legacy_558": ROOT
    / "catalog/acceptance/issue38/probes/matrix-write/two-run-result.json",
    "fixed_request": ROOT / "catalog/acceptance/issue38/requests/EX03.txt",
    "fixed_spec": ROOT / "catalog/acceptance/issue38/spec.json",
    "fixed_expected": ROOT / "catalog/acceptance/issue38/expected.json",
}

EXPECTED = {
    "analysis": "b6912024ac126928cdf5474d1d71d243c94ad523e3fc190a95086eb28b9e2255",
    "old_script": "65b86b0e5be4ec2da30e57a6bd858e395d1103da2d05ab2e7607362772d1dfd9",
    "new_script": "068e676d70c373a9cf8203d19f6154e38460f609c4fdf774dbef1528f68fc7ae",
    "prepared_robin": "d2cac7051bb54cba44edb61aba48a7af7b8db9d4962425a519f48a6d137d25de",
    "pad_recopy": "148267f09f53d74db1059cee823a4a2e159f2bbebfa249d3a25c996796fa765b",
    "pad_capture": "5123b133487219b29348c9fc27a75f5f56b2cd3885ca893fb4e84327a2fe0621",
    "negative": "ec1a8a7bf6a0bcb5390db362a6cb3502f947b8c2d11c3f6fe8e6e759dadd14c4",
    "synthetic_pad_capture": "fc50f1e98fb624f4bab7f38ea422bfc8fb3eb3c2e21190dba6fcaa6467342d22",
    "synthetic_preflight": "6590feab3d529e79080018c1258b2a54254927f769df6eaa526a916add9755d9",
    "synthetic_run": "43f792c1ec8fc387adb43e17b7e669b80b6c5ea7e45d6e03668e684785ac4b73",
    "synthetic_artifact": "1054e360275062293694426520af64eb9d50595a6cd06d1300d356ee5b37734d",
    "synthetic_result": "3f10c3ee8ca916f525bdcf881a959e3d5bd8f22d2275dbae6af60b7b7a8e52ee",
    "manifest": "295306ea7e2e45da8cf77dec2784e94ea8ea8333da0df6a4000f83e9228b509e",
    "instruction": "bceb1c7e4f47c0cd6a92ad698d08108175002bffcaaaff492a309ca74a122aa1",
    "bundle": "2d95ce344ff66195061fd15010d13b75937888575fa2345fb543ae2115242f69",
    "r9_generated": "7a02ea0d073adde698578b8fa578f5701c728114ee55fbf20aa0ecdaaa32cb14",
    "r10_generated": "4946431c9ce47f986b841115fbfd328036356c4e12ae7cbe912c2bf06e2b1ed3",
    "legacy_558": "3f292fc60c2a4f50733e49a3b6e204a4fb568c73a0708ec1112fc73781766bbc",
    "fixed_request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "fixed_spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "fixed_expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_new(path: Path, value: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(value)


def main() -> dict[str, object]:
    actual = {name: sha256(path) for name, path in INPUTS.items()}
    if actual != EXPECTED:
        raise ValueError(f"Protected evidence/package hash mismatch: {actual}")

    analysis = json.loads(INPUTS["analysis"].read_bytes())
    pad_capture = json.loads(INPUTS["pad_capture"].read_bytes())
    synthetic_capture = json.loads(INPUTS["synthetic_pad_capture"].read_bytes())
    preflight = json.loads(INPUTS["synthetic_preflight"].read_bytes())
    run = json.loads(INPUTS["synthetic_run"].read_bytes())
    artifact = json.loads(INPUTS["synthetic_artifact"].read_text(encoding="utf-8-sig"))
    manifest = json.loads(INPUTS["manifest"].read_bytes())
    legacy = json.loads(INPUTS["legacy_558"].read_bytes())

    if pad_capture["result"] != "PASS_PAD_DESIGNER_SAVE_RECOPY_NO_EXECUTION":
        raise ValueError("Independent PAD re-copy failed")
    if synthetic_capture["result"] != "PASS_PAD_DESIGNER_SAVE_RECOPY_NO_EXECUTION":
        raise ValueError("Synthetic PAD re-copy failed")
    if preflight["status"] != "PASS_READY_FOR_ONE_DEDICATED_SYNTHETIC_PAD_RUN":
        raise ValueError("Synthetic preflight failed")
    if run["decision"] != "PASS_ONE_DEDICATED_SYNTHETIC_PAD_RUN":
        raise ValueError("Synthetic PAD run failed")
    if artifact["status"] != "PASS_EXTERNAL_ARTIFACT_CHECK_FOR_DEDICATED_PAD_PROBE":
        raise ValueError("Synthetic artifact verification failed")
    if not all(artifact["checks"].values()):
        raise ValueError("Synthetic artifact verification is incomplete")
    if manifest["version"] != "20260917-excel-r11":
        raise ValueError("Unexpected package version")
    if manifest["instruction_sha256"] != actual["instruction"]:
        raise ValueError("Instruction manifest mismatch")
    if manifest["bundle_sha256"] != actual["bundle"]:
        raise ValueError("Bundle manifest mismatch")
    if run["authorization_boundary"]["pad_runs_used"] != 1:
        raise ValueError("Unexpected dedicated PAD run count")
    if run["authorization_boundary"]["additional_pad_run"] != 0:
        raise ValueError("Unexpected additional dedicated PAD run")
    if not legacy.get("legacy_issue38_differences", {}).get("preserved", False):
        # Older records do not use a single schema. The known fixed count below
        # is still checked directly without rewriting the legacy record.
        encoded = json.dumps(legacy, ensure_ascii=False)
        if "558" not in encoded:
            raise ValueError("Legacy 558 failure is no longer present")

    old_lines = INPUTS["old_script"].read_text(encoding="utf-8").splitlines()
    new_lines = INPUTS["new_script"].read_text(encoding="utf-8").splitlines()
    diff = "\n".join(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="20260917-excel-r10/EX03-R10-Independent-FormatSandwich.ps1.txt",
            tofile="20260917-excel-r11/EX03-R11-Independent-Minimal-FormatSandwich.ps1.txt",
            lineterm="",
        )
    ) + "\n"
    write_new(PROBE / "r10-to-r11-script.diff", diff)

    variables = run["pad_observation"]["variables"]
    pad_boolean_names = [
        "ImmediateVsReopenedText",
        "ImmediateVsReopenedNumber",
        "SourceVsImmediateText",
        "SourceVsImmediateNumber",
        "SourceVsReopenedText",
        "SourceVsReopenedNumber",
    ]
    pad_boolean_checks = {name: variables[name] for name in pad_boolean_names}
    if not all(pad_boolean_checks.values()):
        raise ValueError("A PAD JSON comparison is false")

    acceptance = {
        "schema_version": 1,
        "recorded_at": datetime.now().astimezone().isoformat(),
        "probe_id": "EX03-R11-MINIMAL-POWERSHELL",
        "base_commit": "ac90b0943d2ff4e1172c23712ef49fe93787b7b2",
        "version": {
            "id": manifest["version"],
            "status": manifest["status"],
            "instruction_sha256": actual["instruction"],
            "instruction_utf16": manifest["instruction_utf16"],
            "bundle_sha256": actual["bundle"],
            "manifest_sha256": actual["manifest"],
            "teaching_script_sha256": actual["new_script"],
            "prepared_robin_sha256": actual["prepared_robin"],
            "pad_recopy_sha256": actual["pad_recopy"],
        },
        "cause_boundary": {
            "classification": analysis["pipeline_boundary"]["classification"],
            "r9_earliest_confirmed_missing_stage": analysis["pipeline_boundary"]["r9"]["earliest_confirmed_missing_stage"],
            "r10_earliest_confirmed_missing_stage": analysis["pipeline_boundary"]["r10"]["earliest_confirmed_missing_stage"],
            "copy_save_extract_decode_causal": False,
            "hidden_model_or_service_cause": "UNKNOWN_NOT_CLAIMED",
        },
        "extraction_decode": {
            "known_good_parser_error_count": analysis["extraction_decode_tests"]["good"]["parser_error_count"],
            "intentional_negative_mutations_preserved": analysis["extraction_decode_tests"]["intentional_negative"]["mutations_preserved_exactly"],
            "intentional_negative_parser_error_count": analysis["extraction_decode_tests"]["intentional_negative"]["parser_error_count"],
            "intentional_negative_executed": False,
        },
        "implementation_change": {
            "old_lines": analysis["local_successor"]["old_script_lines"],
            "new_lines": analysis["local_successor"]["new_script_lines"],
            "old_utf8_bytes_without_final_newline": analysis["local_successor"]["old_script_utf8_bytes_without_final_newline"],
            "new_utf8_bytes_without_final_newline": analysis["local_successor"]["new_script_utf8_bytes_without_final_newline"],
            "retired_fragments": analysis["local_successor"]["avoided_fragments"],
            "diff": "r10-to-r11-script.diff",
            "new_parser_error_count": analysis["local_successor"]["parser_error_count"],
        },
        "independent_source_pad": {
            "result": pad_capture["result"],
            "flow_name": pad_capture["environment"]["flow_name"],
            "paste_count": pad_capture["observation"]["paste_invocations"],
            "save_count": pad_capture["observation"]["save_invocations"],
            "recopy_count": pad_capture["observation"]["recopy_invocations"],
            "actions": pad_capture["observation"]["actions_after_paste"],
            "variables": pad_capture["observation"]["variables_after_paste"],
            "lf_normalized_exact": pad_capture["comparison"]["lf_normalized_exact"],
            "executed": False,
        },
        "dedicated_synthetic_pad": {
            "recopy_result": synthetic_capture["result"],
            "run_result": run["decision"],
            "pad_runs_used": run["authorization_boundary"]["pad_runs_used"],
            "additional_run": run["authorization_boundary"]["additional_pad_run"],
            "pad_json_comparisons": pad_boolean_checks,
            "external_artifact_result": artifact["status"],
            "external_artifact_checks_passed": sum(1 for value in artifact["checks"].values() if value),
            "external_artifact_checks_total": len(artifact["checks"]),
            "result_sha256": actual["synthetic_result"],
            "scope": "text and number at synthetic A2:B2 only",
            "exception_restoration": {
                "inner_finally_structure": "PASS",
                "normal_path_original_format_restored": "PASS",
                "forced_exception_runtime": "NOT_RUN",
            },
        },
        "protected_inputs": {
            "fixed_request_sha256": actual["fixed_request"],
            "fixed_spec_sha256": actual["fixed_spec"],
            "fixed_expected_sha256": actual["fixed_expected"],
            "r9_generated_sha256": actual["r9_generated"],
            "r10_generated_sha256": actual["r10_generated"],
            "legacy_558_record_sha256": actual["legacy_558"],
            "r9_r10_generated_outputs_modified": False,
        },
        "scope": {
            "copilot_send": 0,
            "integrated_ex03_run": 0,
            "additional_dedicated_pad_run": 0,
            "github_write": 0,
            "legacy_558_failure_preserved": True,
            "existing_output_guard_live_path": "REMAINS_UNCONFIRMED",
            "integrated_output_path_absent": not (
                ROOT
                / "catalog/acceptance/issue38/runs/EX03-attempt1/照合結果.xlsx"
            ).exists(),
        },
        "decision": {
            "status": "PASS_LOCAL_R11_CAUSE_BOUNDARY_AND_BOUNDED_PAD_VALIDATION_NOT_EX03_ACCEPTANCE",
            "accepted_for_copilot_ex03": False,
            "reason": "Copilot send and integrated EX03 PAD Run1/Run2 were not authorized in this task and remain not run.",
        },
    }
    write_new(
        PROBE / "acceptance.json",
        json.dumps(acceptance, ensure_ascii=False, indent=2) + "\n",
    )

    review = f"""# Issue #38 EX03 r11 local cause analysis and bounded validation

## 判定

`{acceptance['decision']['status']}`。r9/r10共通の欠落は後段のcopy/save/extract/decodeでは発生しておらず、最初に保全できた応答表現に既に存在した。非公開のmodel/service内部原因は推定しない。

r11は指示だけでなく内包PowerShellを実変更した。88行 / 5011 byteを58行 / 3300 byteへ短縮し、壊れた3静的member表現を廃止した。独立教材のPAD保存・再コピーはPASS、同じ短縮表現の合成2セルprobeはPAD 1 Runと成果物13/13をPASSした。ただしCopilot送信0、EX03統合Run 0なのでEX03受入ではない。

## 変更前後

変更前:

```powershell
if ([string]::Equals([IO.Path]::GetFullPath([string]$candidate.FullName), $targetPath, [StringComparison]::OrdinalIgnoreCase)) {{
if ($afterPrefixCharacter -cne $beforePrefixCharacter -or -not [string]::IsNullOrEmpty($afterPrefixCharacter)) {{
```

変更後:

```powershell
$targetPath = [IO.Path]::GetFullPath($targetPath)
if ([IO.Path]::GetFullPath([string]$candidate.FullName) -ieq $targetPath) {{ $matches += $candidate }}
try {{
    $cell.NumberFormat = '@'
    $cell.Value2 = [string]$payload.probe
}}
finally {{ $cell.NumberFormat = $beforeNumberFormat }}
if ([string]$cell.PrefixCharacter -cne '') {{ throw (...) }}
```

完全diff: `r10-to-r11-script.diff`

## 証拠

- r9境界: `rendered_response_code_dom`。DOMとcode copy SHAは同一。
- r10境界: `copied_full_response`。full responseはcode copyをbyte同一で内包。
- known-good decode: parser error 0。
- 意図的破損負例: 欠落2件をdecode後も保持しparser error 19、未実行。
- 独立教材PAD: 1 paste / 1 save / 1 recopy、110 action / 45 variable、LF正規化一致、実行0。
- 合成PAD: 1 paste / 1 save / 1 recopy / 1 Run。source/immediate/reopenedのtext/number JSON比較6件は全True。
- 成果物: text value/type、number value/type、元書式、prefix空、formulaなし、source/work非改変を含む13/13 PASS。
- 例外復元: inner finally構造と正常経路の元書式復元はPASS。強制例外RunはNOT_RUN。

## 固定版

- version: `{manifest['version']}`
- instruction SHA-256: `{actual['instruction']}` ({manifest['instruction_utf16']} UTF-16 units)
- bundle SHA-256: `{actual['bundle']}`
- manifest SHA-256: `{actual['manifest']}`
- PAD-recopied teaching Robin SHA-256: `{actual['pad_recopy']}`
- embedded script SHA-256: `{actual['new_script']}`

固定依頼・spec・expected、r9/r10生成物、旧558差分記録はSHA固定で非改変。既存output guard実機経路は未確認のまま。GitHub書込み0。
"""
    write_new(PROBE / "review.md", review)

    result = {
        "decision": acceptance["decision"]["status"],
        "acceptance_sha256": sha256(PROBE / "acceptance.json"),
        "review_sha256": sha256(PROBE / "review.md"),
        "diff_sha256": sha256(PROBE / "r10-to-r11-script.diff"),
        "instruction_sha256": actual["instruction"],
        "bundle_sha256": actual["bundle"],
        "manifest_sha256": actual["manifest"],
    }
    print(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == "__main__":
    main()
