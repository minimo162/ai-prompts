#!/usr/bin/env python3
"""Build the non-live EX03 fixed-helper Copilot A3 assembly-rule candidate."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
A2_BUILDER_PATH = ROOT / "tools/Build-Issue38Ex03FixedHelperCopilotCandidateA2.py"
A2_SPEC = importlib.util.spec_from_file_location(
    "issue38_fixed_helper_copilot_a2_builder_for_a3",
    A2_BUILDER_PATH,
)
a2 = importlib.util.module_from_spec(A2_SPEC)
assert A2_SPEC.loader is not None
A2_SPEC.loader.exec_module(a2)

CANDIDATE_ID = "20260918-excel-r12-fixed-helper-a3"
ROUTE_ID = "EX03-R12-FIXED-HELPER-COPILOT-A3"
BASE_COMMIT = "37d4ef462aca52d1a6855ce549eac87463b008ca"
DESTINATION = ROOT / "copilot/versions" / CANDIDATE_ID
A2 = ROOT / "copilot/versions/20260918-excel-r12-fixed-helper-a2"
A2_CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A2-G1"
RUNTIME = a2.T1 / "runtime"
WORK = RUNTIME / "work.xlsx"
OUTPUT = RUNTIME / "照合結果.xlsx"

A2_BUNDLE_NAME = "PAD-Robin-Fixed-Helper-A2-Bundle.txt"
A3_BUNDLE_NAME = "PAD-Robin-Fixed-Helper-A3-Bundle.txt"
BT = chr(96)
EXPECTED_SUCCESS = a2.EXPECTED_SUCCESS

SOURCES = dict(a2.SOURCES)
SOURCES.update(
    {
        "a2_builder": A2_BUILDER_PATH,
        "a2_test": ROOT / "tests/Test-Issue38Ex03FixedHelperCopilotCandidateA2.py",
        "a2_instruction": A2 / "agent-instructions.txt",
        "a2_bundle": A2 / "knowledge" / A2_BUNDLE_NAME,
        "a2_manifest": A2 / "manifest.json",
        "a2_coverage": A2 / "COVERAGE.md",
        "a2_placement": A2 / "PLACEMENT.md",
        "a2_non_live": A2 / "non-live-verification.json",
        "a2_response": A2_CYCLE / "copilot-response.txt",
        "a2_assessment": A2_CYCLE / "generation-assessment.json",
        "a2_result": A2_CYCLE / "RESULT.md",
    }
)

EXPECTED_SOURCE_SHA256 = dict(a2.EXPECTED_SOURCE_SHA256)
EXPECTED_SOURCE_SHA256.update(
    {
        "a2_builder": "38119eb83844bc9be75c06d0afd883f4cc1fd4d0ed064591e492fe2350cc777a",
        "a2_test": "02340fa7cbcc4610211864a5d2a053dd11e8ca3ae45a0fe3880aa3d04c2f74a1",
        "a2_instruction": "def1af576bac79d5dbf321ac38d7702d3d968932b2e0767265f9544eb18ebe60",
        "a2_bundle": "009a830d7a1bb431c1f02933e45933c2d7466260c616e46114255605dc3e5b1c",
        "a2_manifest": "afe054f0e532c7c69b1359b54fe07dc05c42bb99e196be07cf3dd826977f008d",
        "a2_coverage": "8813198b1f76c6034918294908fa86ec2c0a2637e186bd1c6aead65d97e2f2d3",
        "a2_placement": "74f8fe4013ceb492fc2ebed661a417749f46c47d147e4ea2c64487909cde556a",
        "a2_non_live": "8520b68a557a49c2324a3c6e78efc2111de2758cb6136d43e033a960bd0b57f0",
        "a2_response": "5f26b25cddd880ce0bd4c4869a87c7a1a31829ebd22459d8d2e67bd52408061d",
        "a2_assessment": "8c813a695bd82e92045df63dc87167313a1557e8ff41a3bd4af359057f878c2e",
        "a2_result": "5bf717f3053c873d9e0f071a027b344b17d9cd279343fbdbfeacfdc6c21217f7",
    }
)

SOURCE_ROLES = dict(a2.SOURCE_ROLES)
SOURCE_ROLES.update(
    {
        "a2_builder": "A2_REPRODUCIBLE_BUILDER_PRESERVED",
        "a2_test": "A2_LIMITED_TEST_PRESERVED",
        "a2_instruction": "A2_INSTRUCTION_BASE_PRESERVED",
        "a2_bundle": "A2_TEACHING_BUNDLE_PRESERVED_NOT_ATTACHED_TO_A3",
        "a2_manifest": "A2_MANIFEST_PRESERVED",
        "a2_coverage": "A2_COVERAGE_PRESERVED",
        "a2_placement": "A2_PLACEMENT_PRESERVED",
        "a2_non_live": "A2_NON_LIVE_RESULT_PRESERVED",
        "a2_response": "A2_G1_REFUSAL_PRESERVED",
        "a2_assessment": "A2_G1_ASSESSMENT_PRESERVED",
        "a2_result": "A2_G1_RESULT_PRESERVED",
    }
)

PRESERVE_FROM_BASE = (
    "tools/Build-Issue38Ex03FixedHelperCopilotCandidateA2.py",
    "tests/Test-Issue38Ex03FixedHelperCopilotCandidateA2.py",
    "copilot/versions/20260918-excel-r12-fixed-helper-a2/agent-instructions.txt",
    "copilot/versions/20260918-excel-r12-fixed-helper-a2/COVERAGE.md",
    "copilot/versions/20260918-excel-r12-fixed-helper-a2/knowledge/PAD-Robin-Fixed-Helper-A2-Bundle.txt",
    "copilot/versions/20260918-excel-r12-fixed-helper-a2/manifest.json",
    "copilot/versions/20260918-excel-r12-fixed-helper-a2/non-live-verification.json",
    "copilot/versions/20260918-excel-r12-fixed-helper-a2/PLACEMENT.md",
    "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A2-G1/RESULT.md",
    "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A2-G1/copilot-response.txt",
    "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A2-G1/generation-acceptance-criteria.json",
    "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A2-G1/generation-assessment.json",
    "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A2-G1/history-check.json",
    "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A2-G1/live-send.json",
    "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A2-G1/plan.json",
    "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A2-G1/post-stop-integrity.json",
    "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A2-G1/preflight.json",
    "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A2-G1/protected-before.json",
    "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A2-G1/send-conditions.txt",
    "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A2-G1/submitted-body.txt",
)

COMPONENTS = a2.COMPONENTS
REQUIREMENT_COVERAGE = a2.REQUIREMENT_COVERAGE

ROUTE_INSTRUCTIONS = f"""【Excel値転記・固定helper別経路 20260918-excel-r12-fixed-helper-a3】
このA3はA2とA2-G1拒否を変更せず、拒否で不足とされた「採取済み部品の組立規則」だけを追加した後継の未使用候補です。正式r12 FAIL、固定helper T2補助PASS、A1/A2拒否、旧558 raw差分を分離して保持し、A3へ成功として継承しません。

Route IDは {ROUTE_ID} です。組立規則IDは AR04_EXPLICIT_JSON_HANDOFF、AR09_EXPLICIT_NUMERIC_WRITES、AR10_MULTIPLE_RECTANGLE_READBACK、AR11_MULTIPLE_JSON_COMPARISONS です。

標準入力は、変更していない固定EX03依頼、この指示全文、同じ候補IDの {BT}{A3_BUNDLE_NAME}{BT} 実添付です。bundle内のIN-BUNDLE INDEX、SOURCE-LINE ASSEMBLY RULES、CONTROL BLOCK MAP、DERIVED SMALL EXAMPLE、RAW_COMPONENTだけを参照し、外部索引や未添付原文を生成前提にしません。

逐語保持の対象はC06_FIXED_LAUNCHER_RUNSCRIPT全体と、各組立規則でimmutableとされた未変更構文部分だけです。mutableとして明示した変数名、DataTable索引、パス、sheet、range、target、出力変数、状態名、必要回数の明示的複製、接続位置、ブロック深度に合わせた先頭インデントは変更できます。RAW_COMPONENT全体の逐語複写を、明示変更部分まで含めて要求しません。

C04はSET定義群、JSON変換群、mode定義、source書込み群、mode書込みの順で、必要な命令行を明示的に複製します。C09は成功分岐内で数値変数を先に定義し、対象sheetを明示してWriteCellを1行ずつ複製します。C10はSaveAsと再開を各1回だけ行い、sheet切替＋TypedValues読取りの2行を矩形ごとに複製してから1回だけ閉じます。C11は保存値定義群、JSON変換群、source/saved比較群、完了状態の順で位置ごとに明示的に複製します。新しいPAD LOOP、未採取の命令、引数、列挙値、制御構造を作りません。

外側output guardはC02のIF/ELSEを開き、C12末尾ENDが閉じます。C07のexact-success IFの内側にNORMAL IFを置き、成功処理はNORMAL側だけです。C12の最初のELSE/ENDはNORMAL分岐、次のELSE/ENDはexact-success分岐、最後のENDはoutput guardに対応します。両失敗側はWorkをcloseし、SaveAsを含めません。

bundleの小例は別条件の派生断片で、採取原文、完成Robin、固定EX03配線ではなくNOT_CAPTURED_NOT_COMPLETE_NOT_RUNです。行ごとの出典と許可置換を示すためだけに使い、例のE番号や注釈を生成Robinへ入れません。完成した固定EX03 Robin、採点値、固定EX03専用全配線、完成フローの採取・実行済み原文が教材にないことは生成拒否の理由にしません。

helper、invocation、launcher、runtime、固定依頼、期待値、正式出力形式は変更しません。検証者がhelperとinvocationを固定パスへ事前配置します。C06は固定パス、SHA、expectedSuccess、外側RunScript行を含めて変更せず使い、helper本体やinvocation JSONを生成・展開・書換えしません。

IN-BUNDLE INDEXと組立規則を照合し、実際に根拠がない命令または接続が残る場合だけRobinを出さず、component ID、出典命令行、未解決の接続前後を具体的に報告します。完成回答を丸ごと教材へ足す要求で補いません。

入力と原本はReadOnly、検証者が用意したwork copyだけを編集します。既存output時は入力読取り、JSON生成、work起動、helper実行より前に停止します。空、ERROR、別出力、別modeでは数値書込み、SaveAs、完成状態へ進みません。network、delete、既存output上書き、Invoke-Expression、外部取得SHA、権限・security・Excel設定変更を追加しません。

回答は説明の後に、全工程のRobinだけを正確に1個のMarkdown {BT}text{BT} コードブロックへ入れます。コードブロック内へ説明、見出し、E番号、行番号、Plain Text、JSON、Markdownフェンス文字列、省略記号、疑似コードを入れません。先頭行と最終非空行は実際のPAD命令です。

このA3はCopilot未送信、PAD保存・再コピー未実施、PAD/Excel Run 0です。生成後も無修正原文の安全検査と保存・再コピー一致が通るまで、完成・実行済み・受入済みと表示しません。
"""

SEND_CONDITIONS = f"""【{ROUTE_ID} / G1 準備済み送信本文条件 — 今回は未送信】
候補IDは {CANDIDATE_ID}、Route IDは {ROUTE_ID} です。固定EX03依頼、同版指示全文、同版 {A3_BUNDLE_NAME} を一組として扱います。

helper、invocation、runtime、固定依頼、期待値、出力形式はA2から変更しません。helper SHA-256は {a2.EXPECTED_SOURCE_SHA256['helper']}、invocation SHA-256は {a2.EXPECTED_SOURCE_SHA256['invocation']}、launcher SHA-256は {a2.EXPECTED_SOURCE_SHA256['launcher']} です。専用runtimeは {RUNTIME.resolve()}、workは {WORK.resolve()}、outputは {OUTPUT.resolve()} です。

bundleのSOURCE-LINE ASSEMBLY RULESに従い、C04、C09、C10、C11を採取済み命令行の明示的複製で構成してください。新しいPAD LOOPは作りません。CONTROL BLOCK MAPどおりにoutput guard、exact-success、NORMAL、両失敗側close、3個のENDを接続してください。

逐語保持は固定C06全体と各規則のimmutable部分に限定します。規則でmutableとされた置換、複製、接続、先頭インデント調整は許可します。完成フローの採取・実行済み原文は生成前の必須条件ではありません。未知の命令、引数、列挙値、制御構造は捏造しません。

DERIVED SMALL EXAMPLEは別条件の未実行断片であり、完成回答としてコピーしません。固定EX03の完成Robin、採点値、全体配線を要求・推測・教材化しません。根拠不足が残る場合は、component ID、出典命令行、接続前後だけを具体的に報告し、完成回答の丸ごと追加を求めません。

回答形式、安全条件、停止条件は同版指示全文のままです。この本文は将来の1回送信用に固定した準備物であり、今回Copilotへ送信していません。
"""

ASSEMBLY_RULES: tuple[dict[str, Any], ...] = (
    {
        "id": "AR04_EXPLICIT_JSON_HANDOFF",
        "component": "C04_JSON_FILE_HANDOFF",
        "purpose": "explicitly duplicate source-slot JSON handoff commands without a PAD loop",
        "line_bindings": [
            {"source": "r2r3_normal_recopy", "lines": [12, 15], "role": "SET source variable definitions"},
            {"source": "r2r3_normal_recopy", "lines": [16, 19], "role": "source JSON conversions"},
            {"source": "r2r3_normal_recopy", "lines": [20, 21], "role": "single mode definition and conversion"},
            {"source": "r2r3_normal_recopy", "lines": [22, 25], "role": "source JSON file writes"},
            {"source": "r2r3_normal_recopy", "lines": [26, 26], "role": "single mode file write"},
        ],
        "immutable_parts": [
            "SET command shape",
            "ConvertCustomObjectToJson CustomObject probe wrapper and Json output shape",
            "File.WriteText AppendNewLine False, Overwrite, UTF8 arguments",
            "mode definition/conversion/write occurs once",
        ],
        "mutable_parts": [
            "source variable and JSON variable names",
            "DataTable row/column indexes",
            "source-N JSON path and N",
            "explicit source-slot copy count",
            "leading indentation needed by the outer ELSE body",
        ],
        "definitions": ["each source variable", "each source JSON variable", "RunMode", "RunModeJson"],
        "references": ["C03 DataTable outputs", "each source JSON variable at its matching write"],
        "execution_order": [
            "all source SET definitions",
            "all source JSON conversions",
            "RunMode SET and JSON conversion once",
            "all matching source-N writes",
            "mode write once",
        ],
        "connection": "after all C03 reads and before C05/C06; every reference follows its definition",
        "copy_method": "copy the captured command lines explicitly once per slot; do not create a LOOP",
    },
    {
        "id": "AR09_EXPLICIT_NUMERIC_WRITES",
        "component": "C09_NUMERIC_WRITE",
        "purpose": "define numeric source variables and duplicate WriteCell explicitly inside the success branch",
        "line_bindings": [
            {"source": "r2r3_normal_recopy", "lines": [12, 15], "role": "SET-from-DataTable definition template"},
            {"source": "r2r3_normal_recopy", "lines": [28, 28], "role": "target-sheet activation template"},
            {"source": "r2r3_normal_recopy", "lines": [168, 168], "role": "single branch-entry marker"},
            {"source": "r2r3_normal_recopy", "lines": [169, 169], "role": "WriteCell template"},
        ],
        "immutable_parts": [
            "SET definition shape",
            "ActivateWorksheetByName action and Name argument shape",
            "NumericWriteEntered marker occurs once",
            "WriteCell action and Instance/Value/Column/Row argument names",
        ],
        "mutable_parts": [
            "numeric variable names and DataTable indexes",
            "target sheet",
            "target column and row",
            "explicit WriteCell copy count",
            "leading indentation for the NORMAL success body",
        ],
        "definitions": ["every numeric source variable before its first WriteCell", "NumericWriteEntered once"],
        "references": ["C03 DataTable outputs", "Work from C05", "numeric variable at each WriteCell"],
        "execution_order": [
            "C07 exact-success and NORMAL gates pass",
            "define all numeric source variables",
            "activate the first target sheet",
            "set NumericWriteEntered once",
            "emit each WriteCell in source order, activating a different sheet before its group",
        ],
        "connection": "inside the NORMAL branch after C07 line 103 and before C10 SaveAs",
        "copy_method": "copy SET, activation, and WriteCell lines explicitly; do not create a LOOP",
    },
    {
        "id": "AR10_MULTIPLE_RECTANGLE_READBACK",
        "component": "C10_SAVE_CLOSE_REOPEN_READBACK",
        "purpose": "save/reopen once and duplicate only activation plus TypedValues read for each rectangle",
        "line_bindings": [
            {"source": "r2r3_normal_recopy", "lines": [170, 173], "role": "single SaveAs marker, SaveAs, close, read-only reopen"},
            {"source": "r2r3_normal_recopy", "lines": [174, 175], "role": "rectangle activation and TypedValues read pair"},
            {"source": "r2r3_normal_recopy", "lines": [176, 176], "role": "single close after all rectangle reads"},
        ],
        "immutable_parts": [
            "SaveAs OpenXmlWorkbook shape",
            "close Work before read-only reopen",
            "ReadOnly True and UseMachineLocale False",
            "TypedValues and FirstLineIsHeader False",
            "close Reopened once after the final read",
        ],
        "mutable_parts": [
            "output path",
            "sheet, start/end columns and rows",
            "readback variable name",
            "explicit activation/read pair copy count",
        ],
        "definitions": ["Reopened at the single reopen", "one readback variable per rectangle"],
        "references": ["Work from C05", "output path", "Reopened for every activation/read and final close"],
        "execution_order": [
            "set SaveAsEntered once",
            "SaveAs once",
            "close Work once",
            "reopen output ReadOnly once",
            "for each rectangle explicitly emit activation then read",
            "close Reopened once",
        ],
        "connection": "after the last C09 WriteCell and before C11 saved-value definitions",
        "copy_method": "copy only the captured activation/read pair per rectangle; do not duplicate SaveAs/reopen and do not create a LOOP",
    },
    {
        "id": "AR11_MULTIPLE_JSON_COMPARISONS",
        "component": "C11_JSON_VALUE_TYPE_COMPARE",
        "purpose": "duplicate saved-slot definitions, JSON conversions, and equality comparisons by position",
        "line_bindings": [
            {"source": "r2r3_normal_recopy", "lines": [177, 180], "role": "saved variable definitions"},
            {"source": "r2r3_normal_recopy", "lines": [181, 184], "role": "saved JSON conversions"},
            {"source": "r2r3_normal_recopy", "lines": [185, 188], "role": "source JSON versus saved JSON comparisons"},
            {"source": "r2r3_normal_recopy", "lines": [189, 189], "role": "single success-state assignment"},
        ],
        "immutable_parts": [
            "SET saved variable shape",
            "ConvertCustomObjectToJson probe wrapper and Json output shape",
            "JSON string equality shape",
            "success-state assignment occurs once after all comparisons",
        ],
        "mutable_parts": [
            "readback variable and row/column indexes",
            "saved/source JSON and boolean result variable names",
            "explicit position copy count",
            "final success-state variable and label",
        ],
        "definitions": ["every saved variable", "every saved JSON variable", "every comparison boolean", "final state"],
        "references": ["all C10 readback variables", "matching source JSON variables", "matching saved JSON variables"],
        "execution_order": [
            "define every saved variable in fixed position order",
            "convert every saved value to JSON in the same order",
            "compare matching source and saved JSON variables in the same order",
            "set success state once",
        ],
        "connection": "after C10 closes Reopened and before C12 begins the NORMAL failure ELSE",
        "copy_method": "copy each captured command line explicitly per position; do not create a LOOP",
    },
)

CONTROL_EVENTS: tuple[dict[str, Any], ...] = (
    {"sequence": 1, "component": "C02_OUTPUT_GUARD", "source": "r2r3_normal_recopy", "line": 5, "event": "OPEN", "block": "OUTPUT_GUARD"},
    {"sequence": 2, "component": "C02_OUTPUT_GUARD", "source": "r2r3_normal_recopy", "line": 7, "event": "ELSE", "block": "OUTPUT_GUARD"},
    {"sequence": 3, "component": "C06_FIXED_LAUNCHER_RUNSCRIPT", "source": "t2_pad_recopy", "line": 100, "event": "BODY", "block": "OUTPUT_GUARD"},
    {"sequence": 4, "component": "C07_EXACT_SUCCESS_MODE_GATE", "source": "t2_pad_recopy", "line": 101, "event": "OPEN", "block": "EXACT_SUCCESS"},
    {"sequence": 5, "component": "C07_EXACT_SUCCESS_MODE_GATE", "source": "t2_pad_recopy", "line": 102, "event": "OPEN", "block": "NORMAL_MODE"},
    {"sequence": 6, "component": "C07_EXACT_SUCCESS_MODE_GATE", "source": "t2_pad_recopy", "line": 103, "event": "SUCCESS_BODY_START", "block": "NORMAL_MODE"},
    {"sequence": 7, "component": "C12_FAILURE_CLOSE_NO_SAVE", "source": "r2r3_normal_recopy", "line": 190, "event": "ELSE", "block": "NORMAL_MODE"},
    {"sequence": 8, "component": "C12_FAILURE_CLOSE_NO_SAVE", "source": "r2r3_normal_recopy", "line": 191, "event": "CLOSE_WORK_NO_SAVE", "block": "NORMAL_MODE"},
    {"sequence": 9, "component": "C12_FAILURE_CLOSE_NO_SAVE", "source": "r2r3_normal_recopy", "line": 193, "event": "END", "block": "NORMAL_MODE"},
    {"sequence": 10, "component": "C12_FAILURE_CLOSE_NO_SAVE", "source": "r2r3_normal_recopy", "line": 194, "event": "ELSE", "block": "EXACT_SUCCESS"},
    {"sequence": 11, "component": "C12_FAILURE_CLOSE_NO_SAVE", "source": "r2r3_normal_recopy", "line": 195, "event": "CLOSE_WORK_NO_SAVE", "block": "EXACT_SUCCESS"},
    {"sequence": 12, "component": "C12_FAILURE_CLOSE_NO_SAVE", "source": "r2r3_normal_recopy", "line": 197, "event": "END", "block": "EXACT_SUCCESS"},
    {"sequence": 13, "component": "C12_FAILURE_CLOSE_NO_SAVE", "source": "r2r3_normal_recopy", "line": 198, "event": "END", "block": "OUTPUT_GUARD"},
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


def source_line(source: str, line_number: int) -> str:
    lines = SOURCES[source].read_text(encoding="utf-8").splitlines()
    if line_number < 1 or line_number > len(lines):
        raise ValueError(f"Invalid source line {source}:{line_number}")
    return lines[line_number - 1]


def literal_argument_token(line: str, argument: str) -> str:
    prefix = f"{argument}: $'''"
    if line.count(prefix) != 1:
        raise ValueError(f"Expected one {argument} literal in {line}")
    rest = line.split(prefix, 1)[1]
    value = rest.split("'''", 1)[0]
    return prefix + value + "'''"


def derived_record(
    rule_id: str,
    source: str,
    line_number: int,
    replacements: Iterable[tuple[str, str]] = (),
    *,
    defines: Iterable[str] = (),
    references: Iterable[str] = (),
) -> dict[str, Any]:
    template = source_line(source, line_number)
    masked = template
    mutable: list[dict[str, str]] = []
    markers: list[tuple[str, str]] = []
    for index, (old, new) in enumerate(replacements, start=1):
        if masked.count(old) != 1:
            raise ValueError(
                f"Mutable token must occur exactly once at {source}:{line_number}: {old!r}"
            )
        marker = f"{{MUTABLE_{index}}}"
        masked = masked.replace(old, marker, 1)
        markers.append((marker, new))
        mutable.append({"source_token": old, "derived_token": new})
    derived = masked
    for marker, value in markers:
        derived = derived.replace(marker, value)
    for variable in tuple(defines) + tuple(references):
        if variable not in derived:
            raise ValueError(
                f"Declared variable {variable!r} absent from derived line {source}:{line_number}"
            )
    return {
        "rule_id": rule_id,
        "source": source,
        "source_path": relative(SOURCES[source]),
        "source_line": line_number,
        "template_sha256": sha256_bytes(template.encode("utf-8")),
        "immutable_skeleton_sha256": sha256_bytes(masked.encode("utf-8")),
        "mutable_replacements": mutable,
        "defines": list(defines),
        "references": list(references),
        "text": derived,
    }


def build_derived_example() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    root = r"C:\\A3-DERIVED-NOT-RUN"
    r2 = "r2r3_normal_recopy"

    for index in range(1, 5):
        records.append(
            derived_record(
                "AR04_EXPLICIT_JSON_HANDOFF",
                r2,
                12,
                (
                    ("SET Source1 TO", f"SET DemoSource{index} TO"),
                    ("SourceData[0][0]", f"DemoData[0][{index - 1}]"),
                ),
                defines=(f"DemoSource{index}",),
                references=("DemoData",),
            )
        )
    for index in range(1, 5):
        records.append(
            derived_record(
                "AR04_EXPLICIT_JSON_HANDOFF",
                r2,
                16,
                (
                    ("CustomObject: { 'probe': Source1 }", f"CustomObject: {{ 'probe': DemoSource{index} }}"),
                    ("Json=> Source1Json", f"Json=> DemoSource{index}Json"),
                ),
                defines=(f"DemoSource{index}Json",),
                references=(f"DemoSource{index}",),
            )
        )
    records.append(
        derived_record(
            "AR04_EXPLICIT_JSON_HANDOFF",
            r2,
            20,
            defines=("RunMode",),
        )
    )
    records.append(
        derived_record(
            "AR04_EXPLICIT_JSON_HANDOFF",
            r2,
            21,
            defines=("RunModeJson",),
            references=("RunMode",),
        )
    )
    source_write = source_line(r2, 22)
    old_source_path = literal_argument_token(source_write, "File")
    for index in range(1, 5):
        records.append(
            derived_record(
                "AR04_EXPLICIT_JSON_HANDOFF",
                r2,
                22,
                (
                    (old_source_path, f"File: $'''{root}\\\\source-{index}.json'''"),
                    ("TextToWrite: Source1Json", f"TextToWrite: DemoSource{index}Json"),
                ),
                references=(f"DemoSource{index}Json",),
            )
        )
    mode_write = source_line(r2, 26)
    records.append(
        derived_record(
            "AR04_EXPLICIT_JSON_HANDOFF",
            r2,
            26,
            (
                (
                    literal_argument_token(mode_write, "File"),
                    f"File: $'''{root}\\\\mode.json'''",
                ),
            ),
            references=("RunModeJson",),
        )
    )

    activation = source_line(r2, 28)
    records.append(
        derived_record(
            "AR09_EXPLICIT_NUMERIC_WRITES",
            r2,
            28,
            ((literal_argument_token(activation, "Name"), "Name: $'''DemoTargetOne'''"),),
            references=("Work",),
        )
    )
    records.append(
        derived_record(
            "AR09_EXPLICIT_NUMERIC_WRITES",
            r2,
            168,
            defines=("NumericWriteEntered",),
        )
    )
    write_cell = source_line(r2, 169)
    records.append(
        derived_record(
            "AR09_EXPLICIT_NUMERIC_WRITES",
            r2,
            169,
            (
                ("Value: Source4", "Value: DemoSource3"),
                (literal_argument_token(write_cell, "Column"), "Column: $'''B'''"),
                ("Row: 2", "Row: 2"),
            ),
            references=("Work", "DemoSource3"),
        )
    )
    records.append(
        derived_record(
            "AR09_EXPLICIT_NUMERIC_WRITES",
            r2,
            28,
            ((literal_argument_token(activation, "Name"), "Name: $'''DemoTargetTwo'''"),),
            references=("Work",),
        )
    )
    records.append(
        derived_record(
            "AR09_EXPLICIT_NUMERIC_WRITES",
            r2,
            169,
            (
                ("Value: Source4", "Value: DemoSource4"),
                (literal_argument_token(write_cell, "Column"), "Column: $'''D'''"),
                ("Row: 2", "Row: 4"),
            ),
            references=("Work", "DemoSource4"),
        )
    )

    records.append(
        derived_record(
            "AR10_MULTIPLE_RECTANGLE_READBACK",
            r2,
            170,
            defines=("SaveAsEntered",),
        )
    )
    save_as = source_line(r2, 171)
    records.append(
        derived_record(
            "AR10_MULTIPLE_RECTANGLE_READBACK",
            r2,
            171,
            (
                (
                    literal_argument_token(save_as, "DocumentPath"),
                    f"DocumentPath: $'''{root}\\\\demo-output.xlsx'''",
                ),
            ),
            references=("Work",),
        )
    )
    records.append(
        derived_record(
            "AR10_MULTIPLE_RECTANGLE_READBACK",
            r2,
            172,
            references=("Work",),
        )
    )
    reopen = source_line(r2, 173)
    records.append(
        derived_record(
            "AR10_MULTIPLE_RECTANGLE_READBACK",
            r2,
            173,
            (
                (
                    literal_argument_token(reopen, "Path"),
                    f"Path: $'''{root}\\\\demo-output.xlsx'''",
                ),
            ),
            defines=("Reopened",),
        )
    )
    read_activation = source_line(r2, 174)
    read_cells = source_line(r2, 175)
    rectangle_specs = (
        ("DemoTargetOne", "A", 2, "B", 2, "DemoReadbackOne"),
        ("DemoTargetTwo", "C", 4, "D", 4, "DemoReadbackTwo"),
    )
    for sheet, start_col, start_row, end_col, end_row, output_var in rectangle_specs:
        records.append(
            derived_record(
                "AR10_MULTIPLE_RECTANGLE_READBACK",
                r2,
                174,
                (
                    (
                        literal_argument_token(read_activation, "Name"),
                        f"Name: $'''{sheet}'''",
                    ),
                ),
                references=("Reopened",),
            )
        )
        records.append(
            derived_record(
                "AR10_MULTIPLE_RECTANGLE_READBACK",
                r2,
                175,
                (
                    (
                        literal_argument_token(read_cells, "StartColumn"),
                        f"StartColumn: $'''{start_col}'''",
                    ),
                    ("StartRow: 2", f"StartRow: {start_row}"),
                    (
                        literal_argument_token(read_cells, "EndColumn"),
                        f"EndColumn: $'''{end_col}'''",
                    ),
                    ("EndRow: 2", f"EndRow: {end_row}"),
                    ("RangeValue=> Readback", f"RangeValue=> {output_var}"),
                ),
                defines=(output_var,),
                references=("Reopened",),
            )
        )
    records.append(
        derived_record(
            "AR10_MULTIPLE_RECTANGLE_READBACK",
            r2,
            176,
            references=("Reopened",),
        )
    )

    saved_specs = (
        ("DemoSaved1", "DemoReadbackOne[0][0]"),
        ("DemoSaved2", "DemoReadbackOne[0][1]"),
        ("DemoSaved3", "DemoReadbackTwo[0][0]"),
        ("DemoSaved4", "DemoReadbackTwo[0][1]"),
    )
    for saved, readback_ref in saved_specs:
        records.append(
            derived_record(
                "AR11_MULTIPLE_JSON_COMPARISONS",
                r2,
                177,
                (
                    ("SET Saved1 TO", f"SET {saved} TO"),
                    ("Readback[0][0]", readback_ref),
                ),
                defines=(saved,),
                references=(readback_ref.split("[", 1)[0],),
            )
        )
    for index in range(1, 5):
        records.append(
            derived_record(
                "AR11_MULTIPLE_JSON_COMPARISONS",
                r2,
                181,
                (
                    ("CustomObject: { 'probe': Saved1 }", f"CustomObject: {{ 'probe': DemoSaved{index} }}"),
                    ("Json=> Saved1Json", f"Json=> DemoSaved{index}Json"),
                ),
                defines=(f"DemoSaved{index}Json",),
                references=(f"DemoSaved{index}",),
            )
        )
    for index in range(1, 5):
        records.append(
            derived_record(
                "AR11_MULTIPLE_JSON_COMPARISONS",
                r2,
                185,
                (
                    ("SET Source1VsSaved TO", f"SET DemoMatch{index} TO"),
                    (
                        "Source1Json = Saved1Json",
                        f"DemoSource{index}Json = DemoSaved{index}Json",
                    ),
                ),
                defines=(f"DemoMatch{index}",),
                references=(f"DemoSource{index}Json", f"DemoSaved{index}Json"),
            )
        )
    final_state = source_line(r2, 189)
    records.append(
        derived_record(
            "AR11_MULTIPLE_JSON_COMPARISONS",
            r2,
            189,
            (
                ("SET ProbeState TO", "SET DemoState TO"),
                (
                    "$'''SUCCESS_GATE_PASSED_SAVED_READBACK_READY'''",
                    "$'''DERIVED_EXAMPLE_READY_NOT_RUN'''",
                ),
            ),
            defines=("DemoState",),
        )
    )
    return records


def validate_example_variables(records: list[dict[str, Any]]) -> dict[str, Any]:
    defined = {"DemoData", "Work"}
    unresolved: list[dict[str, str]] = []
    for index, record in enumerate(records, start=1):
        for variable in record["references"]:
            if variable not in defined:
                unresolved.append({"line": f"E{index:03d}", "variable": variable})
        defined.update(record["defines"])
    if unresolved:
        raise ValueError(f"Derived example has forward/undefined references: {unresolved}")
    if any(
        re.search(r"^\s*(LOOP|FOREACH)\b", record["text"], flags=re.IGNORECASE)
        for record in records
    ):
        raise ValueError("Derived example introduced a new PAD loop command")
    return {
        "predefined": ["DemoData", "Work"],
        "defined_count": len(defined),
        "unresolved_references": [],
        "execution_order_valid": True,
        "new_pad_loop_commands": 0,
    }


def validate_control_events() -> dict[str, Any]:
    stack: list[str] = []
    closed: list[str] = []
    for expected_sequence, event in enumerate(CONTROL_EVENTS, start=1):
        if event["sequence"] != expected_sequence:
            raise ValueError("Control-event sequence is not contiguous")
        kind = event["event"]
        block = event["block"]
        if kind == "OPEN":
            stack.append(block)
        elif kind in {"ELSE", "SUCCESS_BODY_START"}:
            if not stack or stack[-1] != block:
                raise ValueError(f"Control event {kind} does not target current block {block}")
        elif kind == "END":
            if not stack or stack[-1] != block:
                raise ValueError(f"END does not close current block {block}")
            closed.append(stack.pop())
        elif kind in {"BODY", "CLOSE_WORK_NO_SAVE"}:
            if block not in stack:
                raise ValueError(f"Control event {kind} is outside block {block}")
        else:
            raise ValueError(f"Unknown control event: {kind}")
    if stack:
        raise ValueError(f"Unclosed control blocks: {stack}")
    failure_lines = [
        source_line(event["source"], event["line"])
        for event in CONTROL_EVENTS
        if event["event"] == "CLOSE_WORK_NO_SAVE"
    ]
    if len(failure_lines) != 2 or any("Excel.CloseExcel.Close Instance: Work" not in line for line in failure_lines):
        raise ValueError("Both failure branches must close Work")
    failure_span = "\n".join(source_line("r2r3_normal_recopy", line) for line in range(190, 198))
    if "SaveAs" in failure_span:
        raise ValueError("Failure branch unexpectedly contains SaveAs")
    return {
        "balanced": True,
        "closed_in_order": closed,
        "outer_guard_closed_by": "C12 line 198",
        "normal_closed_by": "C12 line 193",
        "exact_success_closed_by": "C12 line 197",
        "failure_close_count": 2,
        "failure_save_as_count": 0,
    }


def validate_preserved_from_base() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relative_path in PRESERVE_FROM_BASE:
        path = ROOT / relative_path
        if not path.is_file():
            raise ValueError(f"Preserved A2 file missing: {relative_path}")
        base_bytes = subprocess.check_output(
            ["git", "show", f"{BASE_COMMIT}:{relative_path}"],
            cwd=ROOT,
        )
        current = path.read_bytes()
        if current != base_bytes:
            raise ValueError(f"A2/base evidence changed: {relative_path}")
        records.append(
            {
                "path": relative_path,
                "sha256": sha256_bytes(current),
                "bytes": len(current),
                "matches_base_commit": True,
            }
        )
    return records


def render_instruction() -> tuple[str, dict[str, Any]]:
    before = SOURCES["a2_instruction"].read_text(encoding="utf-8")
    if before.count(a2.ROUTE_INSTRUCTIONS) != 1:
        raise ValueError("A2 route instruction block changed")
    bundle_name_count = before.count(A2_BUNDLE_NAME)
    if bundle_name_count < 2:
        raise ValueError("A2 bundle-name references changed")
    after_route = before.replace(a2.ROUTE_INSTRUCTIONS, ROUTE_INSTRUCTIONS)
    remaining_bundle_name_count = after_route.count(A2_BUNDLE_NAME)
    after = after_route.replace(A2_BUNDLE_NAME, A3_BUNDLE_NAME)
    if (
        a2.ROUTE_INSTRUCTIONS in after
        or A2_BUNDLE_NAME in after
        or a2.CANDIDATE_ID in after
    ):
        raise ValueError("A2 route-specific instruction text remained in A3")
    if utf16_units(after) > 8000:
        raise ValueError(f"A3 instruction exceeds 8000 UTF-16 units: {utf16_units(after)}")
    delta = {
        "schema_version": 1,
        "base_candidate": a2.CANDIDATE_ID,
        "base_instruction_path": relative(SOURCES["a2_instruction"]),
        "base_instruction_sha256": sha256(SOURCES["a2_instruction"]),
        "candidate_id": CANDIDATE_ID,
        "base_bundle_filename_occurrences": bundle_name_count,
        "transforms": [
            {
                "kind": "ROUTE_BLOCK_REPLACEMENT",
                "occurrences": 1,
                "before": a2.ROUTE_INSTRUCTIONS,
                "after": ROUTE_INSTRUCTIONS,
            },
            {
                "kind": "BUNDLE_FILENAME_REPLACEMENT",
                "occurrences": remaining_bundle_name_count,
                "before": A2_BUNDLE_NAME,
                "after": A3_BUNDLE_NAME,
            },
        ],
        "other_transformations": 0,
        "reconstructs_candidate_exactly": True,
    }
    return after, delta


def component_marker(component_id: str, edge: str) -> bytes:
    return f"RAW_COMPONENT {component_id} {edge}\n".encode("utf-8")


def extract_component(bundle: bytes, component_id: str) -> bytes:
    begin = component_marker(component_id, "BEGIN")
    end = component_marker(component_id, "END")
    if bundle.count(begin) != 1 or bundle.count(end) != 1:
        raise ValueError(f"Component marker count changed: {component_id}")
    start = bundle.index(begin) + len(begin)
    finish = bundle.index(end, start)
    return bundle[start:finish]


def render_bundle(
    actual_source_sha: dict[str, str],
    example_records: list[dict[str, Any]],
) -> tuple[bytes, list[dict[str, Any]]]:
    component_records: list[dict[str, Any]] = []
    for component in COMPONENTS:
        excerpt = a2.component_excerpt(component)
        component_records.append(
            {
                **component,
                "source_path": relative(SOURCES[component["source"]]),
                "source_sha256": actual_source_sha[component["source"]],
                "excerpt_sha256": sha256_bytes(excerpt),
                "excerpt_bytes": len(excerpt),
            }
        )

    lines = [
        "PAD Robin fixed-helper A3 self-contained assembly-rule bundle",
        f"candidate_id: {CANDIDATE_ID}",
        f"route_id: {ROUTE_ID}",
        f"bundle_filename: {A3_BUNDLE_NAME}",
        "status: LOCAL_PREPARED_LIMITED_NON_LIVE_NOT_RUN",
        "",
        "BOUNDARY",
        "- A2 and the A2-G1 refusal remain unchanged; this successor adds assembly rules only.",
        "- RAW_COMPONENT blocks are exact byte slices of existing PAD captures/re-copies.",
        "- Verbatim preservation applies to the complete fixed C06 launcher block and each rule's immutable portions.",
        "- Listed mutable substitutions, explicit command-line copies, connections, and required indentation changes are allowed.",
        "- No new PAD LOOP command is introduced. Unknown actions, arguments, enum values, and block shapes remain forbidden.",
        "- The derived small example is NOT_CAPTURED_NOT_COMPLETE_NOT_RUN and is not a fixed-EX03 answer.",
        "- A complete fixed-EX03 Robin, grading values, and fixed-EX03 full wiring are intentionally absent.",
        "- A captured or executed complete flow is not a prerequisite for generation from the listed rules.",
        "",
        "VERIFIER-MANAGED FIXED IDENTITIES (NOT MUTABLE)",
        f"- helper: {relative(SOURCES['helper'])} / SHA-256 {actual_source_sha['helper']}",
        f"- invocation: {relative(SOURCES['invocation'])} / SHA-256 {actual_source_sha['invocation']}",
        f"- launcher: {relative(SOURCES['launcher'])} / SHA-256 {actual_source_sha['launcher']}",
        f"- exact success: {EXPECTED_SUCCESS}",
        "- helper and invocation are preplaced by the verifier and must not be emitted or modified.",
        "",
        "IN-BUNDLE INDEX",
    ]
    for record in component_records:
        dependencies = ",".join(record["dependencies"]) if record["dependencies"] else "none"
        mutable = "; ".join(record["mutable_parameters"]) if record["mutable_parameters"] else "none"
        immutable = "; ".join(record["immutable_syntax"])
        lines.extend(
            [
                f"[{record['id']}] {record['title']}",
                f"  source: {record['source_path']} lines {record['start_line']}-{record['end_line']}",
                f"  source_sha256: {record['source_sha256']}",
                f"  excerpt_sha256: {record['excerpt_sha256']}",
                f"  dependencies: {dependencies}",
                f"  mutable_parameters: {mutable}",
                f"  immutable_syntax: {immutable}",
                f"  prior_execution_scope: {record['execution_scope']}",
            ]
        )

    lines.extend(["", "SOURCE-LINE ASSEMBLY RULES"])
    for rule in ASSEMBLY_RULES:
        lines.extend(
            [
                f"[{rule['id']}] component={rule['component']}",
                f"  purpose: {rule['purpose']}",
            ]
        )
        for binding in rule["line_bindings"]:
            lines.append(
                f"  source_lines: {relative(SOURCES[binding['source']])}:{binding['lines'][0]}-{binding['lines'][1]} => {binding['role']}"
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
    for event in CONTROL_EVENTS:
        lines.append(
            f"- {event['sequence']:02d} {event['event']} {event['block']} => "
            f"{event['component']} / {relative(SOURCES[event['source']])}:{event['line']}"
        )
    lines.extend(
        [
            "- C12 line 193 closes NORMAL_MODE.",
            "- C12 line 197 closes EXACT_SUCCESS.",
            "- C12 line 198 closes OUTPUT_GUARD.",
            "- C12 lines 191 and 195 close Work without SaveAs in the two failure branches.",
            "",
            "DERIVED SMALL ASSEMBLY EXAMPLE — NOT RAW CAPTURE / NOT COMPLETE ROBIN / NOT RUN",
            "- Different condition: one four-cell DemoData row, two demo target sheets, two numeric writes, two one-row readback rectangles, four JSON comparisons.",
            "- This fragment omits C01/C02/C05/C06/C07/C12 commands and is not connected to the fixed invocation.",
            "- E numbers and source annotations are teaching metadata and must never be copied into generated Robin.",
        ]
    )
    for index, record in enumerate(example_records, start=1):
        lines.append(
            f"E{index:03d} [{record['rule_id']}] from {record['source_path']}:{record['source_line']} | {record['text']}"
        )
    lines.extend(["", "RAW COMPONENTS"])

    parts: list[bytes] = [("\n".join(lines) + "\n").encode("utf-8")]
    for record in component_records:
        parts.append((f"\nRAW COMPONENT METADATA {record['id']}\n").encode("utf-8"))
        parts.append(component_marker(record["id"], "BEGIN"))
        parts.append(a2.component_excerpt(record))
        parts.append(component_marker(record["id"], "END"))
    parts.append(
        (
            "\nEND OF SELF-CONTAINED A3 BUNDLE\n"
            "The raw blocks are captured source. The assembly rules and E-lines are derived teaching material, not a complete fixed-EX03 answer and not an executed A3 flow.\n"
        ).encode("utf-8")
    )
    bundle = b"".join(parts)
    for record in component_records:
        if extract_component(bundle, record["id"]) != a2.component_excerpt(record):
            raise ValueError(f"Raw component changed while rendering: {record['id']}")
    return bundle, component_records


def artifact_record(path: Path, destination: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(destination).as_posix(),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def source_record(name: str, path: Path) -> dict[str, Any]:
    return {
        "path": relative(path),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "role": SOURCE_ROLES[name],
        "copilot_attachment": False,
    }


def payload_sha256(destination: Path, paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.relative_to(destination).as_posix()):
        digest.update(path.relative_to(destination).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def render_coverage() -> str:
    return f"""# {CANDIDATE_ID} limited non-live coverage

This record is limited to the four checks authorized for A3. It does not claim
Copilot generation, PAD save/re-copy, PAD/Excel execution, or acceptance.

| Authorized check | Result basis |
| --- | --- |
| cited component source identity | 12 RAW_COMPONENT blocks equal their SHA-pinned source line slices |
| derived example variable references and block pairing | no forward/undefined reference; CONTROL BLOCK MAP closes NORMAL, exact-success, then outer guard |
| fixed launcher unchanged | C06 decodes to launcher SHA {a2.EXPECTED_SOURCE_SHA256['launcher']} after restoring only terminal LF |
| teaching/test independence | no complete fixed-EX03 Robin, grader values, or fixed full wiring; example is NOT_CAPTURED_NOT_COMPLETE_NOT_RUN |

No new PAD LOOP command was added. C04, C09, C10, and C11 use explicit copies
of captured command lines. A3 instruction, prepared submitted body, and bundle
name the same candidate, route, assembly-rule IDs, and scope.
"""


def render_placement(actual_source_sha: dict[str, str]) -> str:
    return f"""# {CANDIDATE_ID} placement and boundary

Route: {BT}{ROUTE_ID}{BT}. This is assembly-rule teaching preparation only.
A2 and A2-G1 remain unchanged.

## Prepared future Copilot input

If separately authorized later, use {BT}submitted-body.txt{BT} without edits and attach
exactly {BT}knowledge/{A3_BUNDLE_NAME}{BT}. This turn did not send either file.

## Fixed verifier-managed identities

| Role | Existing path | Required SHA-256 |
| --- | --- | --- |
| helper | {BT}{SOURCES['helper'].resolve()}{BT} | {BT}{actual_source_sha['helper']}{BT} |
| invocation | {BT}{SOURCES['invocation'].resolve()}{BT} | {BT}{actual_source_sha['invocation']}{BT} |
| launcher | {BT}{SOURCES['launcher'].resolve()}{BT} | {BT}{actual_source_sha['launcher']}{BT} |

C06 remains byte-exact. Only rule-listed mutable tokens and explicit copies may
change. The small example is a different-condition, incomplete, unexecuted
derivation and is not the fixed-EX03 answer.

## Current scope

Only source identity, derived variable/block consistency, fixed launcher
identity, and teaching/test independence were checked. Copilot send, PAD/Excel,
new capture, full regression, acceptance, and GitHub write were not run.
"""


def build(destination: Path = DESTINATION) -> dict[str, Any]:
    destination = Path(destination)
    if destination.exists() and any(path.is_file() for path in destination.rglob("*")):
        raise ValueError(f"Candidate already exists: {destination}")

    preserved_a2 = validate_preserved_from_base()
    actual_source_sha = {name: sha256(path) for name, path in SOURCES.items()}
    if actual_source_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"Protected source SHA mismatch: {actual_source_sha}")

    formal = json.loads(SOURCES["formal_r12_status"].read_text(encoding="utf-8"))
    t2_result = json.loads(SOURCES["t2_result"].read_text(encoding="utf-8"))
    a2_assessment = json.loads(SOURCES["a2_assessment"].read_text(encoding="utf-8"))
    if formal["accepted"] or not formal["status"].startswith("FAIL_"):
        raise ValueError("Formal r12 failure boundary changed")
    if t2_result["decision"] != "PASS_FIXED_HELPER_AUXILIARY_NORMAL_RUN1":
        raise ValueError("T2 auxiliary boundary changed")
    if a2_assessment["final_status"] != "STOPPED_FAIL_REFUSAL":
        raise ValueError("A2 refusal boundary changed")

    instruction, instruction_delta = render_instruction()
    request = SOURCES["fixed_request"].read_text(encoding="utf-8").rstrip("\r\n")
    send_conditions = SEND_CONDITIONS.rstrip("\r\n") + "\n"
    submitted_body = (
        request
        + "\n\n"
        + send_conditions.rstrip("\r\n")
        + "\n\n"
        + instruction.rstrip("\r\n")
        + "\n"
    )
    example_records = build_derived_example()
    example_validation = validate_example_variables(example_records)
    control_validation = validate_control_events()
    bundle, component_records = render_bundle(actual_source_sha, example_records)

    c06 = extract_component(bundle, "C06_FIXED_LAUNCHER_RUNSCRIPT")
    c06_text = c06.decode("utf-8").replace("\r\n", "\n")
    decoded_launcher = a2.embedded_script(c06_text)
    launcher_bytes = SOURCES["launcher"].read_bytes()
    if decoded_launcher.encode("utf-8") + b"\n" != launcher_bytes:
        raise ValueError("A3 C06 no longer decodes to fixed launcher plus terminal LF")
    launcher_restored_sha = sha256_bytes(decoded_launcher.encode("utf-8") + b"\n")
    if launcher_restored_sha != actual_source_sha["launcher"]:
        raise ValueError("A3 fixed launcher SHA mismatch")

    c06_removed = bundle.replace(
        c06,
        b"[C06_FIXED_LAUNCHER_RUNSCRIPT_FIXED_CONTENT_REMOVED_FOR_INDEPENDENCE_CHECK]\n",
    ).decode("utf-8")
    forbidden_fixed_terms = (
        "入力い.xlsx",
        "入力ろ.xlsx",
        "受取明細",
        "追加項目",
        "集計先",
        "追記先",
        "EX03-attempt1",
        "項目甲",
        "項目乙",
        "日本語",
    )
    leaked = [term for term in forbidden_fixed_terms if term in c06_removed]
    if leaked:
        raise ValueError(f"Fixed EX03 terms leaked outside immutable C06: {leaked}")
    for source_name, label in (
        ("helper", "helper body"),
        ("invocation", "invocation JSON"),
        ("t2_pad_recopy", "complete T2 Robin"),
        ("r2r3_normal_recopy", "complete R2/R3 Robin"),
        ("fixed_expected", "fixed expected data"),
    ):
        if SOURCES[source_name].read_bytes() in bundle:
            raise ValueError(f"{label} leaked into A3 bundle")

    instruction_path = destination / "agent-instructions.txt"
    conditions_path = destination / "send-conditions.txt"
    body_path = destination / "submitted-body.txt"
    bundle_path = destination / "knowledge" / A3_BUNDLE_NAME
    rules_path = destination / "assembly-rules.json"
    delta_path = destination / "instruction-delta.json"
    coverage_path = destination / "COVERAGE.md"
    placement_path = destination / "PLACEMENT.md"
    verification_path = destination / "non-live-verification.json"

    write_text(instruction_path, instruction)
    write_text(conditions_path, send_conditions)
    write_text(body_path, submitted_body)
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.write_bytes(bundle)
    write_json(
        rules_path,
        {
            "schema_version": 1,
            "candidate_id": CANDIDATE_ID,
            "status": "DERIVED_RULES_AND_SMALL_EXAMPLE_NOT_CAPTURED_NOT_COMPLETE_NOT_RUN",
            "rules": ASSEMBLY_RULES,
            "control_events": CONTROL_EVENTS,
            "control_validation": control_validation,
            "derived_example": {
                "condition": "four-cell DemoData row, two targets, two numeric writes, two readback rectangles, four comparisons",
                "predefined_variables": ["DemoData", "Work"],
                "records": example_records,
                "validation": example_validation,
            },
        },
    )
    instruction_delta["candidate_instruction_sha256"] = sha256(instruction_path)
    instruction_delta["candidate_instruction_utf16_units"] = utf16_units(instruction)
    write_json(delta_path, instruction_delta)
    write_text(coverage_path, render_coverage())
    write_text(placement_path, render_placement(actual_source_sha))

    verification = {
        "schema_version": 1,
        "candidate_id": CANDIDATE_ID,
        "route_id": ROUTE_ID,
        "decision": "PASS_LIMITED_NON_LIVE_ASSEMBLY_RULES_ONLY",
        "authorized_checks": {
            "cited_component_source_identity": {
                "status": "PASS",
                "component_count": len(component_records),
                "all_exact": True,
            },
            "derived_example_variables_and_block_pairing": {
                "status": "PASS",
                "example_line_count": len(example_records),
                "unresolved_references": [],
                "new_pad_loop_commands": 0,
                "control": control_validation,
            },
            "fixed_launcher_unchanged": {
                "status": "PASS",
                "sha256": launcher_restored_sha,
            },
            "teaching_test_independence": {
                "status": "PASS",
                "complete_fixed_ex03_robin_absent": True,
                "fixed_grader_values_absent": True,
                "fixed_ex03_full_wiring_absent": True,
                "derived_example_marked_not_captured_not_complete_not_run": True,
            },
        },
        "instruction_body_bundle_consistency": {
            "candidate_id": CANDIDATE_ID,
            "route_id": ROUTE_ID,
            "bundle_filename": A3_BUNDLE_NAME,
            "assembly_rule_ids": [rule["id"] for rule in ASSEMBLY_RULES],
            "submitted_body_begins_with_fixed_request": submitted_body.startswith(request + "\n\n"),
            "copilot_send_count": 0,
        },
        "preserved_a2_files": preserved_a2,
        "preserved_boundaries": {
            "formal_r12_status": formal["status"],
            "formal_r12_accepted": formal["accepted"],
            "t2_decision": t2_result["decision"],
            "a2_result": a2_assessment["final_status"],
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

    artifacts = {
        "instruction": artifact_record(instruction_path, destination),
        "send_conditions": artifact_record(conditions_path, destination),
        "submitted_body": artifact_record(body_path, destination),
        "bundle": artifact_record(bundle_path, destination),
        "assembly_rules": artifact_record(rules_path, destination),
        "instruction_delta": artifact_record(delta_path, destination),
        "coverage": artifact_record(coverage_path, destination),
        "placement": artifact_record(placement_path, destination),
        "non_live_verification": artifact_record(verification_path, destination),
    }
    payload_paths = [
        instruction_path,
        conditions_path,
        body_path,
        bundle_path,
        rules_path,
        delta_path,
        coverage_path,
        placement_path,
        verification_path,
    ]
    manifest = {
        "schema_version": 1,
        "candidate_id": CANDIDATE_ID,
        "route_id": ROUTE_ID,
        "status": "LOCAL_PREPARED_LIMITED_NON_LIVE_NOT_COPILOT_OR_PAD_ACCEPTED",
        "base_commit": BASE_COMMIT,
        "successor_to": a2.CANDIDATE_ID,
        "a2_files_modified": False,
        "replaces_formal_r12": False,
        "inherits_t2_auxiliary_pass": False,
        "artifacts": artifacts,
        "candidate_payload_sha256": payload_sha256(destination, payload_paths),
        "candidate_payload_sha256_algorithm": "SHA256(sorted relative UTF-8 path + NUL + bytes + NUL)",
        "source_evidence": {name: source_record(name, path) for name, path in SOURCES.items()},
        "preserved_a2_files": preserved_a2,
        "instruction_contract": {
            "utf16_code_units": utf16_units(instruction),
            "max_utf16_code_units": 8000,
            "bundle_filename": A3_BUNDLE_NAME,
            "verbatim_scope": "ENTIRE_C06_AND_RULE_LISTED_IMMUTABLE_PORTIONS_ONLY",
            "listed_replacement_duplication_connection_and_indentation_changes_allowed": True,
            "complete_flow_capture_or_execution_required_before_generation": False,
            "fabrication_of_unknown_action_argument_enum_or_control_allowed": False,
        },
        "assembly_contract": {
            "rule_ids": [rule["id"] for rule in ASSEMBLY_RULES],
            "explicit_command_copy_only": True,
            "new_pad_loop_commands": 0,
            "control_block_map_balanced": True,
            "derived_example_status": "NOT_CAPTURED_NOT_COMPLETE_NOT_RUN",
        },
        "fixed_contract": {
            "helper_sha256": actual_source_sha["helper"],
            "invocation_sha256": actual_source_sha["invocation"],
            "launcher_sha256": actual_source_sha["launcher"],
            "decoded_launcher_terminal_lf_restored_sha256": launcher_restored_sha,
            "success_output": EXPECTED_SUCCESS,
            "helper_invocation_runtime_fixed_request_expected_output_format_changed": False,
        },
        "component_records": component_records,
        "teaching_independence": {
            "complete_fixed_ex03_robin_in_bundle": False,
            "fixed_expected_or_grader_values_in_bundle": False,
            "fixed_ex03_full_wiring_in_bundle": False,
            "helper_body_in_bundle": False,
            "invocation_json_in_bundle": False,
            "fixed_launcher_runscript_in_bundle": True,
            "derived_example_is_different_condition": True,
            "derived_example_marked_not_run": True,
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
