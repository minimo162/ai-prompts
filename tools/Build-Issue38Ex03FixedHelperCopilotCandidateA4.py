#!/usr/bin/env python3
"""Build the non-live EX03 fixed-helper Copilot A4 wiring candidate."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
A3_BUILDER_PATH = ROOT / "tools/Build-Issue38Ex03FixedHelperCopilotCandidateA3.py"
A3_SPEC = importlib.util.spec_from_file_location(
    "issue38_fixed_helper_copilot_a3_builder_for_a4",
    A3_BUILDER_PATH,
)
a3 = importlib.util.module_from_spec(A3_SPEC)
assert A3_SPEC.loader is not None
A3_SPEC.loader.exec_module(a3)

CANDIDATE_ID = "20260918-excel-r12-fixed-helper-a4"
ROUTE_ID = "EX03-R12-FIXED-HELPER-COPILOT-A4"
BASE_COMMIT = "1fe070fbfd0fce57acb65d8a2ee5152f8450a434"
DESTINATION = ROOT / "copilot/versions" / CANDIDATE_ID
A3 = ROOT / "copilot/versions/20260918-excel-r12-fixed-helper-a3"
A3_CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A3-G1"
A4_PROBE = ROOT / "catalog/acceptance/issue38/probes/ex03-r12-fixed-helper-a4"
HELPER = ROOT / "catalog/acceptance/issue38/probes/ex03-r12-fixed-helper/EX03-R12-Fixed-StringTransfer.ps1"
INVOCATION = A4_PROBE / "invocation.json"
LAUNCHER = A4_PROBE / "launcher.ps1"

A3_BUNDLE_NAME = "PAD-Robin-Fixed-Helper-A3-Bundle.txt"
A4_BUNDLE_NAME = "PAD-Robin-Fixed-Helper-A4-Bundle.txt"
EXPECTED_SUCCESS = a3.EXPECTED_SUCCESS
EXPECTED_HELPER_SHA256 = "08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135"
EXPECTED_INVOCATION_SHA256 = "5c5a2008f55296a48f63fa65178aab971e4212455bb2af58e33149bdcaec40d8"
EXPECTED_LAUNCHER_SHA256 = "a286179f8fb7f8febc87f1915cf10965ee0a50769251ecb17573c00926c174d5"
BT = chr(96)

ISSUE_ROOT = ROOT / "catalog/acceptance/issue38"
FIXED_WORK = ISSUE_ROOT / "runs/EX03-attempt1/work.xlsx"
FIXED_OUTPUT = ISSUE_ROOT / "runs/EX03-attempt1/照合結果.xlsx"
A4_JSON_ROOT = ISSUE_ROOT / "runs/EX03-attempt1/a4-helper-json"

SOURCES = {
    "helper": HELPER,
    "invocation": INVOCATION,
    "launcher": LAUNCHER,
    "fixed_request": ISSUE_ROOT / "requests/EX03.txt",
    "fixed_spec": ISSUE_ROOT / "spec.json",
    "fixed_expected": ISSUE_ROOT / "expected.json",
    "formal_r12_status": ISSUE_ROOT / "cycles/EX03-r12-G1/acceptance-status.json",
    "t2_result": ISSUE_ROOT / "probes/ex03-r12-fixed-helper/trials/EX03-R12-FIXED-HELPER-P1-T2/result.json",
    "t2_pad_recopy": ISSUE_ROOT / "probes/ex03-r12-fixed-helper/trials/EX03-R12-FIXED-HELPER-P1-T2/pad-recopy-before-run.robin",
    "a3_builder": A3_BUILDER_PATH,
    "a3_test": ROOT / "tests/Test-Issue38Ex03FixedHelperCopilotCandidateA3.py",
    "a3_instruction": A3 / "agent-instructions.txt",
    "a3_bundle": A3 / "knowledge" / A3_BUNDLE_NAME,
    "a3_manifest": A3 / "manifest.json",
    "a3_response": A3_CYCLE / "copilot-response.txt",
    "a3_assessment": A3_CYCLE / "generation-assessment-final.json",
    "a3_result": A3_CYCLE / "FINAL-RESULT.md",
}

SOURCE_ROLES = {
    "helper": "UNCHANGED_VERIFIER_HELPER",
    "invocation": "A4_VERIFIER_INVOCATION_NOT_COPILOT_ATTACHMENT",
    "launcher": "A4_FIXED_LAUNCHER_NOT_RUN",
    "fixed_request": "UNCHANGED_FIXED_REQUEST_PREFIX",
    "fixed_spec": "UNCHANGED_FIXED_CASE_SHAPE_NOT_BUNDLED",
    "fixed_expected": "UNCHANGED_GRADER_DATA_NOT_BUNDLED",
    "formal_r12_status": "FORMAL_R12_FAIL_BOUNDARY_PRESERVED",
    "t2_result": "AUXILIARY_T2_PASS_BOUNDARY_NOT_INHERITED",
    "t2_pad_recopy": "CAPTURED_RUNSCRIPT_WRAPPER_AND_GATE_SOURCE",
    "a3_builder": "A3_REPRODUCIBLE_BUILDER_PRESERVED",
    "a3_test": "A3_LIMITED_TEST_PRESERVED",
    "a3_instruction": "A3_INSTRUCTION_BASE_PRESERVED",
    "a3_bundle": "A3_BUNDLE_PRESERVED_NOT_ATTACHED_TO_A4",
    "a3_manifest": "A3_MANIFEST_PRESERVED",
    "a3_response": "A3_G1_REFUSAL_PRESERVED",
    "a3_assessment": "A3_G1_FINAL_ASSESSMENT_PRESERVED",
    "a3_result": "A3_G1_FINAL_RESULT_PRESERVED",
}

PROTECTED_PREFIXES = (
    "copilot/versions/20260918-excel-r12-fixed-helper-a1",
    "copilot/versions/20260918-excel-r12-fixed-helper-a2",
    "copilot/versions/20260918-excel-r12-fixed-helper-a3",
    "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A1-G1",
    "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A2-G1",
    "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A3-G1",
    "catalog/acceptance/issue38/cycles/EX03-r12-G1",
    "catalog/acceptance/issue38/probes/ex03-r12-fixed-helper",
    "catalog/acceptance/issue38/fixtures/EX03",
    "catalog/acceptance/issue38/requests/EX03.txt",
    "catalog/acceptance/issue38/spec.json",
    "catalog/acceptance/issue38/expected.json",
    "tools/Build-Issue38Ex03FixedHelperCopilotCandidateA1.py",
    "tools/Build-Issue38Ex03FixedHelperCopilotCandidateA2.py",
    "tools/Build-Issue38Ex03FixedHelperCopilotCandidateA3.py",
    "tests/Test-Issue38Ex03FixedHelperCopilotCandidateA1.py",
    "tests/Test-Issue38Ex03FixedHelperCopilotCandidateA2.py",
    "tests/Test-Issue38Ex03FixedHelperCopilotCandidateA3.py",
)


POSITION_ROWS: tuple[dict[str, Any], ...] = (
    {"order": 1, "input_id": "input1", "workbook": "fixtures/EX03/入力い.xlsx", "sheet": "受取明細", "cell": "D4", "data_table": "Data1", "index": [0, 0], "kind": "text", "helper_index": 1, "target_sheet": "集計先", "target_cell": "F7", "readback": "Readback1", "readback_index": [0, 0]},
    {"order": 2, "input_id": "input1", "workbook": "fixtures/EX03/入力い.xlsx", "sheet": "受取明細", "cell": "E4", "data_table": "Data1", "index": [0, 1], "kind": "number", "target_sheet": "集計先", "target_cell": "G7", "readback": "Readback1", "readback_index": [0, 1]},
    {"order": 3, "input_id": "input1", "workbook": "fixtures/EX03/入力い.xlsx", "sheet": "受取明細", "cell": "D5", "data_table": "Data1", "index": [1, 0], "kind": "text", "helper_index": 2, "target_sheet": "集計先", "target_cell": "F8", "readback": "Readback1", "readback_index": [1, 0]},
    {"order": 4, "input_id": "input1", "workbook": "fixtures/EX03/入力い.xlsx", "sheet": "受取明細", "cell": "E5", "data_table": "Data1", "index": [1, 1], "kind": "number", "target_sheet": "集計先", "target_cell": "G8", "readback": "Readback1", "readback_index": [1, 1]},
    {"order": 5, "input_id": "input1", "workbook": "fixtures/EX03/入力い.xlsx", "sheet": "受取明細", "cell": "D6", "data_table": "Data1", "index": [2, 0], "kind": "text", "helper_index": 3, "target_sheet": "集計先", "target_cell": "F9", "readback": "Readback1", "readback_index": [2, 0]},
    {"order": 6, "input_id": "input1", "workbook": "fixtures/EX03/入力い.xlsx", "sheet": "受取明細", "cell": "E6", "data_table": "Data1", "index": [2, 1], "kind": "number", "target_sheet": "集計先", "target_cell": "G9", "readback": "Readback1", "readback_index": [2, 1]},
    {"order": 7, "input_id": "input2", "workbook": "fixtures/EX03/入力ろ.xlsx", "sheet": "追加項目", "cell": "B2", "data_table": "Data2", "index": [0, 0], "kind": "text", "helper_index": 4, "target_sheet": "追記先", "target_cell": "D5", "readback": "Readback2", "readback_index": [0, 0]},
    {"order": 8, "input_id": "input2", "workbook": "fixtures/EX03/入力ろ.xlsx", "sheet": "追加項目", "cell": "C2", "data_table": "Data2", "index": [0, 1], "kind": "number", "target_sheet": "追記先", "target_cell": "E5", "readback": "Readback2", "readback_index": [0, 1]},
    {"order": 9, "input_id": "input2", "workbook": "fixtures/EX03/入力ろ.xlsx", "sheet": "追加項目", "cell": "D2", "data_table": "Data2", "index": [0, 2], "kind": "text", "helper_index": 6, "target_sheet": "追記先", "target_cell": "F5", "readback": "Readback2", "readback_index": [0, 2]},
    {"order": 10, "input_id": "input2", "workbook": "fixtures/EX03/入力ろ.xlsx", "sheet": "追加項目", "cell": "B3", "data_table": "Data2", "index": [1, 0], "kind": "text", "helper_index": 5, "target_sheet": "追記先", "target_cell": "D6", "readback": "Readback2", "readback_index": [1, 0]},
    {"order": 11, "input_id": "input2", "workbook": "fixtures/EX03/入力ろ.xlsx", "sheet": "追加項目", "cell": "C3", "data_table": "Data2", "index": [1, 1], "kind": "number", "target_sheet": "追記先", "target_cell": "E6", "readback": "Readback2", "readback_index": [1, 1]},
    {"order": 12, "input_id": "input2", "workbook": "fixtures/EX03/入力ろ.xlsx", "sheet": "追加項目", "cell": "D3", "data_table": "Data2", "index": [1, 2], "kind": "text", "helper_index": 7, "target_sheet": "追記先", "target_cell": "F6", "readback": "Readback2", "readback_index": [1, 2]},
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def utf16_units(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.encode("utf-8"))


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def source_reference(row: dict[str, Any]) -> str:
    return f"{row['data_table']}[{row['index'][0]}][{row['index'][1]}]"


def target_reference(row: dict[str, Any]) -> str:
    return f"{row['target_sheet']}!{row['target_cell']}"


def source_cell_reference(row: dict[str, Any]) -> str:
    return f"{row['sheet']}!{row['cell']}"


def build_wiring_spec() -> dict[str, Any]:
    text_rows = sorted(
        (row for row in POSITION_ROWS if row["kind"] == "text"),
        key=lambda row: int(row["helper_index"]),
    )
    numeric_rows = [row for row in POSITION_ROWS if row["kind"] == "number"]
    text_mappings = []
    for row in text_rows:
        index = int(row["helper_index"])
        text_mappings.append(
            {
                "helper_source_index": index,
                "input_id": row["input_id"],
                "input_workbook": row["workbook"],
                "input_sheet": row["sheet"],
                "input_cell": row["cell"],
                "data_table_variable": row["data_table"],
                "data_table_index": row["index"],
                "source_reference": source_reference(row),
                "source_json_file": f"source-{index}.json",
                "source_json_path": str(A4_JSON_ROOT / f"source-{index}.json"),
                "helper_target_sheet": row["target_sheet"],
                "helper_target_cell": row["target_cell"],
            }
        )
    numeric_mappings = [
        {
            "order": index,
            "input_id": row["input_id"],
            "input_workbook": row["workbook"],
            "input_sheet": row["sheet"],
            "input_cell": row["cell"],
            "data_table_variable": row["data_table"],
            "data_table_index": row["index"],
            "source_reference": source_reference(row),
            "target_sheet": row["target_sheet"],
            "target_cell": row["target_cell"],
        }
        for index, row in enumerate(numeric_rows, start=1)
    ]
    comparisons = [
        {
            "order": row["order"],
            "kind": row["kind"],
            "source_workbook": row["workbook"],
            "source_sheet": row["sheet"],
            "source_cell": row["cell"],
            "source_reference": source_reference(row),
            "saved_sheet": row["target_sheet"],
            "saved_cell": row["target_cell"],
            "saved_reference": f"{row['readback']}[{row['readback_index'][0]}][{row['readback_index'][1]}]",
            "source_and_saved_positions_immutable": True,
            "per_position_variable_names_may_be_generated": True,
        }
        for row in POSITION_ROWS
    ]
    return {
        "schema_version": 1,
        "spec_id": "EX03-R12-FIXED-HELPER-A4-WIRING",
        "candidate_id": CANDIDATE_ID,
        "scope": "FIXED_EX03_ONLY_NOT_GENERALIZED",
        "status": "SPECIFICATION_ONLY_NOT_COMPLETE_ROBIN_NOT_CAPTURED_NOT_RUN",
        "inputs": [
            {
                "input_id": "input1",
                "workbook": "fixtures/EX03/入力い.xlsx",
                "sheet": "受取明細",
                "range": "D4:E6",
                "data_table_variable": "Data1",
            },
            {
                "input_id": "input2",
                "workbook": "fixtures/EX03/入力ろ.xlsx",
                "sheet": "追加項目",
                "range": "B2:D3",
                "data_table_variable": "Data2",
            },
        ],
        "runtime": {
            "issue_root": str(ISSUE_ROOT),
            "fixed_work_relative": "runs/EX03-attempt1/work.xlsx",
            "fixed_work_absolute": str(FIXED_WORK),
            "fixed_output_relative": "runs/EX03-attempt1/照合結果.xlsx",
            "fixed_output_absolute": str(FIXED_OUTPUT),
            "a4_json_root_relative": "runs/EX03-attempt1/a4-helper-json",
            "a4_json_root_absolute": str(A4_JSON_ROOT),
            "mode_json_file": "mode.json",
            "mode_source_variable": "RunMode",
            "normal_mode_literal": "NORMAL",
            "helper_path": str(HELPER),
            "helper_sha256": EXPECTED_HELPER_SHA256,
            "invocation_path": str(INVOCATION),
            "invocation_sha256": EXPECTED_INVOCATION_SHA256,
            "launcher_path": str(LAUNCHER),
            "launcher_sha256": EXPECTED_LAUNCHER_SHA256,
            "fixed_relation": [
                "C02 guards the fixed output before input reads, JSON writes, work open, or helper launch.",
                "C04 writes source-1.json through source-7.json and mode.json into the A4 json_root.",
                "C05 opens the fixed request work.xlsx as the editable Work instance.",
                "C06 runs the SHA-pinned A4 launcher; its invocation targets that same fixed work.xlsx and A4 json_root.",
                "The unchanged helper writes the seven text cells into the already-open Work workbook.",
                "Only the exact-success and NORMAL gates permit C09 numeric writes and C10 SaveAs to the fixed output.",
            ],
            "verifier_preplaces": ["work.xlsx", "helper", "invocation.json", "launcher.ps1", "A4 json_root directory"],
            "flow_creates_before_helper": ["source-1.json through source-7.json", "mode.json"],
            "output_precondition": "fixed output does not exist",
        },
        "text_mappings": text_mappings,
        "numeric_mappings": numeric_mappings,
        "readbacks": [
            {"order": 1, "sheet": "集計先", "range": "F7:G9", "variable": "Readback1", "rows": 3, "columns": 2},
            {"order": 2, "sheet": "追記先", "range": "D5:F6", "variable": "Readback2", "rows": 2, "columns": 3},
        ],
        "comparison_contract": {
            "count": 12,
            "order": "input rectangles in request order, each rectangle row-major",
            "source_and_saved_positions_immutable": True,
            "per_position_variable_names_may_be_generated": True,
            "comparison_primitive": "captured JSON probe string equality from C11",
            "positions": comparisons,
        },
        "generation_contract": {
            "explicit_copy_and_connection_from_captured_components_allowed": True,
            "completed_robin_required_as_generation_source": False,
            "unknown_action_argument_enum_or_control_fabrication_allowed": False,
            "new_pad_loop_allowed": False,
            "cell_or_grader_values_included": False,
        },
    }


WIRING_SPEC = build_wiring_spec()

INVOCATION_OBJECT = {
    "schema_version": 1,
    "prototype_id": "EX03-R12-FIXED-HELPER-A4-VERIFIER",
    "scope": "FIXED_EX03_ONLY_NOT_GENERALIZED",
    "target_workbook": str(FIXED_WORK),
    "json_root": str(A4_JSON_ROOT),
    "text_writes": [
        {
            "source_index": mapping["helper_source_index"],
            "source_label": mapping["source_reference"],
            "sheet": mapping["helper_target_sheet"],
            "cell": mapping["helper_target_cell"],
        }
        for mapping in WIRING_SPEC["text_mappings"]
    ],
}


def expected_launcher_text() -> str:
    return f"""$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

$helperPath = '{HELPER}'
$invocationPath = '{INVOCATION}'
$expectedHelperSha256 = '{EXPECTED_HELPER_SHA256}'
$expectedInvocationSha256 = '{EXPECTED_INVOCATION_SHA256}'
$expectedSuccess = '{{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}}'

function Stop-Launcher {{
    param([string]$Code, [int]$ExitCode)
    $failure = [ordered]@{{ status = 'ERROR'; error_code = $Code }}
    [Console]::Out.Write([string]($failure | ConvertTo-Json -Compress))
    exit $ExitCode
}}

function Get-Sha256 {{
    param([string]$Path)
    $stream = [IO.File]::OpenRead($Path)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {{
        return ([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-', '').ToLowerInvariant()
    }}
    finally {{
        $algorithm.Dispose()
        $stream.Dispose()
    }}
}}

if (-not (Test-Path -LiteralPath $helperPath -PathType Leaf)) {{
    Stop-Launcher 'HELPER_NOT_FOUND' 41
}}
if (-not (Test-Path -LiteralPath $invocationPath -PathType Leaf)) {{
    Stop-Launcher 'INVOCATION_NOT_FOUND' 42
}}

$actualHelperSha256 = Get-Sha256 $helperPath
if ($actualHelperSha256 -cne $expectedHelperSha256) {{
    Stop-Launcher 'HELPER_SHA256_MISMATCH' 43
}}
$actualInvocationSha256 = Get-Sha256 $invocationPath
if ($actualInvocationSha256 -cne $expectedInvocationSha256) {{
    Stop-Launcher 'INVOCATION_SHA256_MISMATCH' 44
}}

try {{
    $helperOutput = (& $helperPath -InvocationPath $invocationPath | Out-String).Trim()
}}
catch {{
    Stop-Launcher 'HELPER_INVOCATION_FAILED' 45
}}

if ([string]::IsNullOrWhiteSpace($helperOutput)) {{
    Stop-Launcher 'HELPER_SUCCESS_OUTPUT_MISSING' 46
}}
if ($helperOutput -cne $expectedSuccess) {{
    Stop-Launcher 'HELPER_UNEXPECTED_OUTPUT' 47
}}

[Console]::Out.Write($helperOutput)
"""


ROUTE_INSTRUCTIONS = f"""【Excel値転記・固定helper別経路 {CANDIDATE_ID}】
このA4はA3とA3-G1拒否を変更せず、固定EX03の接続仕様と固定依頼workへ揃えた検証者管理invocation/launcherだけを追加した未使用候補です。正式r12 FAIL、T2補助PASS、A1/A2/A3拒否、旧558 raw差分を分離して保持し、A4へ成功として継承しません。

Route IDは {ROUTE_ID} です。標準入力は変更していない固定EX03依頼、この指示全文、同じ候補IDの {BT}{A4_BUNDLE_NAME}{BT} 実添付です。bundle内のA4 WIRING SPEC、IN-BUNDLE INDEX、SOURCE-LINE ASSEMBLY RULES、CONTROL BLOCK MAP、COMPONENT blocksだけを生成根拠にします。

A4 WIRING SPECは完成Robin、採取原文、実行結果、採点値ではありません。7個の文字列位置について入力cell/DataTable index、source-N.json、helper source_index、転記先を固定し、5個の数値位置、2個のreadback矩形、12位置の比較順を固定します。source/savedの位置と順序は変更せず、位置ごとの一意な変数名だけ生成できます。

C04はWIRING SPECどおり7個の文字列JSONとmode.jsonをA4専用json_rootへ書きます。C09は同specの5個だけをWriteCellします。C10は固定outputへSaveAsして一度だけ再開し、Readback1=集計先!F7:G9、Readback2=追記先!D5:F6をこの順で読みます。C11はspecの12位置を固定順でJSON比較します。明示された複製と接続は許可し、新しいPAD LOOPは作りません。

C02のguardは {FIXED_OUTPUT}、C05のeditable workは {FIXED_WORK} です。C04のjson_rootは {A4_JSON_ROOT} です。C06はA4 bundleに収録した固定component全体を逐語使用します。その外側RunScript形はT2採取済み、内包scriptはSHA固定A4 launcherで、invocationは同じfixed workとA4 json_rootを指します。helper本体はSHA {EXPECTED_HELPER_SHA256} のまま変更しません。

外側output guard、exact-success、NORMALの三重接続と、両失敗側close/no-SaveAsはCONTROL BLOCK MAPどおりです。空、ERROR、別出力、別modeでは数値書込み、SaveAs、完成状態へ進みません。

採取済みcomponentとWIRING SPECから明示的に複製・接続して生成できます。完成Robinが教材にないことだけを理由に拒否しません。一方、未知の命令、引数、列挙値、制御構造を捏造しません。WIRING SPECとcomponentを照合しても根拠がない構文または接続が残る場合だけRobinを出さず、component ID、出典命令行、未解決の前後を具体的に報告します。

入力と原本はReadOnly、検証者が用意したworkだけを編集します。network、delete、既存output上書き、Invoke-Expression、外部取得SHA、権限・security・Excel設定変更を追加しません。

回答は説明の後に、全工程のRobinだけを正確に1個のMarkdown {BT}text{BT} コードブロックへ入れます。コードブロック内へ説明、見出し、行番号、JSON、Markdownフェンス文字列、省略記号、疑似コードを入れません。先頭行と最終非空行は実際のPAD命令です。

このA4はCopilot未送信、PAD保存・再コピー未実施、PAD/Excel Run 0です。生成後も無修正原文の安全検査と保存・再コピー一致が通るまで、完成・実行済み・受入済みと表示しません。
"""

SEND_CONDITIONS = f"""【{ROUTE_ID} / G1 準備済み送信本文条件 — 今回は未送信】
候補IDは {CANDIDATE_ID}、Route IDは {ROUTE_ID} です。固定EX03依頼、同版指示全文、同版 {A4_BUNDLE_NAME} を一組として扱います。

A4 WIRING SPECは固定EX03の12位置、7個のhelper文字列経路、5個の数値書込み、2個のreadback矩形、12比較順、fixed work/outputとA4専用json_rootの関係を固定します。完成Robin、採取原文、実行結果、採点値ではありません。採取済みcomponentの明示的複製・接続を許可し、完成Robin不在だけを拒否理由にしません。未知のPAD構文・引数・列挙値・制御構造は作りません。

helper SHA-256は {EXPECTED_HELPER_SHA256}、A4 invocation SHA-256は {EXPECTED_INVOCATION_SHA256}、A4 launcher SHA-256は {EXPECTED_LAUNCHER_SHA256} です。workは {FIXED_WORK}、outputは {FIXED_OUTPUT}、json_rootは {A4_JSON_ROOT} です。

C06はbundle内のA4固定componentを逐語使用します。WIRING SPECの位置と順序は不変で、位置ごとの一意な変数名だけ生成できます。回答形式、安全条件、停止条件は同版指示全文のままです。この本文は将来の1回送信用に固定した準備物であり、今回Copilotへ送信していません。
"""


def validate_static_files() -> dict[str, Any]:
    if INVOCATION.read_bytes() != canonical_json_bytes(INVOCATION_OBJECT):
        raise ValueError("A4 invocation differs from canonical WIRING SPEC projection")
    if sha256(INVOCATION) != EXPECTED_INVOCATION_SHA256:
        raise ValueError("A4 invocation SHA mismatch")
    if LAUNCHER.read_text(encoding="utf-8") != expected_launcher_text():
        raise ValueError("A4 launcher content mismatch")
    if sha256(LAUNCHER) != EXPECTED_LAUNCHER_SHA256:
        raise ValueError("A4 launcher SHA mismatch")
    if sha256(HELPER) != EXPECTED_HELPER_SHA256:
        raise ValueError("Unchanged helper SHA mismatch")
    return {
        "helper_sha256": sha256(HELPER),
        "invocation_sha256": sha256(INVOCATION),
        "launcher_sha256": sha256(LAUNCHER),
    }


def expand_range(value: str) -> list[str]:
    match = re.fullmatch(r"([A-Z]+)([0-9]+):([A-Z]+)([0-9]+)", value)
    if not match:
        raise ValueError(f"Unsupported range: {value}")
    start_column, start_row, end_column, end_row = match.groups()

    def column_number(column: str) -> int:
        result = 0
        for character in column:
            result = result * 26 + ord(character) - 64
        return result

    def column_name(number: int) -> str:
        result = ""
        while number:
            number, remainder = divmod(number - 1, 26)
            result = chr(65 + remainder) + result
        return result

    return [
        f"{column_name(column)}{row}"
        for row in range(int(start_row), int(end_row) + 1)
        for column in range(column_number(start_column), column_number(end_column) + 1)
    ]


def validate_wiring_spec(spec: dict[str, Any] = WIRING_SPEC) -> dict[str, Any]:
    text = spec["text_mappings"]
    numeric = spec["numeric_mappings"]
    comparisons = spec["comparison_contract"]["positions"]
    if len(text) != 7 or len(numeric) != 5 or len(comparisons) != 12:
        raise ValueError("A4 wiring count mismatch")
    if [item["helper_source_index"] for item in text] != list(range(1, 8)):
        raise ValueError("Helper source indexes are not exactly 1..7")
    if [item["source_json_file"] for item in text] != [f"source-{index}.json" for index in range(1, 8)]:
        raise ValueError("Helper JSON filenames are not exactly source-1..7")
    expected_sources = [(row["workbook"], row["sheet"], row["cell"]) for row in POSITION_ROWS]
    expected_targets = [(row["target_sheet"], row["target_cell"]) for row in POSITION_ROWS]
    actual_sources = [(item["source_workbook"], item["source_sheet"], item["source_cell"]) for item in comparisons]
    actual_targets = [(item["saved_sheet"], item["saved_cell"]) for item in comparisons]
    if actual_sources != expected_sources or actual_targets != expected_targets:
        raise ValueError("Comparison order or immutable positions changed")
    if [item["order"] for item in comparisons] != list(range(1, 13)):
        raise ValueError("Comparison order is not exactly 1..12")
    text_sources = {(item["input_workbook"], item["input_sheet"], item["input_cell"]) for item in text}
    numeric_sources = {(item["input_workbook"], item["input_sheet"], item["input_cell"]) for item in numeric}
    text_targets = {(item["helper_target_sheet"], item["helper_target_cell"]) for item in text}
    numeric_targets = {(item["target_sheet"], item["target_cell"]) for item in numeric}
    if text_sources & numeric_sources or text_targets & numeric_targets:
        raise ValueError("Text and numeric positions overlap")
    if text_sources | numeric_sources != set(expected_sources):
        raise ValueError("Source rectangle coverage mismatch")
    if text_targets | numeric_targets != set(expected_targets):
        raise ValueError("Target rectangle coverage mismatch")
    readback_targets = {
        (readback["sheet"], cell)
        for readback in spec["readbacks"]
        for cell in expand_range(readback["range"])
    }
    if readback_targets != set(expected_targets):
        raise ValueError("Readback rectangles do not cover all and only targets")
    if [readback["variable"] for readback in spec["readbacks"]] != ["Readback1", "Readback2"]:
        raise ValueError("Readback variable names changed")
    serialized = json.dumps(spec, ensure_ascii=False)
    for forbidden in ("expected_value", "grading_value", "cell_value"):
        if forbidden in serialized:
            raise ValueError(f"Grader field leaked into WIRING SPEC: {forbidden}")
    if spec["generation_contract"]["cell_or_grader_values_included"]:
        raise ValueError("WIRING SPEC claims grader values")
    return {
        "text_count": len(text),
        "numeric_count": len(numeric),
        "readback_count": len(spec["readbacks"]),
        "comparison_count": len(comparisons),
        "source_coverage_count": len(text_sources | numeric_sources),
        "target_coverage_count": len(text_targets | numeric_targets),
        "text_numeric_source_overlap": 0,
        "text_numeric_target_overlap": 0,
        "fixed_order": True,
    }


def protected_snapshot() -> dict[str, Any]:
    completed = subprocess.run(
        ["git", "ls-tree", "-r", "-z", "--name-only", BASE_COMMIT, "--", *PROTECTED_PREFIXES],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    paths = sorted(
        item.decode("utf-8")
        for item in completed.stdout.split(b"\0")
        if item
    )
    if not paths:
        raise ValueError("Protected base snapshot is empty")
    digest = hashlib.sha256()
    for path in paths:
        base = subprocess.run(
            ["git", "show", f"{BASE_COMMIT}:{path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        current_path = ROOT / path
        if not current_path.is_file() or current_path.read_bytes() != base:
            raise ValueError(f"Protected A1-A3/r12/T2 evidence changed: {path}")
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(base)
        digest.update(b"\0")
    return {
        "base_commit": BASE_COMMIT,
        "prefixes": list(PROTECTED_PREFIXES),
        "file_count": len(paths),
        "aggregate_sha256": digest.hexdigest(),
        "all_match_base_commit": True,
    }


def encode_robin_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')


def captured_c06() -> bytes:
    return a3.a2.component_excerpt(next(component for component in a3.COMPONENTS if component["id"] == "C06_FIXED_LAUNCHER_RUNSCRIPT"))


def render_a4_c06() -> bytes:
    launcher = LAUNCHER.read_text(encoding="utf-8")
    if not launcher.endswith("\n"):
        raise ValueError("A4 launcher must end with LF")
    encoded = encode_robin_string(launcher[:-1])
    return (
        "    Scripting.RunPowershellScript.RunScript Script: $'''"
        + encoded
        + "''' ScriptOutput=> PowershellOutput\n"
    ).encode("utf-8")


def component_marker(component_id: str, edge: str) -> bytes:
    return f"COMPONENT {component_id} {edge}\n".encode("utf-8")


def extract_component(bundle: bytes, component_id: str) -> bytes:
    begin = component_marker(component_id, "BEGIN")
    end = component_marker(component_id, "END")
    if bundle.count(begin) != 1 or bundle.count(end) != 1:
        raise ValueError(f"Component marker count changed: {component_id}")
    start = bundle.index(begin) + len(begin)
    finish = bundle.index(end, start)
    return bundle[start:finish]


def component_excerpt(component: dict[str, Any]) -> bytes:
    if component["id"] == "C06_FIXED_LAUNCHER_RUNSCRIPT":
        return render_a4_c06()
    return a3.a2.component_excerpt(component)


def validate_c06_derivation() -> dict[str, Any]:
    captured = captured_c06().decode("utf-8").replace("\r\n", "\n")
    derived = render_a4_c06().decode("utf-8")
    prefix = "Scripting.RunPowershellScript.RunScript Script: $'''"
    suffix = "''' ScriptOutput=> PowershellOutput"
    captured_start = captured.index(prefix)
    captured_end = captured.index(suffix, captured_start)
    derived_start = derived.index(prefix)
    derived_end = derived.index(suffix, derived_start)
    if captured[: captured_start + len(prefix)] != derived[: derived_start + len(prefix)]:
        raise ValueError("A4 C06 captured RunScript prefix changed")
    if captured[captured_end:] != derived[derived_end:]:
        raise ValueError("A4 C06 captured RunScript suffix changed")
    decoded = a3.a2.embedded_script(derived)
    if decoded.encode("utf-8") + b"\n" != LAUNCHER.read_bytes():
        raise ValueError("A4 C06 does not decode to the fixed A4 launcher")
    return {
        "captured_wrapper_source_sha256": sha256(SOURCES["t2_pad_recopy"]),
        "captured_prefix_and_suffix_exact": True,
        "embedded_launcher_terminal_lf_restored_sha256": sha256_bytes(decoded.encode("utf-8") + b"\n"),
        "component_sha256": sha256_bytes(render_a4_c06()),
        "execution_status": "NOT_RUN_A4",
    }


def render_instruction() -> tuple[str, dict[str, Any]]:
    before = SOURCES["a3_instruction"].read_text(encoding="utf-8")
    if before.count(a3.ROUTE_INSTRUCTIONS) != 1:
        raise ValueError("A3 route instruction block changed")
    after_route = before.replace(a3.ROUTE_INSTRUCTIONS, ROUTE_INSTRUCTIONS)
    bundle_name_count = after_route.count(A3_BUNDLE_NAME)
    if bundle_name_count < 1:
        raise ValueError("A3 bundle references changed")
    after_bundle = after_route.replace(A3_BUNDLE_NAME, A4_BUNDLE_NAME)
    component_marker_count = after_bundle.count("`RAW_COMPONENT`")
    if component_marker_count != 1:
        raise ValueError("A3 RAW_COMPONENT instruction reference changed")
    after = after_bundle.replace("`RAW_COMPONENT`", "`COMPONENT`")
    if (
        a3.ROUTE_INSTRUCTIONS in after
        or A3_BUNDLE_NAME in after
        or a3.CANDIDATE_ID in after
        or "`RAW_COMPONENT`" in after
    ):
        raise ValueError("A3 route-specific instruction text remained in A4")
    if utf16_units(after) > 8000:
        raise ValueError(f"A4 instruction exceeds 8000 UTF-16 units: {utf16_units(after)}")
    return after, {
        "schema_version": 1,
        "base_candidate": a3.CANDIDATE_ID,
        "base_instruction_path": relative(SOURCES["a3_instruction"]),
        "base_instruction_sha256": sha256(SOURCES["a3_instruction"]),
        "candidate_id": CANDIDATE_ID,
        "transforms": [
            {"kind": "ROUTE_BLOCK_REPLACEMENT", "occurrences": 1, "before": a3.ROUTE_INSTRUCTIONS, "after": ROUTE_INSTRUCTIONS},
            {"kind": "BUNDLE_FILENAME_REPLACEMENT", "occurrences": bundle_name_count, "before": A3_BUNDLE_NAME, "after": A4_BUNDLE_NAME},
            {"kind": "COMPONENT_MARKER_REPLACEMENT", "occurrences": component_marker_count, "before": "`RAW_COMPONENT`", "after": "`COMPONENT`"},
        ],
        "other_transformations": 0,
        "reconstructs_candidate_exactly": True,
    }


def render_human_wiring(spec: dict[str, Any]) -> list[str]:
    lines = [
        "A4 WIRING SPEC — HUMAN-READABLE FIXED MAP",
        "TEXT: input cell / DataTable index -> JSON file -> helper source_index -> target",
    ]
    for item in spec["text_mappings"]:
        lines.append(
            f"- {item['input_workbook']} {item['input_sheet']}!{item['input_cell']} / {item['source_reference']} -> "
            f"{item['source_json_file']} -> {item['helper_source_index']} -> {item['helper_target_sheet']}!{item['helper_target_cell']}"
        )
    lines.append("NUMERIC: input cell / DataTable index -> target")
    for item in spec["numeric_mappings"]:
        lines.append(
            f"- {item['input_workbook']} {item['input_sheet']}!{item['input_cell']} / {item['source_reference']} -> "
            f"{item['target_sheet']}!{item['target_cell']}"
        )
    lines.append("READBACKS")
    for item in spec["readbacks"]:
        lines.append(f"- {item['order']}: {item['sheet']}!{item['range']} -> {item['variable']}")
    lines.append("COMPARISON ORDER (source -> saved position)")
    for item in spec["comparison_contract"]["positions"]:
        lines.append(
            f"- {item['order']:02d}: {item['source_workbook']} {item['source_sheet']}!{item['source_cell']} / "
            f"{item['source_reference']} -> {item['saved_sheet']}!{item['saved_cell']} / {item['saved_reference']}"
        )
    lines.extend(
        [
            "RUNTIME RELATION",
            f"- work: {spec['runtime']['fixed_work_absolute']}",
            f"- output guard and SaveAs: {spec['runtime']['fixed_output_absolute']}",
            f"- A4 json_root: {spec['runtime']['a4_json_root_absolute']}",
            f"- invocation: {spec['runtime']['invocation_path']} / {spec['runtime']['invocation_sha256']}",
            f"- launcher: {spec['runtime']['launcher_path']} / {spec['runtime']['launcher_sha256']}",
            f"- unchanged helper: {spec['runtime']['helper_path']} / {spec['runtime']['helper_sha256']}",
        ]
    )
    for relation in spec["runtime"]["fixed_relation"]:
        lines.append(f"- {relation}")
    return lines


def render_bundle(actual_sha: dict[str, str]) -> tuple[bytes, list[dict[str, Any]]]:
    c06_validation = validate_c06_derivation()
    component_records = []
    for component in a3.COMPONENTS:
        excerpt = component_excerpt(component)
        record = {
            **component,
            "component_kind": "DERIVED_FIXED_A4_LAUNCHER_NOT_RUN" if component["id"] == "C06_FIXED_LAUNCHER_RUNSCRIPT" else "RAW_CAPTURE_SLICE",
            "source_path": relative(a3.SOURCES[component["source"]]),
            "source_sha256": sha256(a3.SOURCES[component["source"]]),
            "excerpt_sha256": sha256_bytes(excerpt),
            "excerpt_bytes": len(excerpt),
        }
        if component["id"] == "C06_FIXED_LAUNCHER_RUNSCRIPT":
            record.update(
                {
                    "title": "fixed A4 Run PowerShell Script component from captured wrapper plus A4 launcher",
                    "immutable_syntax": [
                        "entire derived A4 component",
                        "captured RunScript prefix and ScriptOutput suffix",
                        "A4 fixed paths and SHA literals",
                        "expectedSuccess",
                    ],
                    "source_path": relative(SOURCES["t2_pad_recopy"]),
                    "source_sha256": actual_sha["t2_pad_recopy"],
                    "embedded_launcher_path": relative(LAUNCHER),
                    "embedded_launcher_sha256": actual_sha["launcher"],
                    "prior_execution_scope": "outer RunScript wrapper executed in T2; A4 launcher content not run",
                }
            )
        component_records.append(record)

    lines = [
        "PAD Robin fixed-helper A4 self-contained wiring bundle",
        f"candidate_id: {CANDIDATE_ID}",
        f"route_id: {ROUTE_ID}",
        f"bundle_filename: {A4_BUNDLE_NAME}",
        "status: LOCAL_PREPARED_LIMITED_NON_LIVE_NOT_RUN",
        "",
        "BOUNDARY",
        "- A1-A3, their refusal evidence, formal r12, and T2 auxiliary evidence remain unchanged.",
        "- A4 adds a fixed WIRING SPEC plus an A4 verifier invocation/launcher aligned to the fixed request work.",
        "- WIRING SPEC is not a completed Robin, raw capture, execution result, or grading-value source.",
        "- Captured components may be copied and connected exactly as listed; a completed Robin is not required as a generation source.",
        "- Unknown actions, arguments, enum values, and control shapes remain forbidden.",
        "- C06 is derived from the captured T2 RunScript wrapper plus the SHA-pinned A4 launcher and has not been run.",
        "",
        *render_human_wiring(WIRING_SPEC),
        "",
        "A4_WIRING_SPEC_JSON_BEGIN",
        json.dumps(WIRING_SPEC, ensure_ascii=False, indent=2),
        "A4_WIRING_SPEC_JSON_END",
        "",
        "IN-BUNDLE INDEX",
    ]
    for record in component_records:
        dependencies = ",".join(record["dependencies"]) if record["dependencies"] else "none"
        lines.extend(
            [
                f"[{record['id']}] {record['title']}",
                f"  component_kind: {record['component_kind']}",
                f"  source: {record['source_path']} lines {record['start_line']}-{record['end_line']}",
                f"  source_sha256: {record['source_sha256']}",
                f"  excerpt_sha256: {record['excerpt_sha256']}",
                f"  dependencies: {dependencies}",
                f"  mutable_parameters: {'; '.join(record['mutable_parameters']) if record['mutable_parameters'] else 'none'}",
                f"  immutable_syntax: {'; '.join(record['immutable_syntax'])}",
                f"  prior_execution_scope: {record.get('prior_execution_scope', record['execution_scope'])}",
            ]
        )
        if record["id"] == "C06_FIXED_LAUNCHER_RUNSCRIPT":
            lines.append(f"  embedded_launcher: {record['embedded_launcher_path']} / {record['embedded_launcher_sha256']}")

    lines.extend(["", "SOURCE-LINE ASSEMBLY RULES"])
    for rule in a3.ASSEMBLY_RULES:
        lines.extend([f"[{rule['id']}] component={rule['component']}", f"  purpose: {rule['purpose']}"])
        for binding in rule["line_bindings"]:
            lines.append(
                f"  source_lines: {relative(a3.SOURCES[binding['source']])}:{binding['lines'][0]}-{binding['lines'][1]} => {binding['role']}"
            )
        lines.append("  immutable_parts: " + "; ".join(rule["immutable_parts"]))
        lines.append("  mutable_parts: " + "; ".join(rule["mutable_parts"]))
        lines.append("  definitions: " + "; ".join(rule["definitions"]))
        lines.append("  references: " + "; ".join(rule["references"]))
        for index, step in enumerate(rule["execution_order"], start=1):
            lines.append(f"  order_{index}: {step}")
        lines.append(f"  connection: {rule['connection']}")
        lines.append(f"  copy_method: {rule['copy_method']}")

    lines.extend(["", "CONTROL BLOCK MAP"])
    for event in a3.CONTROL_EVENTS:
        lines.append(
            f"- {event['sequence']:02d} {event['event']} {event['block']} => "
            f"{event['component']} / {relative(a3.SOURCES[event['source']])}:{event['line']}"
        )
    lines.extend(
        [
            "- C12 line 193 closes NORMAL_MODE.",
            "- C12 line 197 closes EXACT_SUCCESS.",
            "- C12 line 198 closes OUTPUT_GUARD.",
            "- C12 lines 191 and 195 close Work without SaveAs in the two failure branches.",
            "",
            "COMPONENT BLOCKS",
        ]
    )
    parts: list[bytes] = [("\n".join(lines) + "\n").encode("utf-8")]
    for record in component_records:
        parts.append((f"\nCOMPONENT METADATA {record['id']}\n").encode("utf-8"))
        parts.append(component_marker(record["id"], "BEGIN"))
        parts.append(component_excerpt(record))
        parts.append(component_marker(record["id"], "END"))
    parts.append(
        (
            "\nEND OF SELF-CONTAINED A4 BUNDLE\n"
            "The blocks and WIRING SPEC are generation inputs, not a complete captured or executed A4 Robin.\n"
        ).encode("utf-8")
    )
    bundle = b"".join(parts)
    for record in component_records:
        if extract_component(bundle, record["id"]) != component_excerpt(record):
            raise ValueError(f"Component changed while rendering: {record['id']}")
    if c06_validation["embedded_launcher_terminal_lf_restored_sha256"] != EXPECTED_LAUNCHER_SHA256:
        raise ValueError("A4 launcher restoration hash mismatch")
    return bundle, component_records


def source_record(name: str, path: Path) -> dict[str, Any]:
    return {
        "path": relative(path),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "role": SOURCE_ROLES[name],
        "copilot_attachment": False,
    }


def artifact_record(path: Path, destination: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(destination).as_posix(),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def payload_sha256(destination: Path, paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.relative_to(destination).as_posix()):
        digest.update(path.relative_to(destination).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def render_coverage(wiring_validation: dict[str, Any]) -> str:
    return f"""# {CANDIDATE_ID} limited non-live coverage

This preparation does not claim Copilot generation, PAD save/re-copy, PAD or
Excel execution, or acceptance.

| Limited check | Result |
| --- | --- |
| fixed wiring coverage | PASS: {wiring_validation['text_count']} text, {wiring_validation['numeric_count']} numeric, {wiring_validation['readback_count']} readbacks, {wiring_validation['comparison_count']} comparisons |
| source/target coverage and disjointness | PASS: 12 sources, 12 targets, zero text/numeric overlap |
| fixed runtime relation | PASS: fixed request work/output, explicit A4 json_root, SHA-pinned A4 invocation/launcher |
| helper preservation | PASS: unchanged SHA {EXPECTED_HELPER_SHA256} |
| component provenance | PASS: 11 exact captured slices; C06 captured wrapper plus fixed A4 launcher, NOT_RUN_A4 |
| teaching/test independence | PASS: no complete Robin and no cell/grader values; WIRING SPEC is specification only |

Full regression was not run. A1-A3, formal r12, T2 auxiliary evidence, fixed
request/spec/expected, and EX03 fixtures are byte-equal to {BASE_COMMIT}.
"""


def render_placement() -> str:
    return f"""# {CANDIDATE_ID} placement and runtime design

Route: {BT}{ROUTE_ID}{BT}. This is local preparation only. If a later turn is
separately authorized, send {BT}submitted-body.txt{BT} unchanged and attach exactly
{BT}knowledge/{A4_BUNDLE_NAME}{BT}.

## Fixed runtime

| Role | Path | SHA-256 |
| --- | --- | --- |
| unchanged helper | {BT}{HELPER}{BT} | {BT}{EXPECTED_HELPER_SHA256}{BT} |
| A4 verifier invocation | {BT}{INVOCATION}{BT} | {BT}{EXPECTED_INVOCATION_SHA256}{BT} |
| A4 launcher | {BT}{LAUNCHER}{BT} | {BT}{EXPECTED_LAUNCHER_SHA256}{BT} |
| fixed work | {BT}{FIXED_WORK}{BT} | verifier preplaces the fixed request copy |
| A4 JSON root | {BT}{A4_JSON_ROOT}{BT} | verifier precreates; flow writes 7 source JSON files and mode.json |
| fixed output | {BT}{FIXED_OUTPUT}{BT} | must be absent before the flow; C02 guards and C10 SaveAs uses this path |

The invocation targets the same work opened by C05. C04 writes into the exact
json_root read by the unchanged helper through C06. Exact-success plus NORMAL
must pass before five numeric writes or SaveAs. Readback and comparison then use
the fixed two rectangles and twelve positions in {BT}wiring-spec.json{BT}.

No complete Robin, Copilot response, PAD/Excel run, acceptance result, or grader
values were created for A4.
"""


def build(destination: Path = DESTINATION) -> dict[str, Any]:
    destination = Path(destination)
    if destination.exists() and any(path.is_file() for path in destination.rglob("*")):
        raise ValueError(f"Candidate already exists: {destination}")

    static_validation = validate_static_files()
    wiring_validation = validate_wiring_spec()
    preserved = protected_snapshot()
    actual_sha = {name: sha256(path) for name, path in SOURCES.items()}

    formal = json.loads(SOURCES["formal_r12_status"].read_text(encoding="utf-8"))
    t2 = json.loads(SOURCES["t2_result"].read_text(encoding="utf-8"))
    a3_assessment = json.loads(SOURCES["a3_assessment"].read_text(encoding="utf-8"))
    if formal["accepted"] or not formal["status"].startswith("FAIL_"):
        raise ValueError("Formal r12 failure boundary changed")
    if t2["decision"] != "PASS_FIXED_HELPER_AUXILIARY_NORMAL_RUN1":
        raise ValueError("T2 auxiliary boundary changed")
    if a3_assessment["final_status"] != "STOPPED_FAIL_REFUSAL":
        raise ValueError("A3 refusal boundary changed")

    instruction, instruction_delta = render_instruction()
    request = SOURCES["fixed_request"].read_text(encoding="utf-8").rstrip("\r\n")
    conditions = SEND_CONDITIONS.rstrip("\r\n") + "\n"
    body = request + "\n\n" + conditions.rstrip("\r\n") + "\n\n" + instruction.rstrip("\r\n") + "\n"
    bundle, component_records = render_bundle(actual_sha)
    c06_validation = validate_c06_derivation()

    instruction_path = destination / "agent-instructions.txt"
    conditions_path = destination / "send-conditions.txt"
    body_path = destination / "submitted-body.txt"
    bundle_path = destination / "knowledge" / A4_BUNDLE_NAME
    wiring_path = destination / "wiring-spec.json"
    rules_path = destination / "assembly-rules.json"
    delta_path = destination / "instruction-delta.json"
    coverage_path = destination / "COVERAGE.md"
    placement_path = destination / "PLACEMENT.md"
    verification_path = destination / "non-live-verification.json"

    write_text(instruction_path, instruction)
    write_text(conditions_path, conditions)
    write_text(body_path, body)
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.write_bytes(bundle)
    write_json(wiring_path, WIRING_SPEC)
    write_json(
        rules_path,
        {
            "schema_version": 1,
            "candidate_id": CANDIDATE_ID,
            "status": "RULES_PRESERVED_FROM_A3_PLUS_FIXED_A4_WIRING_NOT_RUN",
            "rules": a3.ASSEMBLY_RULES,
            "control_events": a3.CONTROL_EVENTS,
            "control_validation": a3.validate_control_events(),
            "derived_example": {
                "status": "A3_DIFFERENT_CONDITION_EXAMPLE_PRESERVED_NOT_RUN",
                "records": a3.build_derived_example(),
                "validation": a3.validate_example_variables(a3.build_derived_example()),
            },
        },
    )
    instruction_delta["candidate_instruction_sha256"] = sha256(instruction_path)
    instruction_delta["candidate_instruction_utf16_units"] = utf16_units(instruction)
    write_json(delta_path, instruction_delta)
    write_text(coverage_path, render_coverage(wiring_validation))
    write_text(placement_path, render_placement())

    verification = {
        "schema_version": 1,
        "candidate_id": CANDIDATE_ID,
        "route_id": ROUTE_ID,
        "decision": "PASS_LIMITED_NON_LIVE_A4_WIRING_PREPARATION_ONLY",
        "authorized_checks": {
            "wiring_coverage_disjointness_and_order": {"status": "PASS", **wiring_validation},
            "runtime_path_and_sha_alignment": {"status": "PASS", **static_validation},
            "c06_captured_wrapper_plus_fixed_launcher": {"status": "PASS", **c06_validation},
            "helper_preservation": {"status": "PASS", "unchanged_sha256": EXPECTED_HELPER_SHA256},
            "no_complete_robin_or_grader_values": {
                "status": "PASS",
                "complete_robin_present": False,
                "cell_or_grader_values_present": False,
                "wiring_spec_status": WIRING_SPEC["status"],
            },
            "protected_evidence": {"status": "PASS", **preserved},
        },
        "preserved_boundaries": {
            "formal_r12_status": formal["status"],
            "formal_r12_accepted": formal["accepted"],
            "t2_decision": t2["decision"],
            "t2_pass_inherited": False,
            "a3_final_status": a3_assessment["final_status"],
            "a3_result_reused": False,
            "legacy_558_difference_record": "PRESERVED_NOT_RECLASSIFIED",
        },
        "scope": {
            "copilot_send_count": 0,
            "pad_save_recopy_count": 0,
            "pad_run_count": 0,
            "excel_run_count": 0,
            "new_capture_count": 0,
            "full_regression": "NOT_RUN_BY_SCOPE",
            "github_write_count": 0,
        },
    }
    write_json(verification_path, verification)

    artifact_paths = {
        "instruction": instruction_path,
        "send_conditions": conditions_path,
        "submitted_body": body_path,
        "bundle": bundle_path,
        "wiring_spec": wiring_path,
        "assembly_rules": rules_path,
        "instruction_delta": delta_path,
        "coverage": coverage_path,
        "placement": placement_path,
        "non_live_verification": verification_path,
    }
    manifest = {
        "schema_version": 1,
        "candidate_id": CANDIDATE_ID,
        "route_id": ROUTE_ID,
        "status": "LOCAL_PREPARED_LIMITED_NON_LIVE_NOT_COPILOT_OR_PAD_ACCEPTED",
        "base_commit": BASE_COMMIT,
        "successor_to": a3.CANDIDATE_ID,
        "a1_a2_a3_modified": False,
        "replaces_formal_r12": False,
        "inherits_t2_auxiliary_pass": False,
        "artifacts": {name: artifact_record(path, destination) for name, path in artifact_paths.items()},
        "candidate_payload_sha256": payload_sha256(destination, artifact_paths.values()),
        "candidate_payload_sha256_algorithm": "SHA256(sorted relative UTF-8 path + NUL + bytes + NUL)",
        "source_evidence": {name: source_record(name, path) for name, path in SOURCES.items()},
        "protected_snapshot": preserved,
        "wiring_contract": {
            "spec_id": WIRING_SPEC["spec_id"],
            "text_count": 7,
            "numeric_count": 5,
            "readback_count": 2,
            "comparison_count": 12,
            "source_and_saved_positions_immutable": True,
            "per_position_variable_names_may_be_generated": True,
            "complete_robin_required_as_generation_source": False,
            "unknown_pad_syntax_fabrication_allowed": False,
        },
        "fixed_runtime_contract": {
            "work": str(FIXED_WORK),
            "output": str(FIXED_OUTPUT),
            "json_root": str(A4_JSON_ROOT),
            "helper_sha256": EXPECTED_HELPER_SHA256,
            "invocation_sha256": EXPECTED_INVOCATION_SHA256,
            "launcher_sha256": EXPECTED_LAUNCHER_SHA256,
            "decoded_launcher_terminal_lf_restored_sha256": c06_validation["embedded_launcher_terminal_lf_restored_sha256"],
            "success_output": EXPECTED_SUCCESS,
        },
        "component_records": component_records,
        "teaching_independence": {
            "complete_fixed_ex03_robin_in_bundle": False,
            "fixed_expected_or_grader_values_in_bundle": False,
            "fixed_ex03_wiring_spec_in_bundle": True,
            "helper_body_in_bundle": False,
            "invocation_json_in_bundle": False,
            "a4_fixed_launcher_runscript_in_bundle": True,
            "a4_launcher_execution_status": "NOT_RUN",
            "status": "PASS",
        },
        "limited_verification": verification["authorized_checks"],
        "preserved_boundaries": verification["preserved_boundaries"],
        "scope": verification["scope"],
    }
    write_json(destination / "manifest.json", manifest)
    return manifest


def main() -> int:
    manifest = build()
    print(
        json.dumps(
            {
                "candidate_id": manifest["candidate_id"],
                "route_id": manifest["route_id"],
                "candidate_payload_sha256": manifest["candidate_payload_sha256"],
                "status": manifest["status"],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
