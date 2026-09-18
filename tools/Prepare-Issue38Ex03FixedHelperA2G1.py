#!/usr/bin/env python3
"""Prepare the one-send, at-most-two-run EX03 fixed-helper A2-G1 checkpoint."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
CANDIDATE = ROOT / "copilot/versions/20260918-excel-r12-fixed-helper-a2"
CYCLE = BASE / "cycles/EX03-r12-fixed-helper-A2-G1"
PROBE = BASE / "probes/ex03-r12-fixed-helper"
T1 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T1"
T2 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T2"
RUNTIME = T1 / "runtime"

HELPER = PROBE / "EX03-R12-Fixed-StringTransfer.ps1"
INVOCATION = T1 / "invocation.json"
LAUNCHER = T1 / "launcher.ps1"
REQUEST = BASE / "requests/EX03.txt"
SPEC = BASE / "spec.json"
EXPECTED = BASE / "expected.json"
TEMPLATE = BASE / "fixtures/EX03/ひな形.xlsx"
INPUT1 = BASE / "fixtures/EX03/入力い.xlsx"
INPUT2 = BASE / "fixtures/EX03/入力ろ.xlsx"
WORK = RUNTIME / "work.xlsx"
OUTPUT = RUNTIME / "照合結果.xlsx"

INSTRUCTION = CANDIDATE / "agent-instructions.txt"
BUNDLE = CANDIDATE / "knowledge/PAD-Robin-Fixed-Helper-A2-Bundle.txt"
MANIFEST = CANDIDATE / "manifest.json"
COVERAGE = CANDIDATE / "COVERAGE.md"
PLACEMENT = CANDIDATE / "PLACEMENT.md"
NON_LIVE = CANDIDATE / "non-live-verification.json"

CYCLE_ID = "EX03-R12-FIXED-HELPER-COPILOT-A2-G1"
ROUTE_ID = "EX03-R12-FIXED-HELPER-COPILOT-A2"
CANDIDATE_ID = "20260918-excel-r12-fixed-helper-a2"
BASE_COMMIT = "e768b2a14dd8d154ee987554d7c13c53ca644b0f"
EXPECTED_SUCCESS = '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}'

EXPECTED_SHA256 = {
    "instruction": "def1af576bac79d5dbf321ac38d7702d3d968932b2e0767265f9544eb18ebe60",
    "bundle": "009a830d7a1bb431c1f02933e45933c2d7466260c616e46114255605dc3e5b1c",
    "manifest": "afe054f0e532c7c69b1359b54fe07dc05c42bb99e196be07cf3dd826977f008d",
    "coverage": "8813198b1f76c6034918294908fa86ec2c0a2637e186bd1c6aead65d97e2f2d3",
    "placement": "74f8fe4013ceb492fc2ebed661a417749f46c47d147e4ea2c64487909cde556a",
    "non_live": "8520b68a557a49c2324a3c6e78efc2111de2758cb6136d43e033a960bd0b57f0",
    "helper": "08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135",
    "invocation": "92ea864a7e43cec61b4215592a3bae9b8b31109af4e18d3ff0a79dcb15fc5ad6",
    "launcher": "1e9750385455999460e9b1dce754e2a649d4837ae1939cd444376fc360a25ee1",
    "request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
    "template": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
    "work": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
}

SEND_CONDITIONS = rf"""【{ROUTE_ID} / G1 専用送信条件】
このブロックはA2-G1の固定helper別経路条件であり、先頭の正式EX03固定依頼を変更しません。入力ファイル、シート、範囲、転記位置、値・型・位置の期待条件は固定依頼と検証者側spec/expectedのままです。正式r12の判定へは転用しません。

候補ID: {CANDIDATE_ID}
Route ID: {ROUTE_ID}
A2-G1 cycle ID: {CYCLE_ID}
A2専用runtime実パス: {RUNTIME.resolve()}
A2専用work実パス: {WORK.resolve()}
A2専用output実パス: {OUTPUT.resolve()}

検証者が事前配置し、生成物から変更させない物:
- helper: {HELPER.resolve()}
  SHA-256: {EXPECTED_SHA256['helper']}
- invocation: {INVOCATION.resolve()}
  SHA-256: {EXPECTED_SHA256['invocation']}
- launcher: {LAUNCHER.resolve()}
  SHA-256: {EXPECTED_SHA256['launcher']}

この試験は、日本語依頼からhelper、invocation、runtime、期待SHAを生成する試験ではありません。helperとinvocationは生成・展開・変更せず、同版bundleのC06_FIXED_LAUNCHER_RUNSCRIPTを固定パス・SHA・expectedSuccessを含めて変更せず使い、その前後を同版bundleの確認済みRAW_COMPONENTから構成してください。

同版bundleの確認済み部品は、再利用、組合せ、必要回数への反復、IN-BUNDLE INDEXで明示されたパス・sheet・range・target・変数名・データslot・先頭インデントの変更が可能です。組み上げたA2全体は未実行の新しい組合せとして提示してください。完成済みの固定EX03 Robin、採点値、固定EX03専用全配線、過去の統合実行証跡が入力にないことだけを理由に拒否しないでください。未採取の命令名・引数名・列挙値・ブロック構造は捏造せず、実際に根拠がない工程が残る場合だけその工程を報告してください。

固定依頼内の runs\EX03-attempt1 のwork/outputパスは凍結文面として保持しますが、このA2別経路の実行設定には使いません。A2-G1では上記の事前配置invocationと専用runtime実パスを優先します。入力ファイル・sheet・range・targetは固定依頼どおりです。

回答は貼付け用Robin全体をMarkdownの `text` コードブロック1個だけに入れてください。コードブロック内に説明、行番号、Plain Text、JSON、疑似コード、省略記号を入れません。helper/invocationの作成・変更、SHAの再計算・置換、network、delete、既存output上書き、Invoke-Expression、権限・security・Excel設定変更を入れません。

既存output guardは入力読取り、JSON生成、Work起動、helper実行より前です。PowerShell出力が {EXPECTED_SUCCESS} と完全一致し、PAD側RunModeがNORMALの場合だけ5数値書込みとSaveAsへ進みます。それ以外は後続書込み・SaveAsへ進めず、Workを閉じます。SaveAs後は閉じ、ReadOnlyで再開し、2矩形12位置を個別のJSON値型比較にします。

生成物は未実行です。検証者による無修正原文の安全検査とPAD保存・再コピー一致より前に、完成・実行済み・受入済みと表示しないでください。
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(value)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> int:
    if CYCLE.exists():
        raise FileExistsError(f"A2-G1 cycle already exists: {CYCLE}")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if head != BASE_COMMIT:
        raise ValueError(f"A2-G1 must start at {BASE_COMMIT}, observed {head}")

    paths = {
        "instruction": INSTRUCTION,
        "bundle": BUNDLE,
        "manifest": MANIFEST,
        "coverage": COVERAGE,
        "placement": PLACEMENT,
        "non_live": NON_LIVE,
        "helper": HELPER,
        "invocation": INVOCATION,
        "launcher": LAUNCHER,
        "request": REQUEST,
        "spec": SPEC,
        "expected": EXPECTED,
        "template": TEMPLATE,
        "work": WORK,
    }
    actual_sha = {name: sha256(path) for name, path in paths.items()}
    if actual_sha != EXPECTED_SHA256:
        raise ValueError(f"A2 fixed SHA mismatch: {actual_sha}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["candidate_id"] != CANDIDATE_ID or manifest["route_id"] != ROUTE_ID:
        raise ValueError("A2 manifest identity mismatch")
    if manifest["candidate_payload_sha256"] != "7ced4d3d3cf8b9f314b703fa44eeb7508f89d8423afa8fe7ea573342165d5161":
        raise ValueError("A2 candidate payload SHA mismatch")
    if manifest["missing_required_steps"] != []:
        raise ValueError("A2 teaching bundle still records missing steps")
    if manifest["teaching_independence"]["status"] != "PASS":
        raise ValueError("A2 teaching/test independence is not PASS")

    invocation = json.loads(INVOCATION.read_text(encoding="utf-8"))
    if Path(invocation["target_workbook"]).resolve() != WORK.resolve():
        raise ValueError("Fixed invocation target_workbook mismatch")
    if Path(invocation["json_root"]).resolve() != RUNTIME.resolve():
        raise ValueError("Fixed invocation json_root mismatch")
    if len(invocation["text_writes"]) != 7:
        raise ValueError("Fixed invocation text routing count changed")

    handoff_paths = [RUNTIME / f"source-{index}.json" for index in range(1, 8)] + [RUNTIME / "mode.json"]
    if OUTPUT.exists():
        raise ValueError("A2 output already exists before send")
    if any(path.exists() for path in handoff_paths):
        raise ValueError("A2 JSON handoff residue exists before send")

    request = REQUEST.read_text(encoding="utf-8").rstrip("\r\n")
    conditions = SEND_CONDITIONS.rstrip("\r\n")
    instruction = INSTRUCTION.read_text(encoding="utf-8").rstrip("\r\n")
    body = request + "\n\n" + conditions + "\n\n" + instruction + "\n"
    if not body.startswith(request + "\n\n"):
        raise ValueError("Fixed request is not the verbatim leading body component")
    forbidden_a1_clauses = (
        "教材は別条件の未完成断片です",
        "回答へコピーしません",
        "STATIC_FRAGMENT_ONLY_NOT_COMPLETE_NOT_RUN",
        "連結可能な完成回答ではない",
    )
    if any(value in body for value in forbidden_a1_clauses):
        raise ValueError("A1 component-reuse prohibition leaked into A2 submitted body")
    for grader_value in ("春", "夏", "秋", "項目甲", "項目乙", "100%"):
        if grader_value in body:
            raise ValueError(f"Grader value leaked into submitted body: {grader_value}")

    criteria = {
        "schema_version": 1,
        "cycle_id": CYCLE_ID,
        "fixed_before_send": True,
        "response": {
            "markdown_text_code_block_count": 1,
            "generated_robin_unmodified": True,
            "code_first_and_last_nonempty_lines_are_pad_instructions": True,
            "no_explanation_heading_line_number_fence_or_pseudocode_inside": True,
            "refusal_or_no_code": "STOP",
        },
        "syntax_and_structure": {
            "balanced_if_else_end": True,
            "actions_must_use_bundle_observed_command_argument_enum_shapes": True,
            "existing_output_guard_before_read_json_work_and_helper": True,
            "read_only_input_open_count": 2,
            "typed_input_range_read_count": 2,
            "source_json_write_count": 7,
            "mode_json_write_count": 1,
            "fixed_runscript_count": 1,
            "exact_success_and_normal_double_gate": True,
            "numeric_write_count": 5,
            "save_as_count": 1,
            "read_only_output_reopen_count": 1,
            "typed_readback_rectangle_count": 2,
            "json_value_type_comparison_count": 12,
            "failure_close_no_save": True,
            "pad_action_count": "DERIVE_FROM_ACCEPTED_GENERATED_ROBIN_AND_MATCH_DESIGNER",
        },
        "fixed_paths_and_parameters": {
            "input1": str(INPUT1.resolve()),
            "input1_sheet": "受取明細",
            "input1_range": "D4:E6",
            "input2": str(INPUT2.resolve()),
            "input2_sheet": "追加項目",
            "input2_range": "B2:D3",
            "work": str(WORK.resolve()),
            "output": str(OUTPUT.resolve()),
            "target1_sheet": "集計先",
            "target1_start": "F7",
            "target2_sheet": "追記先",
            "target2_start": "D5",
            "json_root": str(RUNTIME.resolve()),
            "source_json_names": [f"source-{index}.json" for index in range(1, 8)],
            "mode_json_name": "mode.json",
        },
        "fixed_launcher": {
            "helper_path": str(HELPER.resolve()),
            "helper_sha256": actual_sha["helper"],
            "invocation_path": str(INVOCATION.resolve()),
            "invocation_sha256": actual_sha["invocation"],
            "launcher_path": str(LAUNCHER.resolve()),
            "launcher_sha256": actual_sha["launcher"],
            "decoded_launcher_terminal_lf_restored_sha256": actual_sha["launcher"],
            "expected_stdout": EXPECTED_SUCCESS,
            "no_launcher_changes": True,
        },
        "safety": {
            "helper_or_invocation_creation_or_modification": False,
            "network": False,
            "delete": False,
            "overwrite_existing_output": False,
            "invoke_expression": False,
            "permission_security_excel_setting_change": False,
            "manual_generated_robin_edit": False,
            "unknown_difference_after_pad_recopy": "STOP",
        },
        "comparison_rule": {
            "t2_complete_flow_verbatim_equality_required": False,
            "observed_escape_and_line_ending_differences": "CLASSIFY_WITH_EXISTING_RULES",
            "all_other_differences": "STOP",
        },
        "run_gate": {
            "max_runs": 2,
            "run1_requires_all_comparisons_and_preservation_before_run2": True,
            "each_run_target_value_type_position_count": 12,
            "each_run_outside_value_type_formula_count": 468,
            "each_run_effective_format_cells": 480,
            "each_run_effective_format_rows": 48,
            "each_run_effective_format_columns": 30,
            "f6": {
                "value": "100%",
                "dotnet_type": "System.String",
                "number_format": "G/標準",
                "prefix": "",
                "has_formula": False,
            },
            "original_input_and_template_sha_unchanged": True,
            "collision_avoidance": "MOVE_RUN_OUTPUT_AND_HANDOFF_TO_RUN_EVIDENCE_THEN_VERIFY_RUNTIME_OUTPUT_JSON_ABSENT_AND_WORK_EQUALS_TEMPLATE",
        },
    }

    protected_paths = [
        HELPER,
        INVOCATION,
        LAUNCHER,
        REQUEST,
        SPEC,
        EXPECTED,
        TEMPLATE,
        INPUT1,
        INPUT2,
        INSTRUCTION,
        BUNDLE,
        MANIFEST,
        COVERAGE,
        PLACEMENT,
        NON_LIVE,
        T2 / "pad-recopy-before-run.robin",
        T2 / "result.json",
        BASE / "cycles/EX03-r12-G1/acceptance-status.json",
        BASE / "cycles/EX03-r12-fixed-helper-A1-G1/copilot-response.txt",
        BASE / "cycles/EX03-r12-fixed-helper-A1-G1/generation-assessment.json",
    ]
    protected = [
        {"path": relative(path), "sha256": sha256(path), "bytes": path.stat().st_size}
        for path in protected_paths
    ]

    now = datetime.now(timezone.utc).astimezone().isoformat()
    CYCLE.mkdir(parents=True, exist_ok=False)
    write_text(CYCLE / "send-conditions.txt", conditions + "\n")
    write_text(CYCLE / "submitted-body.txt", body)
    write_json(CYCLE / "generation-acceptance-criteria.json", criteria)
    write_json(
        CYCLE / "plan.json",
        {
            "schema_version": 1,
            "cycle_id": CYCLE_ID,
            "route_id": ROUTE_ID,
            "candidate_id": CANDIDATE_ID,
            "prepared_at": now,
            "base_commit": BASE_COMMIT,
            "target": "NORMAL_MICROSOFT_365_COPILOT_CHAT",
            "send": {
                "limit_total": 1,
                "local_recorded_before": 0,
                "ui_history_absence_required_before_send": True,
                "resend": 0,
            },
            "input": {
                "fixed_request_path": relative(REQUEST),
                "fixed_request_sha256": actual_sha["request"],
                "send_conditions_path": relative(CYCLE / "send-conditions.txt"),
                "instruction_path": relative(INSTRUCTION),
                "instruction_sha256": actual_sha["instruction"],
                "submitted_body_path": relative(CYCLE / "submitted-body.txt"),
                "submitted_body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                "attachment_path": relative(BUNDLE),
                "attachment_sha256": actual_sha["bundle"],
                "criteria_path": relative(CYCLE / "generation-acceptance-criteria.json"),
            },
            "runtime": {
                "root": str(RUNTIME.resolve()),
                "work": str(WORK.resolve()),
                "output": str(OUTPUT.resolve()),
                "helper": str(HELPER.resolve()),
                "invocation": str(INVOCATION.resolve()),
                "helper_sha256": actual_sha["helper"],
                "invocation_sha256": actual_sha["invocation"],
                "launcher_sha256": actual_sha["launcher"],
            },
            "limits": {
                "copilot_generations_max": 1,
                "pad_runs_max": 2,
                "run2_requires_run1_terminal_all_comparisons_pass_and_artifact_preserved": True,
                "manual_generated_robin_edit": 0,
                "additional_run": 0,
                "next_candidate": 0,
                "full_regression": 0,
                "github_write": 0,
                "stop_on_refusal_mismatch_safety_issue_or_unknown": True,
            },
            "classification": {
                "formal_r12_request_text_modified": False,
                "a2_conditions_separate": True,
                "formal_r12_path_compliance_claimed": False,
                "fixed_input_sheet_range_target_expected_preserved": True,
                "automatic_execution_configuration_from_japanese_request": False,
                "t2_auxiliary_pass_inherited": False,
                "t2_complete_flow_verbatim_equality_required": False,
            },
        },
    )
    write_json(
        CYCLE / "preflight.json",
        {
            "schema_version": 1,
            "cycle_id": CYCLE_ID,
            "recorded_at": now,
            "status": "PASS_LOCAL_READY_PENDING_UI_HISTORY_RECORD",
            "checks": {
                "head_is_e768b2a": True,
                "candidate_manifest_identity": True,
                "candidate_and_all_fixed_sha": True,
                "fixed_request_is_verbatim_leading_component": True,
                "a1_component_reuse_prohibition_absent": True,
                "a2_reuse_combination_parameter_change_allowed": True,
                "actual_runtime_paths_in_body": True,
                "helper_invocation_launcher_paths_and_sha_in_body": True,
                "grader_values_absent_from_body": True,
                "comparison_criteria_fixed_before_send": True,
                "work_matches_template": True,
                "output_absent": True,
                "json_handoff_residue_absent": True,
                "ui_send_history_checked": False,
                "normal_m365_chat_confirmed": False,
            },
            "next_gate": "RECORD_CONFIRMED_A2_G1_NOT_PREVIOUSLY_SENT_IN_NORMAL_M365_CHAT",
        },
    )
    write_json(
        CYCLE / "protected-before.json",
        {
            "schema_version": 1,
            "cycle_id": CYCLE_ID,
            "recorded_at": now,
            "base_commit": BASE_COMMIT,
            "files": protected,
            "runtime": {
                "work_sha256": actual_sha["work"],
                "output_absent": True,
                "handoff_absent": [relative(path) for path in handoff_paths],
            },
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS_LOCAL_READY_PENDING_UI_HISTORY_RECORD",
                "cycle_id": CYCLE_ID,
                "submitted_body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                "submitted_body_characters": len(body),
                "bundle_sha256": actual_sha["bundle"],
                "criteria_sha256": sha256(CYCLE / "generation-acceptance-criteria.json"),
                "runtime": str(RUNTIME.resolve()),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
