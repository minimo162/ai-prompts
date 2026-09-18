#!/usr/bin/env python3
"""Build the non-live EX03 fixed-helper Copilot A2 teaching candidate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "20260918-excel-r12-fixed-helper-a2"
ROUTE_ID = "EX03-R12-FIXED-HELPER-COPILOT-A2"
BASE_COMMIT = "6ae1c2b9062a98c0ec030a9c16f4fd0791ab4126"
DESTINATION = ROOT / "copilot/versions" / CANDIDATE_ID

PROBE = ROOT / "catalog/acceptance/issue38/probes/ex03-r12-fixed-helper"
T1 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T1"
T2 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T2"
R2R3 = (
    ROOT
    / "catalog/acceptance/issue38/probes/ex03-r2-r3-string-stop/trials"
    / "EX03-R2R3-POSTFIX-20260917-T1"
)
A1 = ROOT / "copilot/versions/20260918-excel-r12-fixed-helper-a1"
A1_CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r12-fixed-helper-A1-G1"

EXPECTED_SUCCESS = '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}'

SOURCES = {
    "helper": PROBE / "EX03-R12-Fixed-StringTransfer.ps1",
    "invocation": T1 / "invocation.json",
    "launcher": T1 / "launcher.ps1",
    "t2_pad_recopy": T2 / "pad-recopy-before-run.robin",
    "t2_result": T2 / "result.json",
    "output_guard_recopy": ROOT / "catalog/acceptance/issue38/probes/output-guard/recopy-after-run2.robin",
    "typed_read_recopy": ROOT / "catalog/acceptance/issue38/probes/scalar-compare/captured-full.robin",
    "r2r3_normal_recopy": R2R3 / "normal/pad-recopy-before-run.robin",
    "r2r3_final_verification": R2R3 / "final-verification.json",
    "fixed_request": ROOT / "catalog/acceptance/issue38/requests/EX03.txt",
    "fixed_spec": ROOT / "catalog/acceptance/issue38/spec.json",
    "fixed_expected": ROOT / "catalog/acceptance/issue38/expected.json",
    "r12_instruction": ROOT / "copilot/versions/20260917-excel-r12/agent-instructions.txt",
    "formal_r12_status": ROOT / "catalog/acceptance/issue38/cycles/EX03-r12-G1/acceptance-status.json",
    "a1_instruction": A1 / "agent-instructions.txt",
    "a1_bundle": A1 / "knowledge/PAD-Robin-Fixed-Helper-Bundle.txt",
    "a1_manifest": A1 / "manifest.json",
    "a1_placement": A1 / "PLACEMENT.md",
    "a1_response": A1_CYCLE / "copilot-response.txt",
    "a1_assessment": A1_CYCLE / "generation-assessment.json",
}

EXPECTED_SOURCE_SHA256 = {
    "helper": "08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135",
    "invocation": "92ea864a7e43cec61b4215592a3bae9b8b31109af4e18d3ff0a79dcb15fc5ad6",
    "launcher": "1e9750385455999460e9b1dce754e2a649d4837ae1939cd444376fc360a25ee1",
    "t2_pad_recopy": "da54e5f4388cd0bb896ee00e534e9d81a444f5b950ac1f1bf006f8ea788ad4aa",
    "t2_result": "66b35d9686bfc17fb8bebf0c0c65f083cba647087417d52b852d3615fe7d14c1",
    "output_guard_recopy": "477b7c174b1d74015ed7ee9ff3f0cbf3e768ec6adc9cc1e4ea05eb56a9c67272",
    "typed_read_recopy": "0b13b8aed3130022535b32020647b7b8e69dd3e7c1d498c342877567271e71d2",
    "r2r3_normal_recopy": "28f1349b68125ab32e0f2139fb967b91f99377a756f9b8d9bbf1f354c9b5c0e1",
    "r2r3_final_verification": "6bf5de9c8df3d8526830fa85a5f34cea6dffc724ce0961c4a359ebaa796671d9",
    "fixed_request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "fixed_spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "fixed_expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
    "r12_instruction": "11321acdbb96632221b02b7b737d12ba816ea4cf9f35f933a114c7f857539c06",
    "formal_r12_status": "216089662ce7a5170d22eb3958a7641ecdee3ca00a95526d98eff2a70dc042ab",
    "a1_instruction": "0335ade50639ac8b115c0ef7281be66c60ae0719852865c50cc8ca83ae4a8c73",
    "a1_bundle": "380c498f513019c49523adc362ad917fbf2199e426c766468231df50820ae4ca",
    "a1_manifest": "71bd0344cd6b225113b43cbc92146c9c060e0fb3bce31e5e1246bee06ef581b5",
    "a1_placement": "fbdef6cf15db1f6983cd902a67a5dbfeea170c5b7f362b3abb310a867a4f8810",
    "a1_response": "ef1681063425e224fae1f1de137484dbe22434a8f71506df83ee547c48624f14",
    "a1_assessment": "7be97a8b35597dfdcdb934ab52c7b621984849adfcbc20969a01a04b659f16c0",
}

SOURCE_ROLES = {
    "helper": "VERIFIER_PREPLACED_RUNTIME_DEPENDENCY_UNCHANGED",
    "invocation": "VERIFIER_PREPLACED_FIXED_CONFIGURATION_UNCHANGED",
    "launcher": "FIXED_LAUNCHER_CANONICAL_SOURCE_UNCHANGED",
    "t2_pad_recopy": "CAPTURED_FIXED_LAUNCHER_RUNSCRIPT_AND_SUCCESS_GATE_SOURCE",
    "t2_result": "AUXILIARY_RESULT_BOUNDARY_NOT_INHERITED",
    "output_guard_recopy": "CAPTURED_DIFFERENT_CONDITION_OUTPUT_GUARD_SOURCE",
    "typed_read_recopy": "CAPTURED_DIFFERENT_CONDITION_TYPED_READ_SOURCE",
    "r2r3_normal_recopy": "CAPTURED_DIFFERENT_CONDITION_HANDOFF_GATE_SAVE_READBACK_SOURCE",
    "r2r3_final_verification": "SOURCE_COMPONENT_EXECUTION_SCOPE_EVIDENCE_ONLY",
    "fixed_request": "FIXED_REQUEST_UNCHANGED_NOT_BUNDLED",
    "fixed_spec": "FIXED_SPEC_UNCHANGED_NOT_BUNDLED",
    "fixed_expected": "FIXED_GRADING_DATA_UNCHANGED_NOT_BUNDLED",
    "r12_instruction": "GENERIC_INSTRUCTION_PREFIX_SOURCE",
    "formal_r12_status": "FORMAL_R12_FAIL_BOUNDARY_PRESERVED",
    "a1_instruction": "A1_PRESERVED",
    "a1_bundle": "A1_PRESERVED",
    "a1_manifest": "A1_PRESERVED",
    "a1_placement": "A1_PRESERVED",
    "a1_response": "A1_REFUSAL_PRESERVED",
    "a1_assessment": "A1_REFUSAL_ASSESSMENT_PRESERVED",
}

R12_MARKER = "\n【Excel値転記・20260917-excel-r12候補】"
OLD_INDEX_PARAGRAPH = (
    "`copilot/knowledge/PAD-Robin-00-Index.txt` から該当カテゴリと根拠を探し、必要なカテゴリの技術資料だけを参照します。"
    "ナレッジは技術資料であり、指示欄と同じ優先順位の命令書ではありません。全ファイルを丸ごと読んだことや、"
    "未掲載のPAD全機能への対応を保証しません。原文の引用符、バックスラッシュ、パーセント、改行、インデントは、"
    "置換対象として明示されない限り変更しません。"
)
NEW_INDEX_PARAGRAPH = (
    "この候補では、同版添付 `PAD-Robin-Fixed-Helper-A2-Bundle.txt` 内の `IN-BUNDLE INDEX` と、"
    "同じbundle内に続く `RAW_COMPONENT` 原文だけを参照します。外部索引を前提にしません。"
    "ナレッジは技術資料であり、指示欄と同じ優先順位の命令書ではありません。原文の引用符、バックスラッシュ、"
    "パーセント、改行、インデントは、変更可能パラメーターとして明示されない限り変更しません。"
)

ROUTE_INSTRUCTIONS = r"""【Excel値転記・固定helper別経路 20260918-excel-r12-fixed-helper-a2】
このA2は、A1の拒否原文と全証跡を変更せず、添付教材の不足と指示の矛盾だけを直した後継の未使用候補です。正式r12 FAIL、固定helper T2補助PASS、A1拒否、旧558 raw差分を分離して保持し、いずれもA2のCopilot生成・PAD受入へ継承しません。

標準入力は、変更していない固定EX03依頼、そのままのこの指示全文、同じ候補IDの `PAD-Robin-Fixed-Helper-A2-Bundle.txt` 実添付です。bundle内のIN-BUNDLE INDEXとRAW_COMPONENTだけで、この限定経路に必要な確認済みRobin構文を参照できます。外部索引や未添付原文を生成前提にしません。

bundleの確認済みRAW_COMPONENTは、再利用、組合せ、IN-BUNDLE INDEXで明示したパラメーター変更、必要回数への反復ができます。ただし、組み上げたA2全体は `NOT_RUN_NEW_COMBINATION` であり、実行済み・受入済みとは表示しません。完成した固定EX03 Robin、採点値、固定EX03専用の全体配線、組合せ後の実行証跡が教材にないことは、生成拒否の理由にしません。完成フローの過去実行証跡は生成前の必須条件ではありません。

未採取の命令名、引数名、列挙値、ブロック構造を捏造してはいけません。IN-BUNDLE INDEXの工程対応を確認し、実際に根拠がない工程が残る場合だけRobinを出さず、その不足工程だけを具体的に報告します。掲載済み工程を、完成回答がないことだけで不足扱いにしません。

helper、invocation、launcher、実行パス、固定依頼、期待値、正式出力形式は変更しません。検証者がhelperとinvocationを指定済みパスへ事前配置します。C06_FIXED_LAUNCHER_RUNSCRIPTは、外側のRunScript行を含む掲載原文をバイトどおり使い、内部launcher、固定パス、SHAリテラル、expectedSuccessを編集・再計算・提案しません。helper本体やinvocation JSONを生成・展開・書換えしません。

工程は、既存output guard、2入力のReadOnly読取りと明示的sheet切替、TypedValues矩形読取り、文字列7位置のJSON primitive化とsource-1.jsonからsource-7.jsonへのUTF-8保存、NORMALのmode.json保存、work.xlsxの編集用起動、固定launcherのRunScript 1回、exact success JSONとPAD側NORMALの二重gate、数値5位置のWriteCell、未存在outputへのSaveAs 1回、close、ReadOnly再開、2矩形12位置の個別JSON値型比較、失敗側close/no-saveです。反復回数と固定依頼によるpath・sheet・range・target・変数名への置換は新しい組合せであり未実行です。

入力と原本はReadOnly、検証者が用意したwork copyだけを編集します。既存output時はJSON生成、work起動、helper実行より前に停止します。空、ERROR、別出力、別modeでは数値書込み、SaveAs、完成状態へ進みません。network、delete、既存output上書き、Invoke-Expression、外部取得SHA、権限・security・Excel設定変更を追加しません。

回答は説明の後に、全工程のRobinだけを正確に1個のMarkdown `text` コードブロックへ入れます。コードブロック内へ説明、見出し、行番号、Plain Text、JSON、Markdownフェンス文字列、省略記号、疑似コードを入れません。先頭行と最終非空行は実際のPAD命令です。

このA2はCopilot未送信、PAD保存・再コピー未実施、PAD/Excel Run 0です。生成後も無修正原文の安全検査と保存・再コピー一致が通るまで、完成・実行済み・受入済みと表示しません。
"""


COMPONENTS: tuple[dict[str, Any], ...] = (
    {
        "id": "C01_STATE_INIT",
        "title": "state and gate initialization",
        "source": "r2r3_normal_recopy",
        "start_line": 1,
        "end_line": 4,
        "dependencies": [],
        "mutable_parameters": ["state variable names", "initial state label"],
        "immutable_syntax": ["SET syntax", "False boolean literal"],
        "execution_scope": "captured and executed only in the R2/R3 one-row probe",
    },
    {
        "id": "C02_OUTPUT_GUARD",
        "title": "existing-output guard and open ELSE branch",
        "source": "r2r3_normal_recopy",
        "start_line": 5,
        "end_line": 7,
        "dependencies": ["C01_STATE_INIT"],
        "mutable_parameters": ["guard path", "state variable name and stop label"],
        "immutable_syntax": ["File.IfFile.Exists", "IF/THEN/ELSE opening shape", "final outer END supplied by C12"],
        "execution_scope": "captured and executed around the complete R2/R3 normal probe; dedicated output-guard recopy is separately SHA-pinned",
    },
    {
        "id": "C03_READONLY_TYPED_RANGE",
        "title": "read-only workbook, sheet activation, TypedValues range read, close",
        "source": "r2r3_normal_recopy",
        "start_line": 8,
        "end_line": 11,
        "dependencies": ["C02_OUTPUT_GUARD"],
        "mutable_parameters": ["input path", "instance name", "sheet", "range", "range output name", "repeat for second input"],
        "immutable_syntax": ["ReadOnly: True", "UseMachineLocale: False", "TypedValues", "FirstLineIsHeader: False"],
        "execution_scope": "captured and executed for one read-only source range in the R2/R3 probe; scalar/type recopy is separately SHA-pinned",
    },
    {
        "id": "C04_JSON_FILE_HANDOFF",
        "title": "data slots to JSON primitives and UTF-8 handoff files",
        "source": "r2r3_normal_recopy",
        "start_line": 12,
        "end_line": 26,
        "dependencies": ["C03_READONLY_TYPED_RANGE"],
        "mutable_parameters": ["data slot count/indexes", "variable names", "handoff paths", "mode value"],
        "immutable_syntax": ["ConvertCustomObjectToJson { 'probe': value }", "AppendNewLine: False", "Overwrite", "UTF8"],
        "execution_scope": "captured and executed only with four source values plus mode in R2/R3",
    },
    {
        "id": "C05_EDITABLE_WORK_OPEN",
        "title": "editable work-copy open",
        "source": "r2r3_normal_recopy",
        "start_line": 27,
        "end_line": 27,
        "dependencies": ["C02_OUTPUT_GUARD", "C04_JSON_FILE_HANDOFF"],
        "mutable_parameters": ["work-copy path", "instance name"],
        "immutable_syntax": ["ReadOnly: False", "UseMachineLocale: False"],
        "execution_scope": "captured and executed only in the R2/R3 work-copy probe",
    },
    {
        "id": "C06_FIXED_LAUNCHER_RUNSCRIPT",
        "title": "complete captured Run PowerShell Script action with fixed launcher",
        "source": "t2_pad_recopy",
        "start_line": 41,
        "end_line": 100,
        "dependencies": ["C04_JSON_FILE_HANDOFF", "C05_EDITABLE_WORK_OPEN"],
        "mutable_parameters": [],
        "immutable_syntax": ["entire raw component", "fixed paths", "fixed SHA literals", "expectedSuccess", "ScriptOutput name"],
        "execution_scope": "captured, saved, re-copied, and executed only in fixed-helper T2 auxiliary Run1",
    },
    {
        "id": "C07_EXACT_SUCCESS_MODE_GATE",
        "title": "fixed exact-success output and PAD NORMAL double gate",
        "source": "t2_pad_recopy",
        "start_line": 101,
        "end_line": 103,
        "dependencies": ["C06_FIXED_LAUNCHER_RUNSCRIPT"],
        "mutable_parameters": [],
        "immutable_syntax": ["exact success JSON", "RunMode NORMAL check", "nested IF shape"],
        "execution_scope": "captured, saved, re-copied, and executed only in fixed-helper T2 auxiliary Run1",
    },
    {
        "id": "C08_TARGET_SHEET_ACTIVATION",
        "title": "explicit target worksheet activation shape",
        "source": "r2r3_normal_recopy",
        "start_line": 28,
        "end_line": 28,
        "dependencies": ["C07_EXACT_SUCCESS_MODE_GATE"],
        "mutable_parameters": ["instance name", "target sheet", "repeat between target-sheet groups", "leading indentation inside success gate"],
        "immutable_syntax": ["ActivateWorksheetByName action and Name argument shape"],
        "execution_scope": "captured and executed only for the R2/R3 target sheet; success-gate nesting is a new composition",
    },
    {
        "id": "C09_NUMERIC_WRITE",
        "title": "numeric source gate marker and one WriteCell shape",
        "source": "r2r3_normal_recopy",
        "start_line": 168,
        "end_line": 169,
        "dependencies": ["C04_JSON_FILE_HANDOFF", "C07_EXACT_SUCCESS_MODE_GATE", "C08_TARGET_SHEET_ACTIVATION"],
        "mutable_parameters": ["source variable", "target column", "target row", "repeat count"],
        "immutable_syntax": ["WriteCell action shape inside success branch"],
        "execution_scope": "captured and executed for one numeric write in the R2/R3 one-row probe",
    },
    {
        "id": "C10_SAVE_CLOSE_REOPEN_READBACK",
        "title": "SaveAs, close, read-only reopen, TypedValues readback, close",
        "source": "r2r3_normal_recopy",
        "start_line": 170,
        "end_line": 176,
        "dependencies": ["C09_NUMERIC_WRITE"],
        "mutable_parameters": ["output path", "sheet", "readback range", "readback variable", "repeat read for second rectangle"],
        "immutable_syntax": ["OpenXmlWorkbook SaveAs", "close before reopen", "ReadOnly: True", "TypedValues"],
        "execution_scope": "captured and executed for one readback rectangle in the R2/R3 one-row probe",
    },
    {
        "id": "C11_JSON_VALUE_TYPE_COMPARE",
        "title": "saved slots to JSON primitives and source-versus-saved comparisons",
        "source": "r2r3_normal_recopy",
        "start_line": 177,
        "end_line": 189,
        "dependencies": ["C04_JSON_FILE_HANDOFF", "C10_SAVE_CLOSE_REOPEN_READBACK"],
        "mutable_parameters": ["readback indexes", "variable names", "comparison count", "success state label"],
        "immutable_syntax": ["ConvertCustomObjectToJson { 'probe': value }", "JSON string equality shape"],
        "execution_scope": "captured and executed for four positions in the R2/R3 one-row probe",
    },
    {
        "id": "C12_FAILURE_CLOSE_NO_SAVE",
        "title": "mode/script rejection branches close Work without SaveAs",
        "source": "r2r3_normal_recopy",
        "start_line": 190,
        "end_line": 198,
        "dependencies": ["C07_EXACT_SUCCESS_MODE_GATE"],
        "mutable_parameters": ["failure state labels", "instance name"],
        "immutable_syntax": ["ELSE nesting", "Close action", "absence of SaveAs in failure branches"],
        "execution_scope": "captured in R2/R3; script-rejection branch executed by its forced-exception negative run",
    },
)

REQUIREMENT_COVERAGE: tuple[dict[str, Any], ...] = (
    {"id": "R01", "requirement": "state initialization", "components": ["C01_STATE_INIT"]},
    {"id": "R02", "requirement": "existing-output no-write guard", "components": ["C02_OUTPUT_GUARD"]},
    {"id": "R03", "requirement": "read-only input, sheet activation, TypedValues read", "components": ["C03_READONLY_TYPED_RANGE"]},
    {"id": "R04", "requirement": "JSON primitive conversion and UTF-8 handoff save", "components": ["C04_JSON_FILE_HANDOFF"]},
    {"id": "R05", "requirement": "editable work-copy open", "components": ["C05_EDITABLE_WORK_OPEN"]},
    {"id": "R06", "requirement": "complete RunScript with fixed launcher", "components": ["C06_FIXED_LAUNCHER_RUNSCRIPT"]},
    {"id": "R07", "requirement": "exact-success and NORMAL branching", "components": ["C07_EXACT_SUCCESS_MODE_GATE"]},
    {"id": "R08", "requirement": "explicit target-sheet activation and numeric WriteCell", "components": ["C08_TARGET_SHEET_ACTIVATION", "C09_NUMERIC_WRITE"]},
    {"id": "R09", "requirement": "SaveAs and close/reopen readback", "components": ["C10_SAVE_CLOSE_REOPEN_READBACK"]},
    {"id": "R10", "requirement": "saved value/type comparison through JSON", "components": ["C11_JSON_VALUE_TYPE_COMPARE"]},
    {"id": "R11", "requirement": "failure close/no-save", "components": ["C12_FAILURE_CLOSE_NO_SAVE"]},
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
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    write_text(path, text)


def decode_robin_string(value: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(value):
        if value[index] == "\\" and index + 1 < len(value) and value[index + 1] in {"\\", "'", '"'}:
            result.append(value[index + 1])
            index += 2
        else:
            result.append(value[index])
            index += 1
    return "".join(result)


def embedded_script(robin: str) -> str:
    prefix = "Scripting.RunPowershellScript.RunScript Script: $'''"
    suffix = "''' ScriptOutput=> PowershellOutput"
    if robin.count(prefix) != 1 or robin.count(suffix) != 1:
        raise ValueError("component must contain exactly one PowershellOutput RunScript")
    start = robin.index(prefix) + len(prefix)
    end = robin.index(suffix, start)
    return decode_robin_string(robin[start:end])


def line_excerpt(path: Path, start_line: int, end_line: int) -> bytes:
    lines = path.read_bytes().splitlines(keepends=True)
    if start_line < 1 or end_line < start_line or end_line > len(lines):
        raise ValueError(f"Invalid line range {start_line}-{end_line} for {path}")
    excerpt = b"".join(lines[start_line - 1 : end_line])
    if not excerpt.endswith((b"\n", b"\r")):
        raise ValueError(f"Raw component must end at a captured line boundary: {path}:{end_line}")
    return excerpt


def component_excerpt(component: dict[str, Any]) -> bytes:
    return line_excerpt(
        SOURCES[component["source"]],
        int(component["start_line"]),
        int(component["end_line"]),
    )


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


def render_instruction() -> str:
    generic = SOURCES["r12_instruction"].read_text(encoding="utf-8")
    if generic.count(R12_MARKER) != 1:
        raise ValueError("r12 route marker changed")
    prefix = generic.split(R12_MARKER, 1)[0]
    if prefix.count(OLD_INDEX_PARAGRAPH) != 1:
        raise ValueError("generic external-index paragraph changed")
    prefix = prefix.replace(OLD_INDEX_PARAGRAPH, NEW_INDEX_PARAGRAPH)
    instruction = prefix.rstrip("\r\n") + "\n\n" + ROUTE_INSTRUCTIONS
    if utf16_units(instruction) > 8000:
        raise ValueError(f"Candidate instruction exceeds 8000 UTF-16 code units: {utf16_units(instruction)}")
    return instruction


def render_bundle(actual_source_sha: dict[str, str]) -> tuple[bytes, list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    for component in COMPONENTS:
        excerpt = component_excerpt(component)
        records.append(
            {
                **component,
                "source_path": relative(SOURCES[component["source"]]),
                "source_sha256": actual_source_sha[component["source"]],
                "excerpt_sha256": sha256_bytes(excerpt),
                "excerpt_bytes": len(excerpt),
            }
        )

    header_lines = [
        "PAD Robin fixed-helper A2 self-contained teaching bundle",
        f"candidate_id: {CANDIDATE_ID}",
        f"route_id: {ROUTE_ID}",
        "status: LOCAL_PREPARED_NON_LIVE_NOT_RUN",
        "",
        "BOUNDARY",
        "- IN-BUNDLE INDEX and every required RAW_COMPONENT are in this same attachment.",
        "- Each RAW_COMPONENT is an exact byte slice of an existing PAD capture/re-copy; mixed line endings are intentionally preserved.",
        "- The components may be reused, combined, repeated, and changed only at listed mutable parameters.",
        "- The resulting A2 composition is NOT_RUN_NEW_COMBINATION.",
        "- A complete fixed-EX03 Robin, fixed grading values, and fixed-EX03 full wiring are intentionally absent to preserve teaching/test independence.",
        "- Absence of those three items is not a missing syntax basis and is not a reason to refuse generation.",
        "- Do not invent an action, argument, enum, or block shape not present in these raw components.",
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
    for record in records:
        dependencies = ",".join(record["dependencies"]) if record["dependencies"] else "none"
        mutable = "; ".join(record["mutable_parameters"]) if record["mutable_parameters"] else "none"
        immutable = "; ".join(record["immutable_syntax"])
        header_lines.extend(
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

    header_lines.extend(
        [
            "",
            "REQUIREMENT TO COMPONENT COVERAGE",
        ]
    )
    for coverage in REQUIREMENT_COVERAGE:
        header_lines.append(
            f"- {coverage['id']} {coverage['requirement']}: {','.join(coverage['components'])} / COVERED"
        )
    header_lines.extend(
        [
            "",
            "NEW COMPOSITION PARAMETERS — NOT ROBIN / NOT CAPTURED / NOT RUN",
            "- Use C01, then C02 as the outer guard opening; place C03 through C12 in its ELSE body. C12 contains the captured closing END for that outer guard.",
            "- Repeat C03 for the unchanged fixed request's two read-only source workbooks, explicit sheets, and two source rectangles.",
            "- Repeat C04 from four demonstrated values to seven source JSON files plus one mode JSON file; reuse its captured SET-from-DataTable shape for five numeric source variables without JSON conversion.",
            "- Copy C06 and C07 without edits; their fixed paths, SHA literals, success JSON, and block shape are immutable.",
            "- Reindent and repeat C08 only as needed inside the captured success gate to activate each target sheet; repeat C09 from one demonstrated WriteCell to five fixed-request numeric targets.",
            "- Adapt C10 readback from one demonstrated rectangle to the two fixed-request output rectangles.",
            "- Repeat C11 from four demonstrated JSON comparisons to the twelve fixed-request source-versus-saved positions.",
            "- Keep C12 as the failure exit for both exact-output rejection and non-NORMAL mode; neither branch may contain SaveAs.",
            "- These counts and parameter substitutions describe the requested new composition; they are not a claim that the composed A2 has run.",
            "",
            "RAW COMPONENTS",
        ]
    )

    parts: list[bytes] = [("\n".join(header_lines) + "\n").encode("utf-8")]
    for record in records:
        parts.append((f"\nRAW COMPONENT METADATA {record['id']}\n").encode("utf-8"))
        parts.append(component_marker(record["id"], "BEGIN"))
        parts.append(component_excerpt(record))
        parts.append(component_marker(record["id"], "END"))
    parts.append(
        (
            "\nEND OF SELF-CONTAINED A2 BUNDLE\n"
            "The raw blocks above are source material, not a complete fixed-EX03 answer and not an executed A2 flow.\n"
        ).encode("utf-8")
    )
    bundle = b"".join(parts)

    for record in records:
        extracted = extract_component(bundle, record["id"])
        if extracted != component_excerpt(record):
            raise ValueError(f"Raw component changed while rendering: {record['id']}")
    return bundle, records


def render_coverage(records: list[dict[str, Any]]) -> str:
    record_by_id = {record["id"]: record for record in records}
    lines = [
        f"# {CANDIDATE_ID} teaching coverage",
        "",
        "This is a non-live coverage record for the same-version A2 bundle. It does not",
        "claim Copilot generation, PAD save/re-copy, PAD/Excel execution, or acceptance.",
        "",
        "| Requirement | Covered by | Source condition | New-combination boundary |",
        "| --- | --- | --- | --- |",
    ]
    for coverage in REQUIREMENT_COVERAGE:
        component_ids = coverage["components"]
        scopes = "<br>".join(record_by_id[item]["execution_scope"] for item in component_ids)
        lines.append(
            f"| {coverage['id']} — {coverage['requirement']} | {', '.join(component_ids)} | {scopes} | COVERED; A2 composition NOT_RUN |"
        )
    lines.extend(
        [
            "",
            "## Limited non-live conclusions",
            "",
            "- Missing required syntax steps: none.",
            "- Every raw block is byte-identical to its cited source line slice.",
            "- C06 decodes to the fixed launcher after restoring only its captured terminal LF.",
            "- Fixed helper, invocation, launcher, request, spec, expected data, runtime path,",
            "  and formal output contract are unchanged.",
            "- A2 parameter substitution, repetition, and full ordering remain an unexecuted new combination.",
            "- The bundle omits the complete fixed-EX03 answer, grader values, and fixed-EX03 full wiring.",
            "",
        ]
    )
    return "\n".join(lines)


def render_placement(actual_source_sha: dict[str, str]) -> str:
    return f"""# {CANDIDATE_ID} placement and boundary

Route: `{ROUTE_ID}`. This is teaching preparation only. It is not a Copilot
generation result and does not inherit the fixed-helper T2 auxiliary PASS.

## Later Copilot input, only if separately authorized

Use the unchanged fixed EX03 request, the complete same-version
`agent-instructions.txt`, and attach exactly
`knowledge/PAD-Robin-Fixed-Helper-A2-Bundle.txt`.

The bundle is self-contained for the requested limited route: its internal
index points to the exact raw components included in that file. No external
`PAD-Robin-00-Index.txt` or unbundled Robin source is a generation prerequisite.

## Verifier-preplaced immutable runtime

| Role | Existing path | Required SHA-256 |
| --- | --- | --- |
| helper | `{SOURCES['helper'].resolve()}` | `{actual_source_sha['helper']}` |
| invocation | `{SOURCES['invocation'].resolve()}` | `{actual_source_sha['invocation']}` |
| launcher source | `{SOURCES['launcher'].resolve()}` | `{actual_source_sha['launcher']}` |

Copilot must not create, modify, inline, or rederive helper or invocation. It
copies the complete captured C06 RunScript action without changing the decoded
launcher. The fixed invocation remains the source of the dedicated runtime
path.

## Teaching/test separation

The attachment supplies verified generic action components and the contracted
fixed launcher action. It does not supply the complete fixed-EX03 Robin, fixed
grader values, or fixed-EX03 full wiring. Paths, sheets, ranges, targets,
variable names, and repetition counts are adapted only as listed in the bundle;
their composition is `NOT_RUN_NEW_COMBINATION`.

A1 files and its refusal remain unchanged. Formal r12 remains FAIL. The T2
result remains PASS only for its original auxiliary Run1. The legacy 558 raw
difference record is preserved.

## Current scope

Copilot send, PAD save/re-copy, PAD/Excel run, full regression, candidate
acceptance, and GitHub write are all outside this preparation and were not run.
"""


def build(destination: Path = DESTINATION) -> dict[str, Any]:
    destination = Path(destination)
    if destination.exists() and any(path.is_file() for path in destination.rglob("*")):
        raise ValueError(f"Candidate already exists: {destination}")

    actual_source_sha = {name: sha256(path) for name, path in SOURCES.items()}
    if actual_source_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"Protected source SHA mismatch: {actual_source_sha}")

    formal = json.loads(SOURCES["formal_r12_status"].read_text(encoding="utf-8"))
    t2_result = json.loads(SOURCES["t2_result"].read_text(encoding="utf-8"))
    r2r3_result = json.loads(SOURCES["r2r3_final_verification"].read_text(encoding="utf-8"))
    if formal["status"] != "FAIL_GENERATED_ROBIN_MISMATCH_AND_POWERSHELL_PARSE_ERROR_STOP_BEFORE_PAD":
        raise ValueError("Formal r12 failure boundary changed")
    if formal["accepted"] or formal["pad"]["run1"] != "NOT_RUN_STOP_CONDITION":
        raise ValueError("Formal r12 acceptance boundary changed")
    if t2_result["decision"] != "PASS_FIXED_HELPER_AUXILIARY_NORMAL_RUN1":
        raise ValueError("T2 auxiliary result boundary changed")
    if r2r3_result["result"] != "PASS_NORMAL_AND_FORCED_EXCEPTION_ONE_RUN_EACH":
        raise ValueError("R2/R3 component source evidence boundary changed")

    instruction = render_instruction()
    bundle, component_records = render_bundle(actual_source_sha)

    c06 = next(record for record in component_records if record["id"] == "C06_FIXED_LAUNCHER_RUNSCRIPT")
    c06_text = component_excerpt(c06).decode("utf-8").replace("\r\n", "\n")
    decoded_launcher = embedded_script(c06_text)
    launcher_bytes = SOURCES["launcher"].read_bytes()
    if not launcher_bytes.endswith(b"\n") or b"\r\n" in launcher_bytes:
        raise ValueError("Fixed launcher terminal-LF or LF-only contract changed")
    if decoded_launcher.encode("utf-8") + b"\n" != launcher_bytes:
        raise ValueError("C06 no longer decodes to the fixed launcher plus its terminal LF")
    decoded_launcher_restored_sha = sha256_bytes(decoded_launcher.encode("utf-8") + b"\n")
    if decoded_launcher_restored_sha != actual_source_sha["launcher"]:
        raise ValueError("Decoded launcher restored SHA mismatch")

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
    c06_bytes = extract_component(bundle, "C06_FIXED_LAUNCHER_RUNSCRIPT")
    independent_material = bundle.replace(c06_bytes, b"[C06_FIXED_LAUNCHER_RUNSCRIPT_FIXED_CONTENT_REMOVED_FOR_LEAK_CHECK]\n")
    independent_text = independent_material.decode("utf-8")
    leaked = [term for term in forbidden_fixed_terms if term in independent_text]
    if leaked:
        raise ValueError(f"Fixed EX03 answer terms leaked into independent teaching material: {leaked}")
    if SOURCES["helper"].read_bytes() in bundle:
        raise ValueError("Helper body leaked into A2 bundle")
    if SOURCES["invocation"].read_bytes() in bundle:
        raise ValueError("Invocation JSON leaked into A2 bundle")
    if SOURCES["t2_pad_recopy"].read_bytes() in bundle:
        raise ValueError("Complete T2 Robin leaked into A2 bundle")
    if SOURCES["r2r3_normal_recopy"].read_bytes() in bundle:
        raise ValueError("Complete R2/R3 Robin leaked into A2 bundle")
    if SOURCES["fixed_expected"].read_bytes() in bundle:
        raise ValueError("Fixed grader data leaked into A2 bundle")

    instruction_path = destination / "agent-instructions.txt"
    bundle_path = destination / "knowledge/PAD-Robin-Fixed-Helper-A2-Bundle.txt"
    coverage_path = destination / "COVERAGE.md"
    placement_path = destination / "PLACEMENT.md"
    verification_path = destination / "non-live-verification.json"

    write_text(instruction_path, instruction)
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.write_bytes(bundle)
    write_text(coverage_path, render_coverage(component_records))
    write_text(placement_path, render_placement(actual_source_sha))

    verification = {
        "schema_version": 1,
        "candidate_id": CANDIDATE_ID,
        "route_id": ROUTE_ID,
        "decision": "PASS_TEACHING_PREPARATION_NON_LIVE_ONLY",
        "checks": {
            "protected_source_sha256_all_match": True,
            "a1_instruction_bundle_manifest_placement_response_assessment_unchanged": True,
            "same_version_bundle_internal_index_present": True,
            "required_raw_components_in_same_bundle": True,
            "raw_component_count": len(component_records),
            "raw_components_byte_exact_to_cited_source_slices": True,
            "requirement_count": len(REQUIREMENT_COVERAGE),
            "requirements_covered": len(REQUIREMENT_COVERAGE),
            "missing_required_steps": [],
            "decoded_launcher_exact_before_terminal_lf": True,
            "decoded_launcher_terminal_lf_restored_sha256": decoded_launcher_restored_sha,
            "decoded_launcher_matches_fixed_launcher_sha256": decoded_launcher_restored_sha
            == actual_source_sha["launcher"],
            "fixed_launcher_sha256": actual_source_sha["launcher"],
            "instruction_uses_internal_index_not_external_index": "PAD-Robin-00-Index.txt" not in instruction,
            "instruction_allows_verified_reuse_combination_and_listed_parameter_changes": True,
            "new_combination_marked_not_run": True,
            "prior_complete_flow_execution_not_generation_prerequisite": True,
            "no_fabrication_rule_preserved": True,
            "complete_fixed_ex03_robin_absent": True,
            "fixed_grader_values_absent": True,
            "fixed_ex03_full_wiring_absent": True,
            "helper_body_absent": True,
            "invocation_json_absent": True,
            "teaching_test_independence": "PASS",
        },
        "components": [
            {
                "id": record["id"],
                "source_path": record["source_path"],
                "source_sha256": record["source_sha256"],
                "source_lines": [record["start_line"], record["end_line"]],
                "excerpt_sha256": record["excerpt_sha256"],
                "excerpt_bytes": record["excerpt_bytes"],
                "dependencies": record["dependencies"],
                "mutable_parameters": record["mutable_parameters"],
                "execution_scope": record["execution_scope"],
                "bundle_exact": True,
            }
            for record in component_records
        ],
        "coverage": [
            {**coverage, "status": "COVERED"} for coverage in REQUIREMENT_COVERAGE
        ],
        "preserved_boundaries": {
            "formal_r12_status": formal["status"],
            "formal_r12_accepted": formal["accepted"],
            "t2_decision": t2_result["decision"],
            "t2_scope": t2_result["scope"],
            "r2r3_result": r2r3_result["result"],
            "a1_result": "REFUSED_NO_CODE_BLOCK_PAD_NOT_RUN",
            "legacy_558_difference_record": "PRESERVED_NOT_RECLASSIFIED",
        },
        "scope": {
            "copilot_send_count": 0,
            "pad_save_recopy_count": 0,
            "pad_run_count": 0,
            "excel_run_count": 0,
            "new_capture_count": 0,
            "successful_probe_rerun_count": 0,
            "full_regression": "NOT_RUN_BY_SCOPE",
            "github_write_count": 0,
        },
    }
    write_json(verification_path, verification)

    artifacts = {
        "instruction": artifact_record(instruction_path, destination),
        "bundle": artifact_record(bundle_path, destination),
        "coverage": artifact_record(coverage_path, destination),
        "placement": artifact_record(placement_path, destination),
        "non_live_verification": artifact_record(verification_path, destination),
    }
    payload_files = [instruction_path, bundle_path, coverage_path, placement_path, verification_path]
    manifest = {
        "schema_version": 1,
        "candidate_id": CANDIDATE_ID,
        "route_id": ROUTE_ID,
        "status": "LOCAL_PREPARED_NON_LIVE_NOT_COPILOT_OR_PAD_ACCEPTED",
        "base_commit": BASE_COMMIT,
        "successor_to": "20260918-excel-r12-fixed-helper-a1",
        "a1_files_modified": False,
        "replaces_formal_r12": False,
        "inherits_t2_auxiliary_pass": False,
        "artifacts": artifacts,
        "candidate_payload_sha256": payload_sha256(destination, payload_files),
        "candidate_payload_sha256_algorithm": "SHA256(sorted relative UTF-8 path + NUL + bytes + NUL)",
        "source_evidence": {name: source_record(name, path) for name, path in SOURCES.items()},
        "instruction_contract": {
            "utf16_code_units": utf16_units(instruction),
            "max_utf16_code_units": 8000,
            "formal_output": "EXACTLY_ONE_MARKDOWN_TEXT_CODE_BLOCK_WHEN_GENERATION_IS_POSSIBLE",
            "internal_bundle_index_only": True,
            "verified_components_may_be_reused_combined_repeated": True,
            "listed_parameter_changes_allowed": True,
            "new_combination_status": "NOT_RUN_NEW_COMBINATION",
            "prior_complete_flow_execution_required_before_generation": False,
            "fabrication_of_uncaptured_syntax_allowed": False,
            "on_actual_missing_basis": "NO_ROBIN_AND_REPORT_ONLY_MISSING_STEP",
        },
        "fixed_contract": {
            "helper_sha256": actual_source_sha["helper"],
            "invocation_sha256": actual_source_sha["invocation"],
            "launcher_sha256": actual_source_sha["launcher"],
            "decoded_launcher_terminal_lf_restored_sha256": decoded_launcher_restored_sha,
            "success_output": EXPECTED_SUCCESS,
            "source_json_write_count": 7,
            "mode_json_write_count": 1,
            "numeric_write_count": 5,
            "save_as_count": 1,
            "saved_value_type_comparison_count": 12,
            "helper_invocation_launcher_runtime_path_fixed_request_expected_and_output_format_changed": False,
        },
        "component_records": component_records,
        "requirement_coverage": [
            {**coverage, "status": "COVERED"} for coverage in REQUIREMENT_COVERAGE
        ],
        "missing_required_steps": [],
        "teaching_independence": {
            "complete_fixed_ex03_robin_in_bundle": False,
            "fixed_expected_or_grader_values_in_bundle": False,
            "fixed_ex03_full_wiring_in_bundle": False,
            "helper_body_in_bundle": False,
            "invocation_json_in_bundle": False,
            "contracted_fixed_launcher_runscript_in_bundle": True,
            "generic_captured_components_in_bundle": True,
            "parameter_adaptation_marked_new_not_captured_not_run": True,
            "status": "PASS",
        },
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
