#!/usr/bin/env python3
"""Freeze the EX03 r7 successor from the exact PAD-saved/re-copied Robin.

This builder does not send to Copilot and does not execute EX03.  It preserves
the sealed r6 candidate and its refusal, then makes the dedicated PAD Designer
save/re-copy source authoritative for generation of the same fixed EX03 only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "copilot/versions/20260916-excel-r6"
VERSION = "20260916-excel-r7"
BASE_COMMIT = "7470c7cadc147f31d1803034fa9f4ab90a6b32c8"
CAPTURE = ROOT / "catalog/acceptance/issue38/probes/ex03-r7-robin-source"
R6_CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r6-G1"
R6_MARKER = "Issue #38 EX03 / 20260916-excel-r6 候補の現在の範囲"
R6_INSTRUCTION_MARKER = "【Excel値転記・20260916-excel-r6候補】"
SCRIPT_SUPPORT = Path("support/EX03-TextWrite-FormatSandwich.ps1.txt")
ROBIN_SUPPORT = Path("support/EX03-R7-PAD-Recopy.robin")

INPUTS = {
    "r6_manifest": BASE / "manifest.json",
    "r6_bundle": BASE / "knowledge/PAD-Robin-Knowledge-Bundle.txt",
    "r6_instruction": BASE / "agent-instructions.txt",
    "r6_script": BASE / SCRIPT_SUPPORT,
    "submitted_body": R6_CYCLE / "submitted-body.txt",
    "refusal": R6_CYCLE / "response-rendered.txt",
    "live_send": R6_CYCLE / "live-send.json",
    "preflight": CAPTURE / "preflight.json",
    "pad_capture": CAPTURE / "pad-capture.json",
    "candidate": CAPTURE / "candidate-full.robin",
    "candidate_action": CAPTURE / "candidate-action.robin",
    "pad_recopy": CAPTURE / "pad-recopy-full.robin",
}

EXPECTED = {
    "r6_manifest": "207dfa10f34f0eb7c09a3a39ecfb25c24f870fb5e639b87a0fbce0683cbc9f89",
    "r6_bundle": "9c566e7f85a431f1869302c6a40985e2f81237f17ac4fbbdc9a73e62a646b580",
    "r6_instruction": "1211ee45f80427a474d15d92dbfda3b7c90d2a78b9b7520aadb76f5f22c82fe4",
    "r6_script": "d0a5df36516fcf4e27f6d789300ee5a03789aba8176571b1ab86fe84f15fba1a",
    "submitted_body": "a9051689e227e74a904c20fb860f89935b5c393164629869bebbcc923e93903e",
    "refusal": "7c6f30590b3ee7905038f142c1974d7639c4579c44a6f445ae0a9ea22f58b342",
    "live_send": "c9f00f1a9a4ab48fd1c11f86438fd8c903a3af2a52f25e8e4d25df81a565b9e5",
    "preflight": "c3ee76b7e8a9950157a0a27dc212bcfd4daf85904ca9b1a9205c7a204ba333db",
    "pad_capture": "7429b5dc228325ff91a95fff2d17d3305e6b330b50845a9089ec2081f3e2cc18",
    "candidate": "1f6ea14ea59242d7351d01ef75cd9571eb90676ab3845ffd2a842f01d84c771b",
    "candidate_action": "1356bf8bb8021700fc75cd88edcb5b58a94cbf99c96a141e9008f62a68ced024",
    "pad_recopy": "529d66dd598c395c6313a6f6d6b44c80049effb79de96b675a37f7dc99596d89",
}

ACTION_PREFIX = "Scripting.RunPowershellScript.RunScript Script: $'''"
ACTION_SUFFIX = "''' ScriptOutput=> PowershellOutput"


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
    action = normalized_flow[start:end]
    lines = action.split("\n")
    return "\n".join([lines[0], *(line[4:] for line in lines[1:])])


def action_payload(action: str) -> str:
    if not action.startswith(ACTION_PREFIX) or not action.endswith(ACTION_SUFFIX):
        raise ValueError("PowerShell action wrapper differs from the captured form")
    return action[len(ACTION_PREFIX) : -len(ACTION_SUFFIX)]


def fixed_mapping() -> str:
    return """固定EX03の書込み対応（この12位置と文字列/数値だけに限定）:
- Data1[0][0] -> 集計先!F7 (text) / Data1[0][1] -> 集計先!G7 (number)
- Data1[1][0] -> 集計先!F8 (text) / Data1[1][1] -> 集計先!G8 (number)
- Data1[2][0] -> 集計先!F9 (text) / Data1[2][1] -> 集計先!G9 (number)
- Data2[0][0] -> 追記先!D5 (text) / Data2[0][1] -> 追記先!E5 (number) / Data2[0][2] -> 追記先!F5 (text)
- Data2[1][0] -> 追記先!D6 (text) / Data2[1][1] -> 追記先!E6 (number) / Data2[1][2] -> 追記先!F6 (text)
値は同じRunのDataTableから取得する。固定値をコードへ埋めず、F6等の事後修正をしない。文字列7位置はJSON primitiveを確認して内包スクリプトで各1回、数値5位置は通常WriteCellで各1回だけ書く。日付、空白、真偽値、エラー、数式結果、任意オブジェクト、別fixture、別PC/PAD版へ一般化しない。
"""


R7_SCOPE = """Issue #38 EX03 / 20260916-excel-r7 候補の現在の範囲
この節だけがr6拒否後の後継追加範囲である。r6、拒否原文、固定依頼、fixture、期待値、成功済みprobe、旧FAILを変更せず、旧版の生成・Run結果をr7へ継承しない。
1. 固定EX03の入力2矩形、対象12セル、未存在出力ガード、保存→クローズ→読取り専用再開、12個のJSON型照合を保持する。入力とひな形原本を編集せず、検証者が準備した作業コピーから未存在出力へだけSaveAsする。
2. r6拒否が例示した `=\\>`、`\\_`、`\\[` は実送信bundleのバイト列には0件で、rawの `=>`、`_ValueTypeMatch`、`Data1[0][0]` は存在する。拒否説明だけでsource破損と確定しない。
3. r6統合候補と同じ完全Robinを専用PAD 2.71.115.26224、日本語UI、Power Fx OFFの空Mainへ1回貼付け、110アクション・45変数として保存し、1回再コピーした。Designerエラーは観測されず、候補と再コピーはLF正規化後に完全一致した。PADがトップレベル110区切りをCRLF化し、内包PowerShellの87 LFは保持した。
4. 06のPAD再コピー完全原文を、同じ固定EX03に対する生成の権威ソースとして逐語使用する。これは貼付け・保存・再コピーまでの構文証拠であり、実行・Copilot生成・EX03受入の証拠ではない。未実行状態を実行済みと表示しないための区分であって、この固定原文を出力しない理由にはしない。
5. 再コピー原文中のRunScript payloadは、観測済みRobin escape（`\\\\`、`\\'`、`\\\"`）だけを復号するとsupportの内包PowerShellと最終LFを除き完全一致する。説明用の逆エスケープや再構成を行わず、06の原文をそのまま使う。
6. 内包スクリプトは作業コピーの絶対FullName一致が1冊、固定7 target、source JSONが文字列、対象が非数式であることを検査し、元NumberFormatを取得して一時@→Value2書込み→finally復元し、値・System.String・元書式・prefix空・数式なしをSaveAs前に検査する。失敗時は後続へ進まない。
7. 既存出力ガードの実機経路、r7の通常M365 Copilot生成、無修正PAD実行、Run1成果物保全後のRun2、独立照合は未実施である。原本・対象外全セル・数式・実効書式・558差分FAILの検査を維持し、完成・実行済み・受入済みと書かない。
"""


def audit_section(bundle: str, refusal: str, recopy: str, script: str) -> str:
    action = extract_action(recopy)
    decoded = decode_robin_string(action_payload(action))
    assert normalized(decoded) == normalized(script)
    return f"""r7 source-chain機械照合
- r6実送信bundle: {relative(INPUTS['r6_bundle'])} / SHA-256 {sha256(INPUTS['r6_bundle'])}
- r6拒否原文: {relative(INPUTS['refusal'])} / SHA-256 {sha256(INPUTS['refusal'])}
- PAD投入前候補: {relative(INPUTS['candidate'])} / SHA-256 {sha256(INPUTS['candidate'])}
- PAD保存・再コピー原文: {relative(INPUTS['pad_recopy'])} / SHA-256 {sha256(INPUTS['pad_recopy'])}
- 内包PowerShell: {SCRIPT_SUPPORT.as_posix()} / SHA-256 {sha256(INPUTS['r6_script'])}
- 実送信bundle内の `=\\>` / `\\_` / `\\[` 件数: {bundle.count('=\\>')} / {bundle.count('\\_')} / {bundle.count('\\[')}
- 実送信bundle内の raw `=>` / `_ValueTypeMatch` / `Data1[0][0]` 件数: {bundle.count('=>')} / {bundle.count('_ValueTypeMatch')} / {bundle.count('Data1[0][0]')}
- 拒否原文は技術資料用エスケープを理由に挙げたが、上の実bundle監査はその仮説を支持しない。原因確定は拒否説明だけに依存しない。
- 候補とPAD再コピー: raw SHAは異なるがLF正規化後完全一致。差はCRLF 110件と内包script LF 87件の区切り表現だけ。
- PAD再コピーRunScriptを観測済みescapeだけ復号した本文とsupport: 最終LFを除き完全一致。
- PAD専用確認は貼付け・保存・再コピーのみ。実行0、Copilot送信0、EX03統合Run 0。

内包PowerShell完全原文（比較用。実行時は06のRobin内に内包し、外部ファイルとしてロードしない）
{script.rstrip(chr(13) + chr(10))}
"""


def build(destination: Path) -> None:
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Candidate exists; sealed versions must not be overwritten")

    actual = {name: sha256(path) for name, path in INPUTS.items()}
    if actual != EXPECTED:
        raise ValueError(f"Protected r6/capture input hash mismatch: {actual}")

    manifest = json.loads(INPUTS["r6_manifest"].read_bytes())
    for record in manifest["source_files"]:
        if sha256(BASE / record["path"]) != record["sha256"]:
            raise ValueError(f"r6 source mismatch: {record['path']}")
    if manifest["instruction_sha256"] != actual["r6_instruction"]:
        raise ValueError("r6 instruction manifest mismatch")
    if manifest["bundle_sha256"] != actual["r6_bundle"]:
        raise ValueError("r6 bundle manifest mismatch")

    live_send = json.loads(INPUTS["live_send"].read_bytes())
    preflight = json.loads(INPUTS["preflight"].read_bytes())
    pad_capture = json.loads(INPUTS["pad_capture"].read_bytes())
    if not live_send["observed_result"]["refusal"]:
        raise ValueError("r6 refusal record changed")
    if pad_capture["result"] != "PASS_PAD_DESIGNER_SAVE_RECOPY_NO_EXECUTION":
        raise ValueError("PAD save/re-copy evidence is not the fixed non-execution result")
    if any(pad_capture["scope"][key] for key in ["executed", "copilot_send", "integrated_ex03_run", "github_write"]):
        raise ValueError("PAD capture exceeded the authorized non-execution scope")
    if not all(preflight["mechanical_checks"].values()):
        raise ValueError("Preflight source-chain check is not fully passing")

    bundle = text(INPUTS["r6_bundle"])
    refusal = text(INPUTS["refusal"])
    candidate = text(INPUTS["candidate"])
    recopy = text(INPUTS["pad_recopy"])
    script = text(INPUTS["r6_script"])
    if normalized(candidate) != normalized(recopy):
        raise ValueError("PAD re-copy differs outside line-ending normalization")
    if any(token in bundle for token in ["=\\>", "\\_", "\\["]):
        raise ValueError("Actual sent bundle unexpectedly contains a claimed escape artifact")
    if not all(token in bundle for token in ["=>", "_ValueTypeMatch", "Data1[0][0]"]):
        raise ValueError("Actual sent bundle is missing required raw Robin tokens")
    if not all(token in refusal for token in ["=\\>", "\\_", "DataTable添字"]):
        raise ValueError("Refusal rationale no longer contains the audited escape claims")
    if normalized(extract_action(recopy)) != normalized(text(INPUTS["candidate_action"])):
        raise ValueError("PAD-recopied RunScript action differs from the prepared action")

    (destination / "knowledge").mkdir(parents=True)
    (destination / "support").mkdir(parents=True)
    shutil.copyfile(INPUTS["r6_script"], destination / SCRIPT_SUPPORT)
    shutil.copyfile(INPUTS["pad_recopy"], destination / ROBIN_SUPPORT)

    mapping = fixed_mapping()
    audit = audit_section(bundle, refusal, recopy, script)
    for record in manifest["source_files"]:
        source = BASE / record["path"]
        name = Path(record["path"]).name
        content = text(source)
        if name.startswith(("PAD-Robin-00-", "PAD-Robin-04-", "PAD-Robin-06-")):
            if R6_MARKER not in content:
                raise ValueError(f"r6 replacement marker missing: {name}")
            content = content.split(R6_MARKER, 1)[0].rstrip("\r\n") + "\n\n" + R7_SCOPE + mapping
            if name.startswith("PAD-Robin-04-"):
                content += "\n" + audit
            if name.startswith("PAD-Robin-06-"):
                content += "\nEX03 r7 PAD保存・再コピー完全原文（固定EX03生成用。未実行・未受入）\n"
                content += f"source: {ROBIN_SUPPORT.as_posix()} / SHA-256 {sha256(INPUTS['pad_recopy'])}\n"
                content += "この見出しより後のRobinだけを逐語使用し、説明用の再エスケープ・逆エスケープ・再構成をしない。\n"
                content += recopy.rstrip("\r\n") + "\n"
        (destination / record["path"]).write_bytes(content.encode("utf-8"))

    original_instruction = text(INPUTS["r6_instruction"])
    if R6_INSTRUCTION_MARKER not in original_instruction:
        raise ValueError("r6 instruction replacement marker missing")
    prefix = original_instruction.split(R6_INSTRUCTION_MARKER, 1)[0]
    instructions = prefix + """【Excel値転記・20260916-excel-r7候補】
標準入力は同版の指示全文＋bundle実添付です。r6拒否、固定依頼・期待値、旧版、成功済みprobe、558差分FAILを保持し、いずれもr7の実行受入へ継承しません。00/04/06末尾の「EX03 / 20260916-excel-r7」だけを後継追加範囲として参照します。
固定EX03の入力・ひな形・作業コピー・未存在出力、2矩形、12対象位置、出力存在ガード、保存→閉じる→読取り専用再開、12個のJSON型比較を変更しません。入力と原本はReadOnlyで開き、作業コピーだけを編集し、既存出力時は書込み経路へ入りません。
r6拒否は資料用エスケープを理由に挙げましたが、実送信bundleのバイト監査では `=\\>`、`\\_`、`\\[` は0件です。拒否説明だけからsource破損を確定せず、04の三者照合を使います。
06のr7完全原文は、r6統合候補を専用PAD 2.71.115.26224、日本語UI、Power Fx OFFの空Mainへ貼付け、110アクション・45変数として保存し、再コピーした原文です。候補とはLF正規化後完全一致し、RunScript payloadは観測済みescapeだけを復号するとsupportの内包PowerShellと一致します。
同じ固定EX03では06のPAD再コピー完全原文を生成元として逐語出力します。PADで実行していない状態は実行済みと表示しないための区分であり、この固定原文の出力を拒む理由にはしません。Robinの `=>`、アンダースコア、角括弧、引用符、バックスラッシュ、改行を説明用に再エスケープ・逆エスケープ・再構成しません。
文字列7 source位置は同じRunのDataTableからJSON化し、内包RunScriptで集計先F7/F8/F9、追記先D5/D6/F5/F6へ各1回だけ書きます。数値5位置は集計先G7/G8/G9、追記先E5/E6へ通常WriteCellで各1回だけ書きます。固定値やF6だけの事後修正を入れません。
内包scriptの絶対FullName 1冊、固定target、source文字列、非数式、元NumberFormat、一時@、Value2、finally復元、直後の値・System.String・元書式・prefix空・数式なしの検査を保持します。失敗時はSaveAs・完了状態へ進まず、外部ps1、ネットワーク、削除、上書き、権限・セキュリティ・Excel設定変更を要求しません。
固定EX03の文字列/数値以外、任意文字列、空白、真偽値、日付、エラー、数式結果、オブジェクト、別fixture、他PC/PAD版へ一般化しません。SaveAs後は閉じてReadOnly再開し、2矩形をTypedValuesで再取得して12位置を同じprobeキーで個別JSON比較します。固定期待値を回答へ埋めず、原本・対象外全セル・数式・実効書式は独立検査を維持します。
回答は固定依頼の全工程を一つのtextコードブロックへ入れます。r7はPAD保存・再コピー済み生成ソースであって、通常M365 Copilot生成、無修正PAD Run1/Run2、成果物照合、既存出力ガード実機経路は未実施です。完成・実行済み・受入済みと表示しません。
"""
    (destination / "agent-instructions.txt").write_text(
        instructions, encoding="utf-8", newline="\n"
    )
    instruction_utf16 = len(instructions.encode("utf-16-le")) // 2
    if instruction_utf16 > 8000:
        raise ValueError(f"Instruction exceeds limit: {instruction_utf16}")

    subprocess.run(
        [
            "pwsh", "-NoProfile", "-File", str(ROOT / "tools/Build-KnowledgeBundle.ps1"),
            "-Root", str(destination), "-KnowledgeDirectory", "knowledge",
            "-OutputPath", "knowledge/PAD-Robin-Knowledge-Bundle.txt",
        ],
        check=True,
    )

    evidence_inputs = dict(manifest.get("evidence_inputs", {}))
    for path in [
        INPUTS["submitted_body"], INPUTS["refusal"], INPUTS["live_send"],
        INPUTS["preflight"], INPUTS["pad_capture"], INPUTS["candidate"],
        INPUTS["candidate_action"], INPUTS["pad_recopy"],
    ]:
        evidence_inputs[relative(path)] = sha256(path)

    support_files = []
    for support_path, runtime in [
        (SCRIPT_SUPPORT, "embedded_in_robin_not_loaded_from_disk"),
        (ROBIN_SUPPORT, "authoritative_fixed_ex03_generation_source_not_executed"),
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
        status="FROZEN_CANDIDATE_EX03_PAD_RECOPIED_SOURCE_NOT_COPILOT_OR_RUNTIME_ACCEPTED",
        inherits_live_acceptance=False,
        base_candidate="20260916-excel-r6",
        base_commit=BASE_COMMIT,
        instruction_sha256=sha256(destination / "agent-instructions.txt"),
        instruction_utf16=instruction_utf16,
        bundle_sha256=sha256(destination / manifest["bundle_path"]),
        evidence_inputs=evidence_inputs,
        builder="tools/Build-Issue38Ex03CandidateR7.py",
        support_files=support_files,
    )
    for record in manifest["source_files"]:
        path = destination / record["path"]
        record.update(sha256=sha256(path), bytes=path.stat().st_size)
    manifest["evidence"].update(
        copilot="R6_REFUSAL_PRESERVED_R7_NOT_SENT",
        pad="R7_FIXED_SOURCE_PASTE_SAVE_RECOPY_ONLY_NO_EXECUTION",
        source_chain="R6_SENT_BUNDLE_TO_PAD_SAVED_RECOPY_MECHANICALLY_MATCHED",
        source_candidate_sha256=sha256(INPUTS["candidate"]),
        source_pad_recopy_sha256=sha256(INPUTS["pad_recopy"]),
        source_lf_normalized_exact=True,
        source_candidate_crlf_count=0,
        source_candidate_lf_only_count=197,
        source_recopy_crlf_count=110,
        source_recopy_lf_only_count=87,
        source_action_decodes_to_script=True,
        actual_sent_bundle_claimed_escape_counts={"=\\>": 0, "\\_": 0, "\\[": 0},
        actual_sent_bundle_raw_token_counts={
            "=>": bundle.count("=>"),
            "_ValueTypeMatch": bundle.count("_ValueTypeMatch"),
            "Data1[0][0]": bundle.count("Data1[0][0]"),
        },
        existing_output_guard="STATIC_ONLY_NOT_LIVE_TESTED",
        candidate_adaptation="FIXED_EX03_PAD_SAVED_RECOPY_SOURCE_NOT_RUNTIME_ACCEPTED",
        candidate_script_sha256=sha256(INPUTS["r6_script"]),
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
    }, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=ROOT / "copilot/versions" / VERSION
    )
    build(parser.parse_args().output)
