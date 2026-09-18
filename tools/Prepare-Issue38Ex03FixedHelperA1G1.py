#!/usr/bin/env python3
"""Prepare the one-send EX03 fixed-helper A1-G1 live checkpoint."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
CANDIDATE = ROOT / "copilot/versions/20260918-excel-r12-fixed-helper-a1"
CYCLE = BASE / "cycles/EX03-r12-fixed-helper-A1-G1"
PROBE = BASE / "probes/ex03-r12-fixed-helper"
T1 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T1"
T2 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T2"
RUNTIME = T1 / "runtime"
HELPER = PROBE / "EX03-R12-Fixed-StringTransfer.ps1"
INVOCATION = T1 / "invocation.json"
LAUNCHER = T1 / "launcher.ps1"
T2_RECOPY = T2 / "pad-recopy-before-run.robin"
REQUEST = BASE / "requests/EX03.txt"
SPEC = BASE / "spec.json"
EXPECTED = BASE / "expected.json"
TEMPLATE = BASE / "fixtures/EX03/ひな形.xlsx"
WORK = RUNTIME / "work.xlsx"
OUTPUT = RUNTIME / "照合結果.xlsx"
INSTRUCTION = CANDIDATE / "agent-instructions.txt"
BUNDLE = CANDIDATE / "knowledge/PAD-Robin-Fixed-Helper-Bundle.txt"
MANIFEST = CANDIDATE / "manifest.json"
PLACEMENT = CANDIDATE / "PLACEMENT.md"

CYCLE_ID = "EX03-R12-FIXED-HELPER-COPILOT-A1-G1"
ROUTE_ID = "EX03-R12-FIXED-HELPER-COPILOT-A1"
CANDIDATE_ID = "20260918-excel-r12-fixed-helper-a1"
BASE_COMMIT = "55de244bee8394b2909c8af9d568701594cb40b9"
EXPECTED_SUCCESS = '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}'

EXPECTED_SHA256 = {
    "instruction": "0335ade50639ac8b115c0ef7281be66c60ae0719852865c50cc8ca83ae4a8c73",
    "bundle": "380c498f513019c49523adc362ad917fbf2199e426c766468231df50820ae4ca",
    "manifest": "71bd0344cd6b225113b43cbc92146c9c060e0fb3bce31e5e1246bee06ef581b5",
    "placement": "fbdef6cf15db1f6983cd902a67a5dbfeea170c5b7f362b3abb310a867a4f8810",
    "helper": "08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135",
    "invocation": "92ea864a7e43cec61b4215592a3bae9b8b31109af4e18d3ff0a79dcb15fc5ad6",
    "launcher": "1e9750385455999460e9b1dce754e2a649d4837ae1939cd444376fc360a25ee1",
    "t2_recopy": "da54e5f4388cd0bb896ee00e534e9d81a444f5b950ac1f1bf006f8ea788ad4aa",
    "request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
    "template": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
    "work": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
}

SEND_CONDITIONS = rf"""【{ROUTE_ID} / G1 専用送信条件】
このブロックはA1-G1の別経路条件であり、直前の正式EX03固定依頼を変更しません。入力ファイル、シート、範囲、転記位置、値・型・位置の期待値は固定依頼とspec/expectedのままです。正式r12の受入結果へは転用しません。

候補ID: {CANDIDATE_ID}
Route ID: {ROUTE_ID}
A1-G1 cycle ID: {CYCLE_ID}
A1専用runtime実パス: {RUNTIME.resolve()}
A1専用work実パス: {WORK.resolve()}
A1専用output実パス: {OUTPUT.resolve()}

検証者が事前配置し、生成物から変更させない物:
- helper: {HELPER.resolve()}
  SHA-256: {EXPECTED_SHA256['helper']}
- invocation: {INVOCATION.resolve()}
  SHA-256: {EXPECTED_SHA256['invocation']}

この試験は、日本語依頼からhelper、invocation、runtime、期待SHAなどの実行設定まで自動生成する試験ではありません。Copilotはhelper本体とinvocation JSONを出力せず、同版bundleのFIXED LAUNCHER SOURCEを検証者固定SHAリテラルごと変更せず1個のRun PowerShell Scriptへ埋め込み、その前後のPAD処理だけを生成してください。

固定依頼内の runs\EX03-attempt1 のwork/outputパスは凍結文面として保持しますが、このA1別経路の実行設定には使いません。A1-G1では上記の事前配置invocationとruntime実パスを優先します。このため、A1の固定条件に限る判定であり、正式r12の依頼パス適合は主張しません。

回答は貼付け用Robin全体をMarkdownの `text` コードブロック1個だけに入れてください。コードブロック内に説明、行番号、Plain Text、JSON、疑似コード、省略記号を入れません。helper/invocationの作成・変更、SHAの再計算・置換、network、delete、既存output上書き、Invoke-Expression、権限・security・Excel設定変更を入れません。

PowerShell出力が {EXPECTED_SUCCESS} と完全一致し、PAD側RunModeがNORMALの場合だけ数値書込みとSaveAsへ進めます。それ以外は後続書込み・SaveAsへ進めず、Workを閉じます。既存output guardは入力読取り、JSON生成、Work起動、helper実行より前に置いてください。

教材は別条件の未完成断片です。固定EX03の完成Robinや採点値として扱わず、回答へコピーしません。生成物自体は未実行として提示し、無修正原文の安全検査とPAD保存・再コピー一致より前に成功扱いしません。
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_text(path: Path, value: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(value)


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> int:
    if CYCLE.exists():
        raise FileExistsError(f"A1-G1 cycle already exists: {CYCLE}")

    paths = {
        "instruction": INSTRUCTION,
        "bundle": BUNDLE,
        "manifest": MANIFEST,
        "placement": PLACEMENT,
        "helper": HELPER,
        "invocation": INVOCATION,
        "launcher": LAUNCHER,
        "t2_recopy": T2_RECOPY,
        "request": REQUEST,
        "spec": SPEC,
        "expected": EXPECTED,
        "template": TEMPLATE,
        "work": WORK,
    }
    actual_sha = {name: sha256(path) for name, path in paths.items()}
    if actual_sha != EXPECTED_SHA256:
        raise ValueError(f"A1 fixed SHA mismatch: {actual_sha}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["candidate_id"] != CANDIDATE_ID or manifest["route_id"] != ROUTE_ID:
        raise ValueError("A1 manifest identity mismatch")
    if manifest["candidate_payload_sha256"] != "306c056e04c0ae388a6b47903fb60cb529a02d396bca28c6c1bd944f7147cc94":
        raise ValueError("A1 candidate payload SHA mismatch")
    if manifest["scope"] != {
        "copilot_send_count": 0,
        "pad_save_recopy_count": 0,
        "pad_run_count": 0,
        "excel_run_count": 0,
        "successful_probe_rerun": 0,
        "full_regression": "NOT_RUN_BY_SCOPE",
        "github_write_count": 0,
    }:
        raise ValueError("A1 prepared-scope boundary changed")

    invocation = json.loads(INVOCATION.read_text(encoding="utf-8"))
    if Path(invocation["target_workbook"]).resolve() != WORK.resolve():
        raise ValueError("Fixed invocation target_workbook does not bind to A1 runtime work")
    if Path(invocation["json_root"]).resolve() != RUNTIME.resolve():
        raise ValueError("Fixed invocation json_root does not bind to A1 runtime")
    if len(invocation["text_writes"]) != 7:
        raise ValueError("Fixed invocation text routing count changed")

    if OUTPUT.exists():
        raise ValueError("A1 output already exists before send")
    handoff_paths = [RUNTIME / f"source-{index}.json" for index in range(1, 8)] + [
        RUNTIME / "mode.json"
    ]
    if any(path.exists() for path in handoff_paths):
        raise ValueError("A1 JSON handoff residue exists before send")

    request = REQUEST.read_text(encoding="utf-8").rstrip("\r\n")
    conditions = SEND_CONDITIONS.rstrip("\r\n")
    instruction = INSTRUCTION.read_text(encoding="utf-8").rstrip("\r\n")
    body = request + "\n\n" + conditions + "\n\n" + instruction + "\n"
    if not body.startswith(request + "\n\n"):
        raise ValueError("Fixed request is not the verbatim leading body component")
    for grader_value in ("春", "夏", "秋", "項目甲", "項目乙", "100%"):
        if grader_value in body:
            raise ValueError(f"Grader value leaked into submitted body: {grader_value}")

    protected_paths = [
        HELPER,
        INVOCATION,
        LAUNCHER,
        T2_RECOPY,
        REQUEST,
        SPEC,
        EXPECTED,
        TEMPLATE,
        INSTRUCTION,
        BUNDLE,
        MANIFEST,
        PLACEMENT,
        PROBE / "Finalize-TrialT2.py",
        ROOT / "tests/Test-Issue38Ex03FixedHelperTrialT2.py",
        PROBE / "reviews/FH-R1-corrections.json",
        BASE / "cycles/EX03-r12-G1/acceptance-status.json",
        T2 / "result.json",
    ]
    protected = [
        {
            "path": relative(path),
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in protected_paths
    ]

    now = datetime.now(timezone.utc).astimezone().isoformat()
    CYCLE.mkdir(parents=True, exist_ok=False)
    write_text(CYCLE / "send-conditions.txt", conditions + "\n")
    write_text(CYCLE / "submitted-body.txt", body)
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
                "normal_pad_runs_max": 2,
                "run2_requires_run1_terminal_all_comparisons_pass_and_artifact_preserved": True,
                "manual_generated_robin_edit": 0,
                "additional_run": 0,
                "next_candidate": 0,
                "github_write": 0,
                "stop_on_refusal_mismatch_safety_issue_or_unknown": True,
            },
            "classification": {
                "formal_r12_request_text_modified": False,
                "a1_conditions_separate": True,
                "formal_r12_path_compliance_claimed": False,
                "fixed_input_sheet_range_target_expected_preserved": True,
                "automatic_execution_configuration_from_japanese_request": False,
                "t2_auxiliary_pass_inherited": False,
            },
        },
    )
    write_json(
        CYCLE / "preflight.json",
        {
            "schema_version": 1,
            "cycle_id": CYCLE_ID,
            "recorded_at": now,
            "status": "PASS_LOCAL_READY_PENDING_UI_HISTORY_CHECK",
            "checks": {
                "candidate_manifest_identity": True,
                "candidate_and_all_fixed_sha": True,
                "fixed_request_is_verbatim_leading_component": True,
                "a1_conditions_are_separate": True,
                "actual_runtime_paths_in_body": True,
                "helper_and_invocation_paths_and_sha_in_body": True,
                "grader_values_absent_from_body": True,
                "work_matches_template": True,
                "output_absent": True,
                "json_handoff_residue_absent": True,
                "ui_send_history_checked": False,
                "normal_m365_chat_confirmed": False,
            },
            "next_gate": "CONFIRM_A1_G1_NOT_PREVIOUSLY_SENT_IN_NORMAL_M365_CHAT",
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
    print(json.dumps({
        "status": "PASS_LOCAL_READY_PENDING_UI_HISTORY_CHECK",
        "cycle_id": CYCLE_ID,
        "submitted_body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "bundle_sha256": actual_sha["bundle"],
        "runtime": str(RUNTIME.resolve()),
    }, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
