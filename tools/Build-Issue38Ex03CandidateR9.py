#!/usr/bin/env python3
"""Build the unsent EX03 r9 successor with an explicit escape-fidelity gate.

r9 keeps the fixed request and expectations unchanged and reuses the exact
independent r8 teaching Robin already accepted by PAD paste/save/re-copy.  It
adds only a generation-time contract that forbids new backslashes before
PowerShell square brackets and requires teaching-only labels to be replaced.
It does not send to Copilot, paste into PAD, or execute a flow.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "copilot/versions/20260916-excel-r8"
VERSION = "20260917-excel-r9"
BASE_COMMIT = "8e9dfc6baefba6d39d9b3d54d9adfceebdb12836"
AUDIT = ROOT / "catalog/acceptance/issue38/probes/ex03-r9-escape-fidelity"
R8_MARKER = "Issue #38 EX03 / 20260916-excel-r8 候補の現在の範囲"
R8_INSTRUCTION_MARKER = "【Excel値転記・20260916-excel-r8候補】"
SCRIPT_SUPPORT = Path("support/EX03-R9-Independent-FormatSandwich.ps1.txt")
ROBIN_SUPPORT = Path("support/EX03-R9-Independent-PAD-Recopy.robin")
FIDELITY_SUPPORT = Path("support/EX03-R9-Escape-Fidelity-Contract.txt")

INPUTS = {
    "r8_manifest": BASE / "manifest.json",
    "r8_instruction": BASE / "agent-instructions.txt",
    "r8_bundle": BASE / "knowledge/PAD-Robin-Knowledge-Bundle.txt",
    "r8_script": BASE / "support/EX03-R8-Independent-FormatSandwich.ps1.txt",
    "r8_robin": BASE / "support/EX03-R8-Independent-PAD-Recopy.robin",
    "escape_analysis": AUDIT / "analysis.json",
    "escape_report": AUDIT / "report.md",
    "r8_generated": ROOT / "catalog/acceptance/issue38/cycles/EX03-r8-G1/generated.robin",
    "r8_pad_recopy": ROOT / "catalog/acceptance/issue38/cycles/EX03-r8-G1/pad-recopy-before-run1.robin",
    "r8_acceptance": ROOT / "catalog/acceptance/issue38/cycles/EX03-r8-G1/acceptance-status.json",
    "fixed_request": ROOT / "catalog/acceptance/issue38/requests/EX03.txt",
    "fixed_spec": ROOT / "catalog/acceptance/issue38/spec.json",
    "grader_expected": ROOT / "catalog/acceptance/issue38/expected.json",
}

EXPECTED = {
    "r8_manifest": "9025c8869b84d27e4f39512ce157a114a5231041e641ae12ef36c061eae29d3e",
    "r8_instruction": "57f0cdb656e919f8fd83252a6adcd4d12788dac9bf6833db2f2e942eada23bcb",
    "r8_bundle": "164c99e59204efd863f4fe283e8f84ce2902ee760ab90e45cf7c5336631aaddb",
    "r8_script": "65b86b0e5be4ec2da30e57a6bd858e395d1103da2d05ab2e7607362772d1dfd9",
    "r8_robin": "6d9c23eabfacbcd65b1a18eabf5681805494e41171f94a9b01a28b24452815bb",
    "escape_analysis": "37009a713dd38f68bb142e80c465620fbd29152e445fc1fc72b0b744e7b3f13a",
    "escape_report": "b99d4fa156b780d04ce0af707bd6040545cfc7c0bddca44a9552323bd7f39247",
    "r8_generated": "711bd5b3a5eb1cba48f6872cd5aa8f718ab3534de4d0e069d5fd1eb7b9d1ed89",
    "r8_pad_recopy": "3340cd988d6ed76dc249edc833be33869c530d0b37ddf223807ac86eaef9329f",
    "r8_acceptance": "2f9a7dea1319496ff955bd19cf116fde67f90822021e20eca1c1016a6076a53d",
    "fixed_request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "fixed_spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "grader_expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
}

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
EXPECTED_TEXT = "100%"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def normalized(value: str) -> str:
    return value.replace("\r\n", "\n").rstrip("\n")


def example_mapping() -> str:
    return """r9独立教材例のデータ対応（固定する命令構造と、変更するdata slotを分離）:
- source-one.xlsx / 教材入力一 H3:I5 -> 教材出力一 J4:K6。各行の第1列はtext、第2列はnumber。
- source-two.xlsx / 教材入力二 C7:E8 -> 教材出力二 B10:D11。各行はtext, number, text。
- work-copy.xlsxだけを編集し、未存在のexample-result.xlsxへSaveAsする。
- 文字列7位置は同一RunのDataTableをJSON primitiveで確認して内包scriptから各1回、数値5位置は通常WriteCellから各1回だけ書く。保存・クローズ・ReadOnly再開後に12位置を個別JSON比較する。
- 固定するもの: 命令名、引数名、mode、DataTable添字、型の役割、依存順、分岐、1 RunScript、5 numeric writes、12 JSON comparisons、RunScript内のraw角括弧。
- 依頼から変更するもの: 同じ確認範囲内のpath、存在するsheet名、3x2と2x3のrectangle、対応する開始位置、work copy、未存在output、data slotに由来するerror label。
- text/number以外、異なるshape、空白、真偽値、日付、error、formula result、任意object、別PC/PAD版へ一般化しない。
"""


FIDELITY_CONTRACT = """EX03 r9 generation escape-fidelity contract
This contract applies to the one text code block returned from the independent PAD-recopied source.
1. A text code block is raw Robin text. Do not apply Markdown escaping to its contents.
2. Inside Scripting.RunPowershellScript.RunScript, PowerShell square brackets are literal raw `[` and `]` characters. Never prefix them with a backslash.
3. Preserve raw forms such as `[ordered]`, `[string]`, `[bool]`, `[void]`, `[Runtime.InteropServices.Marshal]`, `[IO.Path]`, `[StringComparison]`, `$matches[0]`, `$allowedTargets[$sheetName]`, and DataTable indexers. These examples constrain characters and do not supply request data.
4. Before emitting Robin, count the exact substrings backslash-open-bracket and backslash-close-bracket in the candidate. Both counts must be zero. Do not repair the text after output.
5. Replace every independent-example data slot consistently, including paths, sheet names, ranges, target cells, allowed-target entries, and teaching-only error labels. No teaching-only label may remain in an adapted candidate.
6. If any fidelity check fails, emit no Robin and report the failed check. A refusal/no-code result is not a runtime PASS.
7. This gate prevents the observed r8 G1 text drift only. It does not prove execution, types outside text/number, other shapes, another PAD version, or another PC.
"""


R9_SCOPE = """Issue #38 EX03 / 20260917-excel-r9 候補の現在の範囲
この節だけがr8後継の追加範囲である。r8以前の版、固定依頼・期待値、旧証跡、成功済みprobe、558差分FAILを変更せず、旧版の生成・Run結果をr9へ継承しない。
1. r8は教材と固定試験を分離し、別条件の完全RobinをPAD保存・再コピー済み原文として固定した。この独立性とsource SHAはr9でも保持する。
2. r8 G1の通常M365 Copilot 1回生成では、教材原文に0件だったbackslash-open-bracket / backslash-close-bracketが生成内に各53件入り、教材専用error labelも2件残った。
3. 無修正生成物は専用Power Fx OFF PADで110 action・45 variableとして保存できたが、再コピーでは角括弧前backslashが30行で二重化した。PADは生成済みのliteral backslashを保持したのであり、最初のbackslashを追加した場所ではない。固定停止条件によりRun1/Run2は0回である。
4. r9は完全Robinや内包scriptを変更せず、生成前検査だけを追加する。RunScript内のPowerShell角括弧はraw `[` / `]` とし、backslashを前置しない。候補中のbackslash-open-bracket / backslash-close-bracketを各0件と確認する。
5. path、sheet、range、target、allowed-targetと同様に、教材専用error labelもdata slotとして一貫置換する。教材名が1件でも残る候補は出力しない。
6. 検査に失敗した場合はRobinを出さず、失敗項目を説明する。後から手修正できる候補を出して成功扱いにしない。
7. r9は未送信候補であり、通常M365生成、PAD貼付け、Run1/Run2、成果物照合、既存output guard実機経路は未実施である。旧FAILと未確認範囲を維持する。
"""


R9_INSTRUCTIONS = """【Excel値転記・20260917-excel-r9候補】
標準入力は同版の指示全文＋bundle実添付です。r8 G1の生成・PAD再コピーFAIL、固定依頼・期待値、旧版、成功済みprobe、558差分FAILを保持し、r9の実行受入へ継承しません。00/04/06末尾の「EX03 / 20260917-excel-r9」だけを後継追加範囲として参照します。
r9はr8の別path・別sheet・別range・別target・別outputの独立教材Robinをbyte同一で再利用します。この原文は専用PAD 2.71.115.26224、日本語UI、Power Fx OFFで110 action・45 variableとして保存・再コピー済みですが、教材例の実行証拠ではありません。
r8 G1では通常M365生成がRunScript内のPowerShell角括弧へbackslashを追加し、PAD再コピーがそのliteral文字を二重化しました。textコードブロック内はraw Robinであり、Markdown向けに再escapeしません。`[ordered]`、`[string]`、`[bool]`、`[void]`、`[Runtime.InteropServices.Marshal]`、`[IO.Path]`、`[StringComparison]`、配列・DataTable添字の `[` と `]` を原文どおり保持し、前へbackslashを追加しません。
回答確定前にコード候補内のbackslash-open-bracketとbackslash-close-bracketを機械的に数え、どちらも0件であることを確認します。1件でもあればRobinを出さず、検査失敗を説明します。生成後の手修正や再表示で合格にしません。
固定するのは命令名、引数名、mode、DataTable添字、text/numberの役割、依存順、分岐・block構造、1 RunScript、5 numeric write、12 JSON compare、RunScript内のraw角括弧です。依頼から置換するのは同じ確認範囲内のpath、存在するsheet名、3x2と2x3のrectangle、対応するtarget start、work copy、未存在outputと、それらdata slotに由来するerror labelです。教材専用path・sheet・target・error labelを候補へ残しません。
固定試験の具体的なpath、sheet、target cell、grader値、完成Robinを教材から補いません。依頼本文のdataだけで独立例のdata slotを置換します。text/number以外、異なるshape、空白、真偽値、日付、error、formula result、任意object、別PC/PAD版へ一般化しません。
入力と原本はReadOnlyで開き、検証者が準備したwork copyだけを編集します。既存output時はwrite経路へ入らず、文字列7位置は同じRunのDataTableからJSON化して内包scriptで各1回、数値5位置は通常WriteCellで各1回だけ書きます。固定値や1 cellだけの事後修正を入れません。
内包scriptの絶対FullName 1冊、許可target、source文字列、非formula、元NumberFormat、一時@、Value2、finally復元、直後の値・System.String・元format・prefix空・formulaなしの検査を保持します。失敗時はSaveAs・完了状態へ進まず、外部ps1、network、delete、overwrite、権限・security・Excel設定変更を要求しません。
SaveAs後はcloseしてReadOnly再開し、2矩形をTypedValuesで再取得して12位置を個別JSON比較します。原本・対象外全cell・formula・effective formatは独立検査を維持し、書式・寸法558差分FAILを隠しません。
回答は利用者依頼の全工程を一つのtextコードブロックへ入れます。r9は独立教材と出力前fidelity gateの候補であり、通常M365 Copilot生成、無修正EX03 PAD Run1/Run2、成果物照合、既存output guard実機経路は未実施です。完成・実行済み・受入済みと表示しません。
"""


def audit_section(analysis: dict) -> str:
    generation = analysis["generation_comparison"]
    pad = analysis["pad_comparison"]
    return f"""r9 escape-fidelity機械照合
- source audit: {relative(INPUTS['escape_analysis'])} / SHA-256 {sha256(INPUTS['escape_analysis'])}
- r8 independent PAD source: {relative(INPUTS['r8_robin'])} / SHA-256 {sha256(INPUTS['r8_robin'])}
- r8 G1 generated Robin: {relative(INPUTS['r8_generated'])} / SHA-256 {sha256(INPUTS['r8_generated'])}
- r8 G1 PAD re-copy: {relative(INPUTS['r8_pad_recopy'])} / SHA-256 {sha256(INPUTS['r8_pad_recopy'])}
- authoritative source bracket-backslash counts: {generation['authoritative_teaching_backslash_open_bracket_count']} / {generation['authoritative_teaching_backslash_close_bracket_count']}
- generated bracket-backslash counts: {generation['generated_backslash_open_bracket_count']} / {generation['generated_backslash_close_bracket_count']}
- expected adaptation vs generated differing lines: {generation['expected_vs_generated_differing_lines']}
- generated vs PAD re-copy differing lines: {pad['generated_vs_pad_recopy_differing_lines']}; all are bracket-backslash doubling: {str(pad['all_differences_are_bracket_backslash_doubling']).lower()}
- PAD import/save: {pad['designer_action_count']} action / {pad['designer_variable_count']} variable / saved {str(pad['saved']).lower()} / runs {pad['pad_runs']}
- bounded diagnostic normalization explains the expected text exactly, but it was not applied to the generated evidence and is not a PASS.
- hidden model reasoning remains unknown. Confirmed boundary is the generated text before PAD import.
- r9 changes only the instruction/bundle fidelity contract; the independent teaching Robin and embedded script remain byte-identical. Copilot send 0、PAD import/run 0、GitHub write 0。

{FIDELITY_CONTRACT.rstrip()}
"""


def build(destination: Path) -> None:
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Candidate exists; sealed versions must not be overwritten")

    actual = {name: sha256(path) for name, path in INPUTS.items()}
    if actual != EXPECTED:
        raise ValueError(f"Protected r8/audit/fixed input hash mismatch: {actual}")

    manifest = json.loads(INPUTS["r8_manifest"].read_bytes())
    analysis = json.loads(INPUTS["escape_analysis"].read_bytes())
    acceptance = json.loads(INPUTS["r8_acceptance"].read_bytes())
    if manifest["version"] != "20260916-excel-r8":
        raise ValueError("Unexpected base candidate")
    if analysis["decision"] != "PASS_ROOT_CAUSE_BOUNDARY_READY_FOR_UNSENT_SUCCESSOR":
        raise ValueError("Escape analysis is not passing")
    if acceptance["decision"]["status"] != "STOPPED_BEFORE_RUN1_PAD_RECOPY_MISMATCH":
        raise ValueError("r8 G1 stop evidence changed")
    if acceptance["runs"]["pad_runs_used"] != 0:
        raise ValueError("r8 G1 now records an execution")
    for record in manifest["source_files"]:
        if sha256(BASE / record["path"]) != record["sha256"]:
            raise ValueError(f"r8 source mismatch: {record['path']}")
    if manifest["instruction_sha256"] != actual["r8_instruction"]:
        raise ValueError("r8 instruction manifest mismatch")
    if manifest["bundle_sha256"] != actual["r8_bundle"]:
        raise ValueError("r8 bundle manifest mismatch")

    base_instruction = text(INPUTS["r8_instruction"])
    base_bundle = text(INPUTS["r8_bundle"])
    teaching_robin = text(INPUTS["r8_robin"])
    generated = text(INPUTS["r8_generated"])
    if any(term in base_instruction + base_bundle + teaching_robin for term in FIXED_COMPLETION_TERMS + UNIQUE_GRADER_STRINGS):
        raise ValueError("Fixed EX03 answer leaked into the independent r8 package")
    if EXPECTED_TEXT in base_instruction or EXPECTED_TEXT in teaching_robin:
        raise ValueError("Fixed EX03 expected percent text leaked into r8 instruction/source")
    if teaching_robin.count(r"\[") or teaching_robin.count(r"\]"):
        raise ValueError("Authoritative teaching Robin contains forbidden bracket backslashes")
    if (generated.count(r"\["), generated.count(r"\]")) != (53, 53):
        raise ValueError("Observed r8 generated escape counts changed")

    (destination / "knowledge").mkdir(parents=True)
    (destination / "support").mkdir(parents=True)
    shutil.copyfile(INPUTS["r8_script"], destination / SCRIPT_SUPPORT)
    shutil.copyfile(INPUTS["r8_robin"], destination / ROBIN_SUPPORT)
    (destination / FIDELITY_SUPPORT).write_text(
        FIDELITY_CONTRACT, encoding="utf-8", newline="\n"
    )

    audit = audit_section(analysis)
    mapping = example_mapping()
    for record in manifest["source_files"]:
        source = BASE / record["path"]
        name = Path(record["path"]).name
        content = text(source)
        if name.startswith(("PAD-Robin-00-", "PAD-Robin-04-", "PAD-Robin-06-")):
            if R8_MARKER not in content:
                raise ValueError(f"r8 replacement marker missing: {name}")
            content = content.split(R8_MARKER, 1)[0].rstrip("\r\n") + "\n\n"
            content += R9_SCOPE + mapping
            if name.startswith("PAD-Robin-04-"):
                content += "\n" + audit
            if name.startswith("PAD-Robin-06-"):
                content += "\nEX03 r9 PAD保存・再コピー独立教材原文（r8とbyte同一。別条件例・未実行・未受入）\n"
                content += f"source: {ROBIN_SUPPORT.as_posix()} / SHA-256 {sha256(INPUTS['r8_robin'])}\n"
                content += "この見出しより後のRobinだけを逐語使用する。RunScript内のraw角括弧へbackslashを追加しない。依頼のdata slotと教材専用error labelだけを同じ確認範囲内で一貫置換する。\n"
                content += teaching_robin.rstrip("\r\n") + "\n"
        (destination / record["path"]).write_bytes(content.encode("utf-8"))

    if R8_INSTRUCTION_MARKER not in base_instruction:
        raise ValueError("r8 instruction replacement marker missing")
    instructions = base_instruction.split(R8_INSTRUCTION_MARKER, 1)[0] + R9_INSTRUCTIONS
    (destination / "agent-instructions.txt").write_text(
        instructions, encoding="utf-8", newline="\n"
    )
    instruction_utf16 = len(instructions.encode("utf-16-le")) // 2
    if instruction_utf16 > 8000:
        raise ValueError(f"Instruction exceeds limit: {instruction_utf16}")
    if any(term in instructions for term in FIXED_COMPLETION_TERMS + UNIQUE_GRADER_STRINGS + [EXPECTED_TEXT]):
        raise ValueError("Fixed EX03 answer leaked into r9 instruction")

    subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(ROOT / "tools/Build-KnowledgeBundle.ps1"),
            "-Root",
            str(destination),
            "-KnowledgeDirectory",
            "knowledge",
            "-OutputPath",
            "knowledge/PAD-Robin-Knowledge-Bundle.txt",
        ],
        check=True,
    )

    bundle_path = destination / manifest["bundle_path"]
    current_bundle = text(bundle_path)
    if any(term in current_bundle for term in FIXED_COMPLETION_TERMS + UNIQUE_GRADER_STRINGS):
        raise ValueError("Fixed EX03 complete answer or grader data leaked into r9 bundle")
    if normalized(teaching_robin) not in normalized(current_bundle):
        raise ValueError("Independent PAD teaching source is missing from r9 bundle")
    for required in [
        "Never prefix them with a backslash",
        "Both counts must be zero",
        "No teaching-only label may remain",
    ]:
        if required not in current_bundle:
            raise ValueError(f"Escape-fidelity contract missing from r9 bundle: {required}")

    evidence_inputs = dict(manifest.get("evidence_inputs", {}))
    for path in INPUTS.values():
        evidence_inputs[relative(path)] = sha256(path)

    support_files = []
    for support_path, runtime in [
        (SCRIPT_SUPPORT, "embedded_in_robin_not_loaded_from_disk"),
        (ROBIN_SUPPORT, "authoritative_independent_teaching_source_reused_not_executed"),
        (FIDELITY_SUPPORT, "generation_time_text_fidelity_contract_not_runtime_code"),
    ]:
        path = destination / support_path
        support_files.append(
            {
                "path": support_path.as_posix(),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
                "runtime": runtime,
            }
        )

    manifest.update(
        version=VERSION,
        status="FROZEN_CANDIDATE_EX03_ESCAPE_FIDELITY_GATE_NOT_COPILOT_OR_RUNTIME_ACCEPTED",
        inherits_live_acceptance=False,
        base_candidate="20260916-excel-r8",
        base_commit=BASE_COMMIT,
        instruction_sha256=sha256(destination / "agent-instructions.txt"),
        instruction_utf16=instruction_utf16,
        bundle_sha256=sha256(bundle_path),
        evidence_inputs=evidence_inputs,
        builder="tools/Build-Issue38Ex03CandidateR9.py",
        support_files=support_files,
    )
    for record in manifest["source_files"]:
        path = destination / record["path"]
        record.update(sha256=sha256(path), bytes=path.stat().st_size)
    manifest["evidence"].update(
        copilot="R8_G1_ONE_SEND_GENERATED_R9_NOT_SENT",
        pad="R8_G1_UNMODIFIED_IMPORT_SAVE_RECOPY_MISMATCH_RUN0_R9_NO_NEW_PAD_ACTION",
        teaching_test_independence="PASS_R9_FIXED_EX03_COMPLETE_ANSWER_ABSENT_FROM_CURRENT_INSTRUCTION_BUNDLE_AND_SUPPORT",
        escape_failure_boundary="CONFIRMED_NORMAL_M365_GENERATED_TEXT_BEFORE_PAD_IMPORT",
        escape_failure_hidden_model_cause="UNKNOWN_NOT_CLAIMED",
        generated_backslash_open_bracket_count=53,
        generated_backslash_close_bracket_count=53,
        teaching_backslash_open_bracket_count=0,
        teaching_backslash_close_bracket_count=0,
        expected_vs_generated_differing_lines=31,
        generated_vs_pad_recopy_differing_lines=30,
        diagnostic_normalization_explains_expected=True,
        diagnostic_normalization_applied_to_evidence=False,
        stale_teaching_label_count=2,
        source_chain="R8_PAD_SOURCE_TO_R8_G1_GENERATION_TO_PAD_RECOPY_AUDITED_R9_FIDELITY_GATE_ADDED",
        source_pad_recopy_sha256=sha256(INPUTS["r8_robin"]),
        source_reused_exact_bytes=True,
        source_new_pad_capture_required=False,
        source_new_pad_capture_reason="UNCHANGED_AUTHORITATIVE_R8_SOURCE_ALREADY_PASTE_SAVE_RECOPY_VERIFIED",
        fixed_request_spec_expected_hashes_preserved=True,
        fixed_completion_terms_absent_from_independent_source=True,
        unique_grader_strings_absent_from_independent_source=True,
        existing_output_guard="STATIC_ONLY_NOT_LIVE_TESTED",
        candidate_adaptation="UNSENT_ESCAPE_FIDELITY_GATE_WITH_UNCHANGED_INDEPENDENT_PAD_SOURCE",
        candidate_script_sha256=sha256(INPUTS["r8_script"]),
        candidate_robin_sha256=sha256(INPUTS["r8_robin"]),
        fidelity_contract_sha256=sha256(destination / FIDELITY_SUPPORT),
    )
    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "version": VERSION,
                "instruction_utf16": instruction_utf16,
                "instruction_sha256": manifest["instruction_sha256"],
                "bundle_sha256": manifest["bundle_sha256"],
                "manifest_sha256": sha256(destination / "manifest.json"),
                "teaching_robin_sha256": manifest["evidence"]["source_pad_recopy_sha256"],
                "fidelity_contract_sha256": manifest["evidence"]["fidelity_contract_sha256"],
                "independence": manifest["evidence"]["teaching_test_independence"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=ROOT / "copilot/versions" / VERSION
    )
    build(parser.parse_args().output)
