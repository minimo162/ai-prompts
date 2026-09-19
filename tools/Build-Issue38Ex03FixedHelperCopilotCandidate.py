#!/usr/bin/env python3
"""Build the non-live EX03 fixed-helper Copilot alternate-route candidate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "20260918-excel-r12-fixed-helper-a1"
ROUTE_ID = "EX03-R12-FIXED-HELPER-COPILOT-A1"
BASE_COMMIT = "11a1c49cf7259f4b904294f934138bf5304eddc9"
DESTINATION = ROOT / "copilot/versions" / CANDIDATE_ID
PROBE = ROOT / "catalog/acceptance/issue38/probes/ex03-r12-fixed-helper"
T1 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T1"
T2 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T2"
EXPECTED_SUCCESS = '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}'

SOURCES = {
    "helper": PROBE / "EX03-R12-Fixed-StringTransfer.ps1",
    "invocation": T1 / "invocation.json",
    "launcher": T1 / "launcher.ps1",
    "t2_pad_recopy": T2 / "pad-recopy-before-run.robin",
    "fixed_request": ROOT / "catalog/acceptance/issue38/requests/EX03.txt",
    "fixed_spec": ROOT / "catalog/acceptance/issue38/spec.json",
    "fixed_expected": ROOT / "catalog/acceptance/issue38/expected.json",
    "r12_instruction": ROOT / "copilot/versions/20260917-excel-r12/agent-instructions.txt",
    "formal_r12_status": ROOT / "catalog/acceptance/issue38/cycles/EX03-r12-G1/acceptance-status.json",
    "t2_result": T2 / "result.json",
    "fh_r1_validator": PROBE / "Finalize-TrialT2.py",
    "fh_r1_tests": ROOT / "tests/Test-Issue38Ex03FixedHelperTrialT2.py",
    "fh_r1_correction": PROBE / "reviews/FH-R1-corrections.json",
}

EXPECTED_SOURCE_SHA256 = {
    "helper": "08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135",
    "invocation": "92ea864a7e43cec61b4215592a3bae9b8b31109af4e18d3ff0a79dcb15fc5ad6",
    "launcher": "1e9750385455999460e9b1dce754e2a649d4837ae1939cd444376fc360a25ee1",
    "t2_pad_recopy": "da54e5f4388cd0bb896ee00e534e9d81a444f5b950ac1f1bf006f8ea788ad4aa",
    "fixed_request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "fixed_spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "fixed_expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
    "r12_instruction": "11321acdbb96632221b02b7b737d12ba816ea4cf9f35f933a114c7f857539c06",
    "formal_r12_status": "216089662ce7a5170d22eb3958a7641ecdee3ca00a95526d98eff2a70dc042ab",
    "t2_result": "66b35d9686bfc17fb8bebf0c0c65f083cba647087417d52b852d3615fe7d14c1",
    "fh_r1_validator": "938c233a7ce380dcf218fbae026a02b7eb757e92f7aac559962154dd00acf48f",
    "fh_r1_tests": "a8eacf31f7d6273cd4a8c4f9efeb93a295cb6233daa2e926e783f7b1a254f2d5",
    "fh_r1_correction": "6db55a719c3f3178b27c3fd863d50ee95c2b81e48b095e29608b28470940caa0",
}

SOURCE_ROLES = {
    "helper": "VERIFIER_PREPLACED_RUNTIME_DEPENDENCY_NOT_COPILOT_OUTPUT",
    "invocation": "VERIFIER_PREPLACED_FIXED_EX03_CONFIGURATION_NOT_COPILOT_OUTPUT",
    "launcher": "VERIFIER_FIXED_SOURCE_COPIED_INTO_GENERATED_RUNSCRIPT",
    "t2_pad_recopy": "VALIDATOR_ONLY_EXECUTED_REFERENCE_NOT_COPILOT_ATTACHMENT",
    "fixed_request": "VERBATIM_LOGICAL_REQUEST_PRESERVED",
    "fixed_spec": "VERIFIER_FIXED_SPEC_NOT_COPILOT_ATTACHMENT",
    "fixed_expected": "VERIFIER_GRADING_DATA_NOT_COPILOT_ATTACHMENT",
    "r12_instruction": "GENERIC_INSTRUCTION_PREFIX_SOURCE",
    "formal_r12_status": "PRESERVED_FORMAL_FAIL_BOUNDARY",
    "t2_result": "PRESERVED_AUXILIARY_PASS_NOT_INHERITED",
    "fh_r1_validator": "FH_R1_READ_ONLY_OBSERVATION_VALIDATOR",
    "fh_r1_tests": "FH_R1_POSITIVE_AND_NEGATIVE_TESTS",
    "fh_r1_correction": "FH_N1_CORRECTION_RECORD",
}

R12_MARKER = "\n【Excel値転記・20260917-excel-r12候補】"

ROUTE_INSTRUCTIONS = r"""【Excel値転記・固定helper別経路 20260918-excel-r12-fixed-helper-a1】
この候補は正式EX03-r12-G1とも固定helper補助試験P1とも異なる未使用IDのCopilot生成試験候補です。正式r12 FAIL、T2補助PASS、旧558 raw差分、固定依頼、spec、expectedを分離して保持し、過去PASSをこの候補へ継承しません。

標準入力は、catalog/acceptance/issue38/requests/EX03.txt の固定依頼を変更せず先頭に置いた本文、この指示全文、同じ候補IDのbundle実添付です。今回は通常の日本語依頼からhelperやinvocationなどの実行設定まで自動生成する試験ではありません。検証者がhelperと固定invocationを指定パスへ事前配置し、SHA-256を検証してから生成試験を開始する限定経路です。

Copilotが生成するのは、固定launcherを1個のRun PowerShell Scriptへ入れたPADの前後処理です。helper本体とinvocation JSONは生成またはインライン展開しません。helperとinvocationの期待SHAは検証者管理であり、回答や依頼本文から再計算、提案、変更しません。bundleのFIXED LAUNCHER SOURCEを、その検証者固定SHAリテラルを含めて内容変更なしでRobin文字列へ埋め込みます。

事前配置される固定runtimeは次です。
- helper: C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\probes\ex03-r12-fixed-helper\EX03-R12-Fixed-StringTransfer.ps1
- invocation: C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\probes\ex03-r12-fixed-helper\trials\EX03-R12-FIXED-HELPER-P1-T1\invocation.json
- JSON/work/output領域: C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\probes\ex03-r12-fixed-helper\trials\EX03-R12-FIXED-HELPER-P1-T1\runtime
この専用runtimeは別経路の実行境界です。固定依頼内の `runs\EX03-attempt1\work.xlsx` と出力パスは凍結文面として保持しますが、この別経路の実行設定には使いません。別経路では事前配置invocationが指定するruntimeを優先します。固定依頼の入力ファイル、シート、矩形、転記先、値・型・位置の期待値は変更しませんが、正式r12の依頼パス適合や実行結果として扱いません。

生成フローは、既存output guard、2入力のReadOnly読取りと明示的シート切替、TypedValues矩形読取り、7文字列のJSON primitive化とsource-1.jsonからsource-7.jsonへのUTF-8書込み、NORMALのmode.json書込み、work.xlsx起動、固定launcher 1回、exact success JSONとPAD側NORMALの二重gate、5数値WriteCell、未存在の照合結果.xlsxへのSaveAs、close、ReadOnly再開、2矩形12位置の個別JSON値型比較、失敗側close/no-saveの順を保持します。

PowerShell出力は {"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true} と文字列完全一致し、かつRunModeがNORMALの場合だけ数値書込みとSaveAsへ進みます。空、ERROR、別出力、別modeでは後続書込み、SaveAs、完成状態へ進みません。既存output時はJSON生成、work起動、helper実行より前に停止します。

入力と原本はReadOnly、検証者が用意したwork copyだけを編集します。network、delete、上書き、Invoke-Expression、外部から取得したSHA、権限・security・Excel設定変更を追加しません。helperとinvocationを作成または更新するFile.WriteTextも生成しません。

教材のINDEPENDENT TEACHING FRAGMENTSは構文断片だけです。固定EX03と異なる1入力・2x2・別sheet/target/path条件で、完成フロー、固定EX03の答え、採点値を含みません。そこから固定EX03のセル値を推測せず、固定依頼と固定launcher契約だけを使います。検証者用T2 PAD再コピー原文はbundleへ含まれず、生成後の差分検査にだけ使われます。

回答は説明の後に、全工程のRobinだけを正確に1個のMarkdown `text` コードブロックへ入れます。コードブロック内へ説明、見出し、行番号、Plain Text、JSON、Markdownフェンス文字列、省略記号、疑似コードを入れません。先頭行と最終非空行は実際のPAD命令にします。条件を満たせない場合はRobinを出さず、不足を説明します。

この候補はCopilot未送信、PAD保存・再コピー未実施、PAD/Excel Run 0です。生成後も無修正原文の安全検査と保存・再コピー一致が通るまで実行済み、完成済み、受入済みと表示しません。
"""

INDEPENDENT_TEACHING = r"""INDEPENDENT TEACHING FRAGMENTS BEGIN
状態: STATIC_FRAGMENT_ONLY_NOT_COMPLETE_NOT_RUN
条件: C:\\VerifierTraining\\lesson-source.xlsx / 教材入力 H3:I4 (2x2) を、lesson-work.xlsx / 教材出力 J4から扱う別条件。入力は1冊だけで、固定EX03の2入力・3x2/2x3矩形・sheet・target・期待値とは異なる。

FRAGMENT A - ReadOnlyで別条件の小矩形を読む:
Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: $'''C:\\VerifierTraining\\lesson-source.xlsx''' Visible: True ReadOnly: True UseMachineLocale: False Instance=> ExampleInput
Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: ExampleInput Name: $'''教材入力'''
Excel.ReadFromExcel.ReadCells Instance: ExampleInput StartColumn: $'''H''' StartRow: 3 EndColumn: $'''I''' EndRow: 4 GetCellContentsMode: Excel.GetCellContentsMode.TypedValues FirstLineIsHeader: False RangeValue=> ExampleData
Excel.CloseExcel.Close Instance: ExampleInput

FRAGMENT B - 1値だけをJSON primitive化して教材専用ファイルへ渡す:
SET ExampleText TO ExampleData[0][0]
Variables.ConvertCustomObjectToJson CustomObject: { 'probe': ExampleText } Json=> ExampleTextJson
File.WriteText File: $'''C:\\VerifierTraining\\example-source.json''' TextToWrite: ExampleTextJson AppendNewLine: False IfFileExists: File.IfFileExists.Overwrite Encoding: File.FileEncoding.UTF8

FRAGMENT C - Robin内の短い独立RunScriptエスケープ例:
Scripting.RunPowershellScript.RunScript Script: $'''$ErrorActionPreference = \'Stop\'
[Console]::Out.Write(\'TRAINING_ONLY\')''' ScriptOutput=> ExampleScriptOutput

FRAGMENT D - 成功出力とmodeの二重gateという形だけを示す:
IF ExampleScriptOutput = $'''TRAINING_ONLY''' THEN
    IF ExampleMode = $'''TRAINING''' THEN
        SET ExampleGatePassed TO True
    ELSE
        SET ExampleState TO $'''MODE_REJECTED'''
    END
ELSE
    SET ExampleState TO $'''SCRIPT_REJECTED'''
END

この4断片は連結可能な完成回答ではなく、SaveAs、固定launcher、固定routing、12位置照合、固定EX03の値や採点変数を含まない。
INDEPENDENT TEACHING FRAGMENTS END
"""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def utf16_units(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


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
        raise ValueError("T2 reference must contain exactly one PowershellOutput RunScript")
    start = robin.index(prefix) + len(prefix)
    end = robin.index(suffix, start)
    return decode_robin_string(robin[start:end])


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def artifact_record(path: Path, destination: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(destination).as_posix(),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def source_record(name: str, path: Path) -> dict[str, object]:
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
        name = path.relative_to(destination).as_posix().encode("utf-8")
        digest.update(name)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def build(destination: Path = DESTINATION) -> dict[str, object]:
    destination = Path(destination)
    if destination.exists():
        raise ValueError(f"Candidate already exists: {destination}")

    actual_source_sha = {name: sha256(path) for name, path in SOURCES.items()}
    if actual_source_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"Protected source SHA mismatch: {actual_source_sha}")

    formal = json.loads(SOURCES["formal_r12_status"].read_text(encoding="utf-8"))
    t2_result = json.loads(SOURCES["t2_result"].read_text(encoding="utf-8"))
    if formal["status"] != "FAIL_GENERATED_ROBIN_MISMATCH_AND_POWERSHELL_PARSE_ERROR_STOP_BEFORE_PAD":
        raise ValueError("Formal r12 failure boundary changed")
    if formal["accepted"] or formal["pad"]["run1"] != "NOT_RUN_STOP_CONDITION":
        raise ValueError("Formal r12 acceptance boundary changed")
    if t2_result["decision"] != "PASS_FIXED_HELPER_AUXILIARY_NORMAL_RUN1":
        raise ValueError("T2 auxiliary decision changed")
    if "not formal EX03-r12 acceptance" not in t2_result["scope"]:
        raise ValueError("T2 auxiliary/formal boundary changed")

    launcher = SOURCES["launcher"].read_text(encoding="utf-8").rstrip("\r\n")
    t2_robin = SOURCES["t2_pad_recopy"].read_text(encoding="utf-8")
    if embedded_script(t2_robin) != launcher:
        raise ValueError("T2 PAD re-copy no longer decodes to the fixed launcher")
    if t2_robin.count("File.WriteText File:") != 8:
        raise ValueError("T2 JSON handoff write count changed")
    if t2_robin.count("Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource") != 5:
        raise ValueError("T2 numeric write count changed")
    if t2_robin.count("_ValueTypeMatch TO SourceCellJson = SavedCellJson") != 12:
        raise ValueError("T2 readback comparison count changed")
    if t2_robin.count("Excel.SaveExcel.SaveAs") != 1:
        raise ValueError("T2 SaveAs count changed")

    generic_instruction = SOURCES["r12_instruction"].read_text(encoding="utf-8")
    if generic_instruction.count(R12_MARKER) != 1:
        raise ValueError("r12 route marker changed")
    instruction = generic_instruction.split(R12_MARKER, 1)[0].rstrip("\r\n") + "\n\n" + ROUTE_INSTRUCTIONS
    if utf16_units(instruction) > 8000:
        raise ValueError("Candidate instruction exceeds 8000 UTF-16 code units")

    bundle = (
        "PAD Robin fixed-helper alternate-route bundle\n"
        f"candidate_id: {CANDIDATE_ID}\n"
        f"route_id: {ROUTE_ID}\n"
        "status: LOCAL_PREPARED_NON_LIVE\n\n"
        "BOUNDARY\n"
        "- This bundle is attached with the same candidate instruction.\n"
        "- The helper body, invocation JSON, fixed EX03 completed Robin, and grader expected values are intentionally absent.\n"
        "- The verifier preplaces helper and invocation and owns both expected SHA-256 values.\n"
        "- Copilot emits the fixed launcher, including verifier-owned SHA literals, inside one RunScript plus the surrounding PAD actions; it does not emit or modify helper/invocation files.\n"
        "- The T2 PAD re-copy is a validator-only source and is not copied into this attachment.\n\n"
        "VERIFIER-MANAGED IDENTITIES\n"
        f"- helper: {relative(SOURCES['helper'])} / SHA-256 {actual_source_sha['helper']}\n"
        f"- invocation: {relative(SOURCES['invocation'])} / SHA-256 {actual_source_sha['invocation']}\n"
        f"- fixed launcher source: {relative(SOURCES['launcher'])} / SHA-256 {actual_source_sha['launcher']}\n"
        f"- executed T2 PAD re-copy reference: {relative(SOURCES['t2_pad_recopy'])} / SHA-256 {actual_source_sha['t2_pad_recopy']}\n"
        "- Generated output copies these verifier-owned SHA literals only as part of the fixed launcher and must not replace or derive them.\n\n"
        "GENERATED SCOPE\n"
        "1. Existing-output no-write guard.\n"
        "2. Fixed request source reads, explicit sheet activation, TypedValues, and JSON handoff files.\n"
        "3. One RunScript containing the FIXED LAUNCHER SOURCE below.\n"
        f"4. Exact success output {EXPECTED_SUCCESS} plus PAD NORMAL gate.\n"
        "5. Five numeric writes, one SaveAs, close/reopen, and twelve individual JSON value/type comparisons.\n"
        "6. Failure closes Work and does not enter later writes or SaveAs.\n\n"
        "FIXED LAUNCHER SOURCE BEGIN\n"
        + launcher
        + "\nFIXED LAUNCHER SOURCE END\n\n"
        + INDEPENDENT_TEACHING
    )

    teaching = bundle.split("INDEPENDENT TEACHING FRAGMENTS BEGIN\n", 1)[1].split(
        "INDEPENDENT TEACHING FRAGMENTS END", 1
    )[0]
    forbidden_teaching_terms = (
        "入力い.xlsx",
        "入力ろ.xlsx",
        "受取明細",
        "追加項目",
        "集計先",
        "追記先",
        "EX03-attempt1",
        "_ValueTypeMatch",
        "Data1[0][0]",
        "100%",
        "項目甲",
    )
    present = [term for term in forbidden_teaching_terms if term in teaching]
    if present:
        raise ValueError(f"Fixed EX03 terms leaked into teaching fragments: {present}")
    if SOURCES["helper"].read_text(encoding="utf-8") in bundle:
        raise ValueError("Helper body leaked into Copilot bundle")
    if SOURCES["invocation"].read_text(encoding="utf-8") in bundle:
        raise ValueError("Invocation JSON leaked into Copilot bundle")
    if t2_robin in bundle:
        raise ValueError("Completed T2 Robin leaked into Copilot bundle")

    placement = f"""# {CANDIDATE_ID} placement and generation boundary

Candidate route: `{ROUTE_ID}`. This is a local non-live preparation. It is not
formal EX03-r12 acceptance and inherits no T2 PASS.

## Verifier preplacement

Before a separately authorized Copilot send, the verifier places or confirms
these existing files. Copilot must not create or modify them.

| Role | Exact path | Required SHA-256 |
| --- | --- | --- |
| helper | `{SOURCES['helper'].resolve()}` | `{actual_source_sha['helper']}` |
| fixed invocation | `{SOURCES['invocation'].resolve()}` | `{actual_source_sha['invocation']}` |

The invocation fixes `work.xlsx`, the JSON handoff directory, seven text
targets, and their routing. Its dedicated runtime takes precedence over the
frozen request's `runs\\EX03-attempt1` work/output paths for this alternate route.
This candidate therefore does **not** test automatic generation of execution
configuration from a Japanese request and does not claim formal request-path
compliance.

The verifier also prepares the fixed template copy at the invocation's
`target_workbook`, confirms that the dedicated output is absent, and retains the
unchanged input fixtures, request, spec, and expected records.

## Copilot input and generated scope

If a later goal authorizes one send, use the unchanged fixed EX03 request,
the complete `agent-instructions.txt`, and attach exactly
`knowledge/PAD-Robin-Fixed-Helper-Bundle.txt` from this candidate ID.

Copilot generates only:

- the existing-output guard and input/JSON/work setup before RunScript;
- one RunScript containing the bundle's fixed launcher source;
- the exact-success/NORMAL gate, numeric writes, SaveAs, close/reopen, and
  twelve value/type comparisons after RunScript.

Copilot does not generate the helper body, invocation JSON, fixture contents,
expected values, or verifier comparisons. It copies the fixed launcher including
the verifier-owned SHA literals, but does not derive or change those literals.

## Validator-only references

- fixed launcher: `{relative(SOURCES['launcher'])}` / `{actual_source_sha['launcher']}`
- executed T2 PAD re-copy: `{relative(SOURCES['t2_pad_recopy'])}` / `{actual_source_sha['t2_pad_recopy']}`

The T2 re-copy is not an attachment or teaching answer. It is retained only for
post-generation structure and launcher comparison. The teaching fragments in
the bundle use a different one-input 2x2 scenario and contain neither the fixed
EX03 completed answer nor grading values.

## Current boundary

Copilot send, PAD save/re-copy, PAD/Excel Run, candidate acceptance, full
regression, and GitHub write are all not run by this preparation.
"""

    instruction_path = destination / "agent-instructions.txt"
    bundle_path = destination / "knowledge/PAD-Robin-Fixed-Helper-Bundle.txt"
    placement_path = destination / "PLACEMENT.md"
    write_text(instruction_path, instruction)
    write_text(bundle_path, bundle)
    write_text(placement_path, placement)

    artifacts = {
        "instruction": artifact_record(instruction_path, destination),
        "bundle": artifact_record(bundle_path, destination),
        "placement": artifact_record(placement_path, destination),
    }
    payload_files = [instruction_path, bundle_path, placement_path]
    manifest = {
        "schema_version": 1,
        "candidate_id": CANDIDATE_ID,
        "route_id": ROUTE_ID,
        "status": "LOCAL_PREPARED_NON_LIVE_NOT_COPILOT_OR_PAD_ACCEPTED",
        "base_commit": BASE_COMMIT,
        "replaces_formal_r12": False,
        "inherits_t2_auxiliary_pass": False,
        "artifacts": artifacts,
        "candidate_payload_sha256": payload_sha256(destination, payload_files),
        "candidate_payload_sha256_algorithm": "SHA256(sorted relative UTF-8 path + NUL + bytes + NUL)",
        "source_evidence": {
            name: source_record(name, path) for name, path in SOURCES.items()
        },
        "copilot_input": {
            "fixed_request_path": relative(SOURCES["fixed_request"]),
            "fixed_request_verbatim": True,
            "fixed_request_logical_input_sheet_range_target_and_expectations_preserved": True,
            "runtime_path_source": "VERIFIER_PREPLACED_INVOCATION_FOR_ALTERNATE_ROUTE",
            "formal_request_runtime_path_compliance_claimed": False,
            "instruction_path": artifacts["instruction"]["path"],
            "attachment_path": artifacts["bundle"]["path"],
            "same_candidate_id": True,
        },
        "preplaced_by_verifier": {
            "helper": {
                "path": str(SOURCES["helper"].resolve()),
                "expected_sha256": actual_source_sha["helper"],
                "expected_sha256_owner": "VERIFIER",
            },
            "invocation": {
                "path": str(SOURCES["invocation"].resolve()),
                "expected_sha256": actual_source_sha["invocation"],
                "expected_sha256_owner": "VERIFIER",
            },
            "automatic_execution_configuration_from_japanese_request": False,
        },
        "copilot_generated": {
            "helper_body": False,
            "invocation_json": False,
            "helper_or_invocation_expected_sha_derived_or_changed": False,
            "verifier_owned_expected_sha_literals_copied_in_fixed_launcher": True,
            "fixed_launcher_inside_one_runscript": True,
            "pad_before_and_after_actions": True,
            "formal_response_text_code_block_count": 1,
        },
        "fixed_contract": {
            "success_output": EXPECTED_SUCCESS,
            "pad_mode": "NORMAL",
            "source_json_write_count": 7,
            "mode_json_write_count": 1,
            "numeric_write_count": 5,
            "save_as_count": 1,
            "saved_value_type_comparison_count": 12,
            "existing_output_no_write": True,
            "failure_close_no_save": True,
        },
        "teaching_independence": {
            "condition": "ONE_INPUT_2X2_H3_I4_TO_J4_DIFFERENT_PATH_SHEET_TARGET",
            "complete_fixed_ex03_robin_in_bundle": False,
            "fixed_expected_or_grader_values_in_bundle": False,
            "t2_pad_recopy_in_bundle": False,
            "helper_body_in_bundle": False,
            "invocation_json_in_bundle": False,
            "fixed_terms_absent_from_teaching_fragments": True,
        },
        "preserved_boundaries": {
            "formal_r12_status": formal["status"],
            "formal_r12_accepted": formal["accepted"],
            "t2_decision": t2_result["decision"],
            "t2_scope": t2_result["scope"],
            "fh_r1_commit": BASE_COMMIT,
            "legacy_558_difference_record": "PRESERVED_NOT_RECLASSIFIED",
        },
        "scope": {
            "copilot_send_count": 0,
            "pad_save_recopy_count": 0,
            "pad_run_count": 0,
            "excel_run_count": 0,
            "successful_probe_rerun": 0,
            "full_regression": "NOT_RUN_BY_SCOPE",
            "github_write_count": 0,
        },
    }
    write_json(destination / "manifest.json", manifest)
    return manifest


def main() -> int:
    manifest = build()
    print(json.dumps({
        "candidate_id": manifest["candidate_id"],
        "route_id": manifest["route_id"],
        "candidate_payload_sha256": manifest["candidate_payload_sha256"],
        "status": manifest["status"],
    }, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
