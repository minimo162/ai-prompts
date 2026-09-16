#!/usr/bin/env python3
"""Freeze the EX03 r8 successor with an independent PAD-recopied example.

The fixed EX03 request, grader data, r7, and prior refusal evidence are
read-only inputs.  The generated package removes the complete fixed EX03
answer from the current teaching section and replaces it with a different
same-shape example that was pasted, saved, and re-copied in a dedicated PAD
flow.  It does not send to Copilot or execute either example or EX03.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "copilot/versions/20260916-excel-r7"
R6 = ROOT / "copilot/versions/20260916-excel-r6"
VERSION = "20260916-excel-r8"
BASE_COMMIT = "806e4095a926fa0c7e020811c09770b5e5292841"
CAPTURE = ROOT / "catalog/acceptance/issue38/probes/ex03-r8-independent-source"
R6_CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r6-G1"
R7_MARKER = "Issue #38 EX03 / 20260916-excel-r7 候補の現在の範囲"
R7_INSTRUCTION_MARKER = "【Excel値転記・20260916-excel-r7候補】"
SCRIPT_SUPPORT = Path("support/EX03-R8-Independent-FormatSandwich.ps1.txt")
ROBIN_SUPPORT = Path("support/EX03-R8-Independent-PAD-Recopy.robin")

INPUTS = {
    "r7_manifest": BASE / "manifest.json",
    "r7_bundle": BASE / "knowledge/PAD-Robin-Knowledge-Bundle.txt",
    "r7_instruction": BASE / "agent-instructions.txt",
    "actually_sent_r6_bundle": R6 / "knowledge/PAD-Robin-Knowledge-Bundle.txt",
    "r6_refusal": R6_CYCLE / "response-rendered.txt",
    "r6_submitted_body": R6_CYCLE / "submitted-body.txt",
    "independence_before": CAPTURE / "independence-before.json",
    "preflight": CAPTURE / "preflight.json",
    "pad_capture": CAPTURE / "pad-capture.json",
    "candidate": CAPTURE / "candidate-full.robin",
    "candidate_action": CAPTURE / "candidate-action.robin",
    "candidate_script": CAPTURE / "candidate-script.ps1.txt",
    "pad_recopy": CAPTURE / "pad-recopy-full.robin",
    "fixed_request": ROOT / "catalog/acceptance/issue38/requests/EX03.txt",
    "fixed_spec": ROOT / "catalog/acceptance/issue38/spec.json",
    "grader_expected": ROOT / "catalog/acceptance/issue38/expected.json",
}

EXPECTED = {
    "r7_manifest": "38517f37be934b1bcf37c0e12f9f33c9e803fa174af15e41579ccdd612dc4e3f",
    "r7_bundle": "228329f60f17192f87878fb6393abf22520d051a1225d9905f2f71354216f1ed",
    "r7_instruction": "b888b7497c2c5a7fb79860c22da6be4b62f013731ab920e87dbb503ef1f0d7fa",
    "actually_sent_r6_bundle": "9c566e7f85a431f1869302c6a40985e2f81237f17ac4fbbdc9a73e62a646b580",
    "r6_refusal": "7c6f30590b3ee7905038f142c1974d7639c4579c44a6f445ae0a9ea22f58b342",
    "r6_submitted_body": "a9051689e227e74a904c20fb860f89935b5c393164629869bebbcc923e93903e",
    "independence_before": "5088b61512fd9418804e1b3f2427732bb179521bbdd05aa1c6f06ed16aa6e7cf",
    "preflight": "61d9af47c8b88ec073ee89f6ad79bd5e952aa0ece5338b850a1ca1ebd87dc3f8",
    "pad_capture": "70ef473d86462fe09ab7c498eef97744c92f04d2d5304c41f61e42f45a7e17c0",
    "candidate": "6d9c23eabfacbcd65b1a18eabf5681805494e41171f94a9b01a28b24452815bb",
    "candidate_action": "283dca2c49814aa842e820b30b1a6ab269a693723af7f3d84517950c140a2d2b",
    "candidate_script": "65b86b0e5be4ec2da30e57a6bd858e395d1103da2d05ab2e7607362772d1dfd9",
    "pad_recopy": "6d9c23eabfacbcd65b1a18eabf5681805494e41171f94a9b01a28b24452815bb",
    "fixed_request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "fixed_spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "grader_expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
}

ACTION_PREFIX = "Scripting.RunPowershellScript.RunScript Script: $'''"
ACTION_SUFFIX = "''' ScriptOutput=> PowershellOutput"

FIXED_ROOT = r"C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\acceptance\\issue38"
FIXED_COMPLETION_TERMS = [
    FIXED_ROOT + r"\\fixtures\\EX03\\入力い.xlsx",
    FIXED_ROOT + r"\\fixtures\\EX03\\入力ろ.xlsx",
    FIXED_ROOT + r"\\runs\\EX03-attempt1\\work.xlsx",
    FIXED_ROOT + r"\\runs\\EX03-attempt1\\照合結果.xlsx",
    "受取明細",
    "追加項目",
    "集計先",
    "追記先",
]
UNIQUE_GRADER_STRINGS = ["春", "夏", "秋", "項目甲", "項目乙"]
EXAMPLE_ROOT = r"C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\teaching\\excel-r8-example"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def normalized(value: str) -> str:
    return value.replace("\r\n", "\n").rstrip("\n")


def decode_robin_string(value: str) -> str:
    decoded: list[str] = []
    index = 0
    while index < len(value):
        if (
            value[index] == "\\"
            and index + 1 < len(value)
            and value[index + 1] in {"\\", "'", '"'}
        ):
            decoded.append(value[index + 1])
            index += 2
        else:
            decoded.append(value[index])
            index += 1
    return "".join(decoded)


def extract_action(flow: str) -> str:
    normalized_flow = normalized(flow)
    start = normalized_flow.index(ACTION_PREFIX)
    end = normalized_flow.index(ACTION_SUFFIX, start) + len(ACTION_SUFFIX)
    lines = normalized_flow[start:end].split("\n")
    return "\n".join([lines[0], *(line[4:] for line in lines[1:])])


def action_payload(action: str) -> str:
    value = action.rstrip("\r\n")
    if not value.startswith(ACTION_PREFIX) or not value.endswith(ACTION_SUFFIX):
        raise ValueError("PowerShell action wrapper differs from the captured form")
    return value[len(ACTION_PREFIX) : -len(ACTION_SUFFIX)]


def example_mapping() -> str:
    return """r8独立教材例のデータ対応（固定する命令構造と、変更するデータを分離）:
- source-one.xlsx / 教材入力一 H3:I5 -> 教材出力一 J4:K6。各行の第1列はtext、第2列はnumber。
- source-two.xlsx / 教材入力二 C7:E8 -> 教材出力二 B10:D11。各行はtext, number, text。
- work-copy.xlsxだけを編集し、未存在のexample-result.xlsxへSaveAsする。
- 文字列7位置は同一RunのDataTableをJSON primitiveで確認して内包scriptから各1回、数値5位置は通常WriteCellから各1回だけ書く。保存・クローズ・ReadOnly再開後に12位置を同じsource/readbackキーでJSON比較する。
- 固定するもの: 命令名、引数名、モード、DataTable添字、型の役割、依存順、分岐、1 RunScript、5 numeric writes、12 JSON comparisons。
- 依頼から変更するもの: 同じ確認範囲内のファイルパス、存在するシート名、3x2と2x3の矩形、対応する開始位置、作業コピー、未存在出力名。固定試験の値や完成解を教材から補わない。
- text/number以外、異なる矩形形状、空白、真偽値、日付、エラー、数式結果、任意オブジェクト、別PC/PAD版へ一般化しない。
"""


R8_SCOPE = """Issue #38 EX03 / 20260916-excel-r8 候補の現在の範囲
この節だけがr7後継の追加範囲である。r7以前の版、拒否原文、固定依頼、fixture、期待値、成功済みprobe、旧FAILを変更せず、旧版の生成・Run結果をr8へ継承しない。
1. r6実送信bundleの生バイトには、拒否理由で例示されたarrow/underscore/bracket前の説明用backslashは存在しない。したがって拒否理由だけでsource破損や内部原因を確定しない。
2. 別の監査では、r6実送信bundleとr7教材が固定EX03の4 workbook path、4 sheet name、2 source rectangle、12 target mapping、guard/read/write/save/reopen/compareを完全に含み、教材と固定試験が結合していた。これは受入設計上の原因として確認したが、Copilot拒否の内部原因だったとは断定しない。
3. r8では固定依頼・期待値を変えず、教材だけを別path、別日本語sheet、別range、別target、別outputの同形例へ差し替えた。固定EX03の完全解と固有grader文字列は、r8の指示、現行追加節、support Robinへ入れない。
4. r8例はr7原文からdata slotだけを明示置換し、命令名、引数名、モード、DataTable添字、型の役割、依存順、分岐、block構造を保持した。逆置換でr7原文へ戻ることを機械確認した。
5. 別例の完全Robinを専用PAD 2.71.115.26224、日本語UI、Power Fx OFFの空Mainへ1回貼付け、110 action・45 variableとして保存し、1回再コピーした。候補と再コピーはraw SHAを含め完全一致し、Designer errorは観測されなかった。
6. 再コピーRobin中のRunScript payloadは、観測済みRobin escapeだけを復号するとsupportの独立例PowerShellと最終LFを除き完全一致する。説明用の再escape、逆escape、手修正は行わない。
7. r8教材例は貼付け・保存・再コピーまでの構文証拠であり、例の実行、通常M365 Copilot生成、EX03 Run1/Run2、成果物照合、既存出力guard実機経路の証拠ではない。原本・対象外全cell・formula・effective format・558差分FAILの独立検査を維持し、完成・実行済み・受入済みと書かない。
"""


def audit_section(sent_bundle: str, refusal: str, recopy: str, script: str) -> str:
    action = extract_action(recopy)
    decoded = decode_robin_string(action_payload(action))
    if normalized(decoded) != normalized(script):
        raise ValueError("Independent Robin payload does not decode to support script")
    return f"""r8 教材独立性・source-chain機械照合
- r6実送信bundle: {relative(INPUTS['actually_sent_r6_bundle'])} / SHA-256 {sha256(INPUTS['actually_sent_r6_bundle'])}
- r6拒否原文: {relative(INPUTS['r6_refusal'])} / SHA-256 {sha256(INPUTS['r6_refusal'])}
- r7独立性事前監査: {relative(INPUTS['independence_before'])} / SHA-256 {sha256(INPUTS['independence_before'])}
- r8 PAD投入前候補: {relative(INPUTS['candidate'])} / SHA-256 {sha256(INPUTS['candidate'])}
- r8 PAD保存・再コピー原文: {relative(INPUTS['pad_recopy'])} / SHA-256 {sha256(INPUTS['pad_recopy'])}
- r8内包PowerShell: {SCRIPT_SUPPORT.as_posix()} / SHA-256 {sha256(INPUTS['candidate_script'])}
- 実送信bundle内の `=\\>` / `\\_` / `\\[` 件数: {sent_bundle.count('=\\>')} / {sent_bundle.count('\\_')} / {sent_bundle.count('\\[')}
- 実送信bundle内の raw `=>` / `_ValueTypeMatch` / `Data1[0][0]` 件数: {sent_bundle.count('=>')} / {sent_bundle.count('_ValueTypeMatch')} / {sent_bundle.count('Data1[0][0]')}
- 拒否原文は説明用escapeを理由に挙げるが、実送信bundleの上記byte監査はその仮説を支持しない。Copilot内部の拒否原因は未確定。
- 一方、実送信bundleに固定試験の完全flowが含まれた教材/test結合は確認済み。r8は教材だけを独立例へ交換し、この設計不備を除去する。拒否原因の確定とは別の判定である。
- r8候補とPAD再コピー: raw SHAを含め完全一致。110 action、45 variable、paste 1、save 1、recopy 1、execution 0。
- PAD再コピーRunScriptを観測済みescapeだけ復号した本文とsupport: 最終LFを除き完全一致。
- r8独立例のRobinに固定EX03のcomplete identifiers、固有grader文字列、expected text 100 percentは0件。
- Copilot送信0、EX03統合Run 0、GitHub書込み0。

内包PowerShell完全原文（比較用。実行時は06のRobin内に内包し、外部fileとしてloadしない）
{script.rstrip(chr(13) + chr(10))}
"""


def build(destination: Path) -> None:
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Candidate exists; sealed versions must not be overwritten")

    actual = {name: sha256(path) for name, path in INPUTS.items()}
    if actual != EXPECTED:
        raise ValueError(f"Protected r7/capture/fixed input hash mismatch: {actual}")

    manifest = json.loads(INPUTS["r7_manifest"].read_bytes())
    if manifest["version"] != "20260916-excel-r7":
        raise ValueError("Unexpected base candidate")
    for record in manifest["source_files"]:
        if sha256(BASE / record["path"]) != record["sha256"]:
            raise ValueError(f"r7 source mismatch: {record['path']}")
    if manifest["instruction_sha256"] != actual["r7_instruction"]:
        raise ValueError("r7 instruction manifest mismatch")
    if manifest["bundle_sha256"] != actual["r7_bundle"]:
        raise ValueError("r7 bundle manifest mismatch")

    independence = json.loads(INPUTS["independence_before"].read_bytes())
    preflight = json.loads(INPUTS["preflight"].read_bytes())
    pad_capture = json.loads(INPUTS["pad_capture"].read_bytes())
    if independence["decision"] != "FAIL_R7_CONTAINS_FIXED_EX03_COMPLETE_ANSWER":
        raise ValueError("r7 independence failure is not preserved")
    if not all(preflight["mechanical_checks"].values()):
        raise ValueError("Independent-source preflight is not fully passing")
    if pad_capture["result"] != "PASS_PAD_DESIGNER_SAVE_RECOPY_INDEPENDENT_SOURCE_NO_EXECUTION":
        raise ValueError("Dedicated PAD save/re-copy result changed")
    if any(
        pad_capture["scope"][key]
        for key in ["executed", "copilot_send", "integrated_ex03_run", "github_write"]
    ):
        raise ValueError("PAD capture exceeded the authorized non-execution scope")

    sent_bundle = text(INPUTS["actually_sent_r6_bundle"])
    refusal = text(INPUTS["r6_refusal"])
    candidate = text(INPUTS["candidate"])
    recopy = text(INPUTS["pad_recopy"])
    candidate_action = text(INPUTS["candidate_action"])
    script = text(INPUTS["candidate_script"])
    if any(token in sent_bundle for token in ["=\\>", "\\_", "\\["]):
        raise ValueError("Actually sent r6 bundle now contains a claimed escape artifact")
    if not all(token in refusal for token in ["=\\>", "\\_", "DataTable添字"]):
        raise ValueError("Refusal rationale no longer contains the audited claims")
    if not all(term in sent_bundle for term in FIXED_COMPLETION_TERMS):
        raise ValueError("Actually sent r6 bundle no longer contains the fixed complete answer")
    if normalized(candidate) != normalized(recopy) or candidate.encode("utf-8") != recopy.encode("utf-8"):
        raise ValueError("PAD re-copy differs from the prepared independent source")
    if normalized(extract_action(recopy)) != normalized(candidate_action):
        raise ValueError("PAD-recopied RunScript action differs from the prepared action")
    if normalized(decode_robin_string(action_payload(extract_action(recopy)))) != normalized(script):
        raise ValueError("PAD-recopied RunScript payload differs from the prepared script")
    if any(term in candidate for term in FIXED_COMPLETION_TERMS + UNIQUE_GRADER_STRINGS + ["100%"]):
        raise ValueError("Fixed EX03 answer or grader data leaked into the independent Robin")
    if EXAMPLE_ROOT not in candidate:
        raise ValueError("Independent example root is missing")
    if candidate.count("Scripting.RunPowershellScript.RunScript") != 1:
        raise ValueError("Independent example RunScript count changed")
    if candidate.count("Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource") != 5:
        raise ValueError("Independent example numeric-write count changed")
    if candidate.count("_ValueTypeMatch TO SourceCellJson = SavedCellJson") != 12:
        raise ValueError("Independent example JSON-compare count changed")

    (destination / "knowledge").mkdir(parents=True)
    (destination / "support").mkdir(parents=True)
    shutil.copyfile(INPUTS["candidate_script"], destination / SCRIPT_SUPPORT)
    shutil.copyfile(INPUTS["pad_recopy"], destination / ROBIN_SUPPORT)

    mapping = example_mapping()
    audit = audit_section(sent_bundle, refusal, recopy, script)
    for record in manifest["source_files"]:
        source = BASE / record["path"]
        name = Path(record["path"]).name
        content = text(source)
        if name.startswith(("PAD-Robin-00-", "PAD-Robin-04-", "PAD-Robin-06-")):
            if R7_MARKER not in content:
                raise ValueError(f"r7 replacement marker missing: {name}")
            content = content.split(R7_MARKER, 1)[0].rstrip("\r\n") + "\n\n" + R8_SCOPE + mapping
            if name.startswith("PAD-Robin-04-"):
                content += "\n" + audit
            if name.startswith("PAD-Robin-06-"):
                content += "\nEX03 r8 PAD保存・再コピー独立教材原文（別条件例。未実行・未受入）\n"
                content += f"source: {ROBIN_SUPPORT.as_posix()} / SHA-256 {sha256(INPUTS['pad_recopy'])}\n"
                content += "この見出しより後のRobinだけを逐語使用し、依頼のdata slotだけを同じ確認範囲内で一貫置換する。固定試験の値や完成解を教材から補わない。\n"
                content += recopy.rstrip("\r\n") + "\n"
        (destination / record["path"]).write_bytes(content.encode("utf-8"))

    original_instruction = text(INPUTS["r7_instruction"])
    if R7_INSTRUCTION_MARKER not in original_instruction:
        raise ValueError("r7 instruction replacement marker missing")
    prefix = original_instruction.split(R7_INSTRUCTION_MARKER, 1)[0]
    instructions = prefix + """【Excel値転記・20260916-excel-r8候補】
標準入力は同版の指示全文＋bundle実添付です。r6拒否、r7独立性FAIL、固定依頼・期待値、旧版、成功済みprobe、558差分FAILを保持し、いずれもr8の実行受入へ継承しません。00/04/06末尾の「EX03 / 20260916-excel-r8」だけを後継追加範囲として参照します。
r6拒否が挙げた説明用escapeは実送信bundleのbyte列に存在しません。拒否理由だけでsource破損や内部原因を確定せず、04の拒否原文・実送信bundle・PAD原文の三者照合を使います。
実送信r6 bundleとr7教材には固定試験の完全flowが入り、教材と試験条件が結合していました。これは受入設計上の問題として確認済みですが、拒否の内部原因だったとは断定しません。r8は固定依頼・期待値を変えず、教材だけを別条件の同形例へ交換します。
06のr8完全原文は、別path・別日本語sheet・別range・別target・別outputの教材例を専用PAD 2.71.115.26224、日本語UI、Power Fx OFFの空Mainへ貼付け、110 action・45 variableとして保存し、再コピーした原文です。投入前候補とraw SHAを含め完全一致し、RunScript payloadは観測済みescapeだけを復号するとsupportの内包PowerShellと一致します。
固定するのは命令名、引数名、mode、DataTable添字、text/numberの役割、依存順、分岐・block構造、1 RunScript、5 numeric write、12 JSON compareです。利用者依頼から置換するのは、同じ確認範囲内のpath、存在するsheet名、3x2と2x3のrectangle、対応するtarget start、work copy、未存在outputです。定義・参照・script内guardを一貫して置換します。
固定EX03の具体的なpath、sheet、target cell、grader値、完成Robinを教材から補いません。依頼本文に示されたdataだけでr8例のdata slotを置換し、教材例の名前や位置へ戻しません。text/number以外、異なるshape、空白、真偽値、日付、error、formula result、任意object、別PC/PAD版へ一般化しません。
入力と原本はReadOnlyで開き、検証者が準備したwork copyだけを編集します。既存output時はwrite経路へ入らず、文字列7位置は同じRunのDataTableからJSON化して内包scriptで各1回、数値5位置は通常WriteCellで各1回だけ書きます。固定値や1 cellだけの事後修正を入れません。
内包scriptの絶対FullName 1冊、許可target、source文字列、非formula、元NumberFormat、一時@、Value2、finally復元、直後の値・System.String・元format・prefix空・formulaなしの検査を保持します。失敗時はSaveAs・完了状態へ進まず、外部ps1、network、delete、overwrite、権限・security・Excel設定変更を要求しません。
SaveAs後はcloseしてReadOnly再開し、2矩形をTypedValuesで再取得して12位置を同じprobe keyで個別JSON比較します。原本・対象外全cell・formula・effective formatは独立検査を維持し、書式・寸法558差分FAILを隠しません。
回答は利用者依頼の全工程を一つのtext code blockへ入れます。r8はPAD保存・再コピー済みの独立教材sourceであって、通常M365 Copilot生成、教材例の実行、無修正EX03 PAD Run1/Run2、成果物照合、既存output guard実機経路は未実施です。完成・実行済み・受入済みと表示しません。
"""
    (destination / "agent-instructions.txt").write_text(
        instructions, encoding="utf-8", newline="\n"
    )
    instruction_utf16 = len(instructions.encode("utf-16-le")) // 2
    if instruction_utf16 > 8000:
        raise ValueError(f"Instruction exceeds limit: {instruction_utf16}")
    if any(term in instructions for term in FIXED_COMPLETION_TERMS + UNIQUE_GRADER_STRINGS + ["100%"]):
        raise ValueError("Fixed answer leaked into r8 instruction")

    subprocess.run(
        [
            "pwsh", "-NoProfile", "-File", str(ROOT / "tools/Build-KnowledgeBundle.ps1"),
            "-Root", str(destination), "-KnowledgeDirectory", "knowledge",
            "-OutputPath", "knowledge/PAD-Robin-Knowledge-Bundle.txt",
        ],
        check=True,
    )

    bundle_path = destination / manifest["bundle_path"]
    current_bundle = text(bundle_path)
    if any(term in current_bundle for term in FIXED_COMPLETION_TERMS + UNIQUE_GRADER_STRINGS):
        raise ValueError("Fixed EX03 complete answer or unique grader data leaked into r8 bundle")
    if normalized(recopy) not in normalized(current_bundle):
        raise ValueError("Independent PAD re-copy is missing from r8 bundle")

    evidence_inputs = dict(manifest.get("evidence_inputs", {}))
    for path in INPUTS.values():
        evidence_inputs[relative(path)] = sha256(path)

    support_files = []
    for support_path, runtime in [
        (SCRIPT_SUPPORT, "embedded_in_robin_not_loaded_from_disk"),
        (ROBIN_SUPPORT, "authoritative_independent_teaching_source_not_executed"),
    ]:
        path = destination / support_path
        support_files.append({
            "path": support_path.as_posix(),
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
            "runtime": runtime,
        })

    manifest.update(
        version=VERSION,
        status="FROZEN_CANDIDATE_EX03_INDEPENDENT_TEACHING_PAD_RECOPIED_NOT_COPILOT_OR_RUNTIME_ACCEPTED",
        inherits_live_acceptance=False,
        base_candidate="20260916-excel-r7",
        base_commit=BASE_COMMIT,
        instruction_sha256=sha256(destination / "agent-instructions.txt"),
        instruction_utf16=instruction_utf16,
        bundle_sha256=sha256(bundle_path),
        evidence_inputs=evidence_inputs,
        builder="tools/Build-Issue38Ex03CandidateR8.py",
        support_files=support_files,
    )
    for record in manifest["source_files"]:
        path = destination / record["path"]
        record.update(sha256=sha256(path), bytes=path.stat().st_size)
    manifest["evidence"].update(
        copilot="R6_REFUSAL_PRESERVED_R8_NOT_SENT",
        pad="R8_INDEPENDENT_SOURCE_PASTE_SAVE_RECOPY_ONLY_NO_EXECUTION",
        teaching_test_independence="PASS_R8_FIXED_EX03_COMPLETE_ANSWER_ABSENT_FROM_CURRENT_INSTRUCTION_BUNDLE_AND_SUPPORT",
        prior_refusal_internal_cause="UNRESOLVED_REFUSAL_ESCAPE_CLAIM_NOT_SUPPORTED_BY_ACTUAL_SENT_BUNDLE_BYTES",
        confirmed_package_issue="R6_R7_COMPLETE_FIXED_ANSWER_COUPLING_REMOVED_FROM_R8_TEACHING_SOURCE",
        source_chain="R6_REFUSAL_AND_SENT_BUNDLE_AUDITED_R8_PAD_RECOPY_MECHANICALLY_MATCHED",
        source_candidate_sha256=sha256(INPUTS["candidate"]),
        source_pad_recopy_sha256=sha256(INPUTS["pad_recopy"]),
        source_exact_bytes=True,
        source_lf_normalized_exact=True,
        source_candidate_crlf_count=110,
        source_candidate_lf_only_count=87,
        source_recopy_crlf_count=110,
        source_recopy_lf_only_count=87,
        source_action_decodes_to_script=True,
        actual_sent_bundle_claimed_escape_counts={"=\\>": 0, "\\_": 0, "\\[": 0},
        actual_sent_bundle_raw_token_counts={
            "=>": sent_bundle.count("=>"),
            "_ValueTypeMatch": sent_bundle.count("_ValueTypeMatch"),
            "Data1[0][0]": sent_bundle.count("Data1[0][0]"),
        },
        fixed_request_spec_expected_hashes_preserved=True,
        fixed_completion_terms_absent_from_independent_source=True,
        unique_grader_strings_absent_from_independent_source=True,
        expected_string_100_percent_absent_from_independent_source=True,
        existing_output_guard="STATIC_ONLY_NOT_LIVE_TESTED",
        candidate_adaptation="INDEPENDENT_TEACHING_SOURCE_PAD_SAVED_RECOPY_NOT_RUNTIME_ACCEPTED",
        candidate_script_sha256=sha256(INPUTS["candidate_script"]),
        candidate_robin_sha256=sha256(INPUTS["pad_recopy"]),
    )
    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(json.dumps({
        "version": VERSION,
        "instruction_utf16": instruction_utf16,
        "instruction_sha256": manifest["instruction_sha256"],
        "bundle_sha256": manifest["bundle_sha256"],
        "manifest_sha256": sha256(destination / "manifest.json"),
        "pad_recopy_sha256": manifest["evidence"]["source_pad_recopy_sha256"],
        "independence": manifest["evidence"]["teaching_test_independence"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=ROOT / "copilot/versions" / VERSION
    )
    build(parser.parse_args().output)
