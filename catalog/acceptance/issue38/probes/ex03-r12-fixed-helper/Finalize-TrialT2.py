#!/usr/bin/env python3
"""Validate and finalize the single saved-flow T2 fixed-helper auxiliary Run."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PROBE = Path(__file__).resolve().parent
ROOT = PROBE.parents[4]
T1 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T1"
T2 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T2"
RUN = T2 / "run1"
RUNTIME = T1 / "runtime"
WORK = RUNTIME / "work.xlsx"
OUTPUT = RUNTIME / "照合結果.xlsx"
RESULT_XLSX = RUN / "result.xlsx"
TEMPLATE = ROOT / "catalog/acceptance/issue38/fixtures/EX03/ひな形.xlsx"
HELPER = PROBE / "EX03-R12-Fixed-StringTransfer.ps1"
INVOCATION = T1 / "invocation.json"
LAUNCHER = T1 / "launcher.ps1"
R11_FINALIZER_PATH = ROOT / "tools/Finalize-Issue38Ex03R11FileAux.py"
EXPECTED_WORK_SHA = "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21"
EXPECTED_SUCCESS = '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}'
EXPECTED_FIXED_SHA = {
    "helper": "08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135",
    "invocation": "92ea864a7e43cec61b4215592a3bae9b8b31109af4e18d3ff0a79dcb15fc5ad6",
    "launcher": "1e9750385455999460e9b1dce754e2a649d4837ae1939cd444376fc360a25ee1",
    "execution_recopy": "da54e5f4388cd0bb896ee00e534e9d81a444f5b950ac1f1bf006f8ea788ad4aa",
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


r11 = load_module("issue38_t2_reused_r11_finalizer", R11_FINALIZER_PATH)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def recorded_path(value: object, label: str) -> Path:
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be a path")
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def path_is(value: object, expected: Path, label: str) -> bool:
    return recorded_path(value, label) == expected.resolve()


def main() -> int:
    for path in (T2 / "result.json", T2 / "RESULT.md"):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite T2 final evidence: {path}")

    plan = load(T2 / "plan.json")
    preflight = load(T2 / "preflight.json")
    identity = load(T2 / "pad-recopy.json")
    pad_run = load(RUN / "pad-run.json")
    pad_variables = load(RUN / "pad-variables.json")
    artifact = load(RUN / "artifact.json")
    typed = load(RUN / "typed-transfer.json")
    legacy = load(RUN / "comparison.json")
    native = load(RUN / "native-styles.json")
    f6 = load(RUN / "f6-native.json")
    contract = r11.fixed_contract()

    require(
        plan["trial_id"] == preflight["trial_id"] == "EX03-R12-FIXED-HELPER-P1-T2",
        "T2 plan/preflight identity mismatch",
    )
    require(
        preflight["result"] == "PASS_READY_FOR_ONE_SAVED_FLOW_NORMAL_PAD_RUN",
        "T2 preflight result mismatch",
    )
    require(
        identity["result"] == "PASS_CURRENT_SAVED_FLOW_EXACT_T1_RECOPY_BASELINE",
        "T2 saved-flow identity mismatch",
    )
    require(identity["comparison"]["byte_exact_to_t1_baseline"] is True, "T2 re-copy not exact")
    require(
        preflight["identity"]["unknown_content_difference_count"] == 0
        and preflight["identity"]["decoded_saved_flow_launcher_exact"] is True
        and preflight["identity"]["other_robin_processing_exact_after_known_difference"] is True,
        "T2 execution identity is not limited to the known T1 differences",
    )

    observed_fixed = {
        "helper": sha256(HELPER),
        "invocation": sha256(INVOCATION),
        "launcher": sha256(LAUNCHER),
        "execution_recopy": sha256(T2 / "pad-recopy-before-run.robin"),
    }
    require(observed_fixed == EXPECTED_FIXED_SHA, "Fixed helper path SHA changed")
    for name, value in observed_fixed.items():
        require(preflight["fixed_sha256"].get(name) == value, f"Preflight fixed SHA mismatch: {name}")
    fixed_script_text = HELPER.read_text(encoding="utf-8") + "\n" + LAUNCHER.read_text(encoding="utf-8")
    stderr_tokens = ("[Console]::Error", "Write-Error", "2>", "2>&1")
    stderr_emitter_counts = {
        token: fixed_script_text.count(token) for token in stderr_tokens
    }
    require(not any(stderr_emitter_counts.values()), "Fixed scripts contain an explicit stderr emitter")
    require(
        fixed_script_text.count("$ErrorActionPreference = 'Stop'") == 2,
        "Fixed helper/launcher error-stop contract changed",
    )

    require(pad_run["run_id"] == "EX03-R12-FIXED-HELPER-P1-T2-RUN1", "PAD Run id mismatch")
    require(pad_run["run_index"] == 1 and pad_run["run_invocations_total"] == 1, "PAD Run count mismatch")
    terminal = pad_run["terminal_observation"]
    require(
        terminal
        == {
            "status_bar": "READY",
            "run_button_enabled": True,
            "stop_button_disabled": True,
            "designer_error_observed": False,
            "normal_termination_observed": True,
        },
        "PAD terminal observation mismatch",
    )
    powershell = pad_run["powershell"]
    require(powershell["stdout_variable"] == "PowershellOutput", "PowerShell output variable mismatch")
    require(powershell["stdout_observed"] == EXPECTED_SUCCESS, "PowerShell success JSON mismatch")
    require(powershell["stdout_matches_fixed_success_json"] is True, "PowerShell success gate mismatch")
    require(powershell["separate_stderr_variable_in_saved_robin"] is False, "Unexpected stderr claim")
    require(powershell["stderr_empty_not_claimed"] is True, "Unproven empty stderr claim")
    require(
        pad_run["status"] == "PASS_TERMINAL_READY_SUCCESS_JSON_NO_DESIGNER_ERROR",
        "PAD Run status mismatch",
    )

    require(
        pad_variables["powershell_output"] == {"observed_value": EXPECTED_SUCCESS, "match": True},
        "PAD PowershellOutput observation mismatch",
    )
    require(
        pad_variables["transfer_state"]
        == {"observed_value": "SAVED_REOPENED_12_JSON_COMPARISONS_READY", "match": True},
        "PAD TransferState mismatch",
    )
    require(pad_variables["counts"] == {"true": 12, "false": 0, "total": 12}, "PAD type counts mismatch")
    require(len(pad_variables["value_type_matches"]) == 12, "PAD type mapping count mismatch")
    require(
        all(
            value == {"observed_value": True, "match": True}
            for value in pad_variables["value_type_matches"].values()
        ),
        "PAD value/type match failure",
    )

    require(RESULT_XLSX.is_file(), "Preserved result missing")
    require((RUN / "work.xlsx").is_file(), "Preserved work missing")
    result_sha = sha256(RESULT_XLSX)
    require(artifact["output_sha256"] == result_sha, "Artifact output SHA mismatch")
    require(artifact["output_bytes"] == RESULT_XLSX.stat().st_size, "Artifact output size mismatch")
    require(path_is(artifact["preserved_output_path"], RESULT_XLSX, "artifact output"), "Artifact path mismatch")
    require(path_is(artifact["runtime_output_path"], OUTPUT, "runtime output"), "Runtime output path mismatch")
    require(artifact["work_sha256"] == sha256(RUN / "work.xlsx") == EXPECTED_WORK_SHA, "Work SHA mismatch")
    require(path_is(artifact["runtime_work_path"], WORK, "runtime work"), "Runtime work path mismatch")
    require(artifact["preserved_output_exact"] is True and artifact["preserved_work_exact"] is True, "Artifact exact flags failed")
    require(artifact["status"] == "PASS_T2_RUN1_ARTIFACT_AND_HANDOFF_PRESERVED", "Artifact status mismatch")
    for name, expected_sha in artifact["handoff_sha256"].items():
        require(sha256(RUN / "handoff" / name) == expected_sha, f"Handoff SHA mismatch: {name}")

    require(typed["run_label"] == "EX03-R12-FIXED-HELPER-P1-T2-RUN1", "Typed Run label mismatch")
    typed_for_shared_validator = copy.deepcopy(typed)
    typed_for_shared_validator["run_label"] = "EX03-R11-FILE-AUX1-RUN1"
    r11.validate_typed_report(typed_for_shared_validator, 1, RESULT_XLSX, result_sha, contract)
    r11.validate_legacy_report(legacy, result_sha, contract)
    r11.validate_native_report(native, RESULT_XLSX, result_sha, contract)
    r11.validate_f6_report(f6, RESULT_XLSX, result_sha, contract)

    require(sha256(WORK) == sha256(TEMPLATE) == EXPECTED_WORK_SHA, "Runtime work/template changed")
    require(OUTPUT.is_file() and sha256(OUTPUT) == result_sha, "Runtime output no longer matches preserved result")
    require(sha256(T2 / "work-before.xlsx") == EXPECTED_WORK_SHA, "Pre-run work evidence changed")

    source_hashes_after = {
        path: sha256(ROOT / "catalog/acceptance/issue38" / path)
        for path in contract["source_hashes"]
    }
    require(source_hashes_after == contract["source_hashes"], "Original input SHA changed")

    protected_mismatches = []
    for item in preflight["protected_tracked_files"]:
        path = ROOT / item["path"]
        current_blob = subprocess.check_output(
            ["git", "hash-object", f"--path={item['path']}", str(path)],
            cwd=ROOT,
            text=True,
        ).strip()
        if current_blob != item["git_blob"]:
            protected_mismatches.append(
                {"path": item["path"], "expected_blob": item["git_blob"], "actual_blob": current_blob}
            )
    require(not protected_mismatches, f"Protected evidence changed: {protected_mismatches}")

    runtime_output = RUN / "runtime-output-after-run.xlsx"
    shutil.move(str(OUTPUT), str(runtime_output))
    require(not OUTPUT.exists() and sha256(runtime_output) == result_sha, "Runtime output preservation failed")
    runtime_handoff = RUN / "runtime-handoff-after-run"
    runtime_handoff.mkdir()
    for name, expected_sha in artifact["handoff_sha256"].items():
        source = RUNTIME / name
        destination = runtime_handoff / name
        require(source.is_file(), f"Runtime handoff missing before preservation: {name}")
        shutil.move(str(source), str(destination))
        require(sha256(destination) == expected_sha, f"Runtime handoff preservation failed: {name}")
        require(sha256(RUN / "handoff" / name) == expected_sha, f"Copied handoff changed: {name}")

    remaining_runtime_json = sorted(path.name for path in RUNTIME.glob("*.json"))
    require(not remaining_runtime_json, f"Runtime JSON remains after preservation: {remaining_runtime_json}")
    require(sha256(WORK) == EXPECTED_WORK_SHA, "Runtime work changed after preservation")

    legacy_total = sum(legacy["failure_counts"].values())
    result = {
        "schema_version": 1,
        "trial_id": "EX03-R12-FIXED-HELPER-P1-T2",
        "decision": "PASS_FIXED_HELPER_AUXILIARY_NORMAL_RUN1",
        "scope": "Fixed-helper alternate-path auxiliary test only; not formal EX03-r12 acceptance.",
        "execution_identity": {
            "saved_flow_sha256": EXPECTED_FIXED_SHA["execution_recopy"],
            "byte_exact_to_t1_recopy": True,
            "known_difference_hunks": 1,
            "unknown_difference_count": 0,
            "decoded_launcher_exact": True,
            "helper_sha256": observed_fixed["helper"],
            "invocation_sha256": observed_fixed["invocation"],
            "launcher_sha256": observed_fixed["launcher"],
            "fixed_paths_unchanged": True,
        },
        "pad": {
            "flow_name": pad_run["flow_name"],
            "flow_window_id": pad_run["flow_window_id"],
            "repaste_count": 0,
            "resave_count": 0,
            "verification_recopy_count": 1,
            "run_count": 1,
            "terminal": terminal,
            "powershell_stdout": EXPECTED_SUCCESS,
            "stderr": {
                "designer_error_observed": False,
                "separate_pad_variable_available": False,
                "empty_stderr_directly_proven": False,
                "fixed_scripts_explicit_stderr_emitters": stderr_emitter_counts,
                "boundary": "No separate stderr variable exists in the fixed saved Robin; exact success JSON, fail-closed launcher, READY terminal state, and no Designer error were observed.",
            },
            "transfer_state": "SAVED_REOPENED_12_JSON_COMPARISONS_READY",
            "value_type_match_true": 12,
            "value_type_match_false": 0,
        },
        "artifact": {
            "result_path": str(RESULT_XLSX),
            "result_sha256": result_sha,
            "result_bytes": RESULT_XLSX.stat().st_size,
            "runtime_output_preserved_path": str(runtime_output),
            "runtime_output_absent_after_preservation": not OUTPUT.exists(),
            "runtime_json_absent_after_preservation": not remaining_runtime_json,
            "work_sha256": sha256(WORK),
            "work_matches_template": sha256(WORK) == sha256(TEMPLATE),
        },
        "comparison": {
            "target_cells": {"checked": 12, "mismatches": 0, "status": "PASS"},
            "outside_cells": {"checked": 468, "mismatches": 0, "status": "PASS"},
            "formulas": {"mismatches": 0, "status": "PASS"},
            "effective_format": {
                "checked_cells": native["bounds"]["checked_cells"],
                "checked_rows": native["bounds"]["checked_rows"],
                "checked_columns": native["bounds"]["checked_columns"],
                "difference_attribute_counts": native["difference_attribute_counts"],
                "status": native["status"],
            },
            "f6": {
                "value": f6["saved_f6"]["value2"],
                "dotnet_type": f6["saved_f6"]["value2_dotnet_type"],
                "number_format": f6["saved_f6"]["number_format_invariant"],
                "prefix": f6["saved_f6"]["prefix_character"],
                "has_formula": f6["saved_f6"]["has_formula"],
                "status": f6["status"],
            },
            "legacy_raw_diagnostic": {
                "status": "FAIL_PRESERVED_NOT_USED_AS_EFFECTIVE_FORMAT_GATE",
                "failure_counts": legacy["failure_counts"],
                "total": legacy_total,
            },
            "original_inputs_unchanged": True,
            "template_unchanged": True,
        },
        "preservation": {
            "t1_fail_run0_records_unchanged": True,
            "formal_ex03_r12_unchanged": True,
            "protected_tracked_mismatch_count": 0,
            "github_write": False,
        },
        "remaining": [
            "The fixed saved Robin has no separate stderr output variable; empty stderr is not directly claimed.",
            "This auxiliary PASS does not replace or broaden formal EX03-r12 acceptance.",
            "No type, workbook shape, or PAD environment beyond the fixed EX03 case is generalized.",
        ],
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(T2 / "result.json", result)

    report = f"""# Issue #38 EX03 r12 fixed-helper saved-flow T2 auxiliary Run

## 判定

`EX03-R12-FIXED-HELPER-P1-T2` は、T1で保存された専用フローを再貼付け・再保存せず正常系1Runした補助試験である。PAD終了、固定成功JSON、12件のPAD内値・型照合、保存xlsxの固定比較はPASSした。正式EX03-r12受入には転用しない。

## 実行対象の同一性

- 現在のPAD再コピーはT1原文SHA `{EXPECTED_FIXED_SHA['execution_recopy']}` とバイト一致
- 既知差分はlauncher成功JSONの引用符エスケープ1 hunkと改行表現のみ
- 未知差分0、復号後launcher・他処理は固定内容と一致
- helper `{observed_fixed['helper']}`
- invocation `{observed_fixed['invocation']}`
- launcher `{observed_fixed['launcher']}`
- 実行用パスはT1の固定パスのまま

## PAD観測

- 再貼付け0、再保存0、確認再コピー1、Run 1
- `PowershellOutput`: `{EXPECTED_SUCCESS}`
- `TransferState`: `SAVED_REOPENED_12_JSON_COMPARISONS_READY`
- `ValueTypeMatch`: 12 true / 0 false
- 終了状態 READY、Run有効、Stop無効、Designerエラーなし
- 保存Robinは別stderr変数を持たないため、stderr空は直接断定しない。固定スクリプトに明示stderr出力はなく、成功JSON・fail-closed gate・正常終了を観測した。

## 成果物照合

- result SHA-256 `{result_sha}`
- 12対象セル: 値・型・位置 mismatch 0
- 対象外468セル: 値・型・数式 mismatch 0
- Excel実効書式: 480セル、48行、30列、差分0
- F6: `100%` / `System.String` / `G/標準` / prefix空 / 数式なし
- 原本入力・ひな形SHA不変、workはひな形と同一
- 旧raw比較の558差分（style 480、row 48、column 30）は別記録として保持

## 保全と境界

- T1 FAIL・Run 0記録、正式r12、固定依頼・期待値は不変
- runtime出力とJSON handoffはT2証跡へ移動保全し、T1 runtimeをworkのみの事前状態へ戻した
- Copilot送信、正式EX03再試験、候補版作成、追加Run、GitHub書込みなし
"""
    (T2 / "RESULT.md").write_text(report, encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
