#!/usr/bin/env python3
"""Build the local-only EX03 r11 package from the preserved r10 package.

r11 changes the actual independent teaching implementation: it replaces the
fragile static-member expressions lost in both r9 and r10 with a shorter
PowerShell script, then uses the PAD-saved/re-copied Robin as the authoritative
source.  The fixed EX03 request, specification, expected values, old failures,
and acceptance boundary remain unchanged.

This builder does not send to Copilot and does not execute PAD.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "copilot/versions/20260917-excel-r10"
VERSION = "20260917-excel-r11"
BASE_COMMIT = "ac90b0943d2ff4e1172c23712ef49fe93787b7b2"
PROBE = ROOT / "catalog/acceptance/issue38/probes/ex03-r11-minimal-powershell"
R9_CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r9-G1"
R10_CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r10-G1"
R10_MARKER = "Issue #38 EX03 / 20260917-excel-r10 候補の現在の範囲"
R10_INSTRUCTION_MARKER = "【Excel値転記・20260917-excel-r10候補】"
SCRIPT_SUPPORT = Path("support/EX03-R11-Independent-Minimal-FormatSandwich.ps1.txt")
ROBIN_SUPPORT = Path("support/EX03-R11-Independent-PAD-Recopy.robin")
CONTRACT_SUPPORT = Path("support/EX03-R11-Minimal-Structural-Contract.txt")

INPUTS = {
    "r10_manifest": BASE / "manifest.json",
    "r10_instruction": BASE / "agent-instructions.txt",
    "r10_bundle": BASE / "knowledge/PAD-Robin-Knowledge-Bundle.txt",
    "analysis": PROBE / "analysis.json",
    "report": PROBE / "report.md",
    "script": PROBE / "independent-minimal-format-sandwich.ps1.txt",
    "prepared_robin": PROBE / "independent-candidate.robin",
    "pad_recopy": PROBE / "independent-pad-recopy.robin",
    "pad_capture": PROBE / "independent-pad-capture.json",
    "synthetic_pad_capture": PROBE / "synthetic-pad-capture.json",
    "synthetic_preflight": PROBE / "synthetic-pad-run-preflight.json",
    "synthetic_run": PROBE / "synthetic-pad-run.json",
    "synthetic_artifact": PROBE / "synthetic-artifact-verification.json",
    "synthetic_result": PROBE / "runtime/result.xlsx",
    "r9_generated": R9_CYCLE / "generated.robin",
    "r10_generated": R10_CYCLE / "generated.robin",
    "fixed_request": ROOT / "catalog/acceptance/issue38/requests/EX03.txt",
    "fixed_spec": ROOT / "catalog/acceptance/issue38/spec.json",
    "fixed_expected": ROOT / "catalog/acceptance/issue38/expected.json",
}

EXPECTED = {
    "r10_manifest": "7807e31e8177b05dc89d235496ee1b5978502f7406586dff2621d769981d6cbe",
    "r10_instruction": "9434c976457b2fec14ad24d8ee57a3400e7eb092ba38259e3f8f728139c20681",
    "r10_bundle": "0c53d6ce82fc5e23363332420b59c34470decbb123f804b2e628d26d58928ec6",
    "analysis": "b6912024ac126928cdf5474d1d71d243c94ad523e3fc190a95086eb28b9e2255",
    "report": "966b64fabe42296b98fc2b05a9c952d4b2856370c3a29fb503664c9ec13aeff5",
    "script": "068e676d70c373a9cf8203d19f6154e38460f609c4fdf774dbef1528f68fc7ae",
    "prepared_robin": "d2cac7051bb54cba44edb61aba48a7af7b8db9d4962425a519f48a6d137d25de",
    "pad_recopy": "148267f09f53d74db1059cee823a4a2e159f2bbebfa249d3a25c996796fa765b",
    "pad_capture": "5123b133487219b29348c9fc27a75f5f56b2cd3885ca893fb4e84327a2fe0621",
    "synthetic_pad_capture": "fc50f1e98fb624f4bab7f38ea422bfc8fb3eb3c2e21190dba6fcaa6467342d22",
    "synthetic_preflight": "6590feab3d529e79080018c1258b2a54254927f769df6eaa526a916add9755d9",
    "synthetic_run": "43f792c1ec8fc387adb43e17b7e669b80b6c5ea7e45d6e03668e684785ac4b73",
    "synthetic_artifact": "1054e360275062293694426520af64eb9d50595a6cd06d1300d356ee5b37734d",
    "synthetic_result": "3f10c3ee8ca916f525bdcf881a959e3d5bd8f22d2275dbae6af60b7b7a8e52ee",
    "r9_generated": "7a02ea0d073adde698578b8fa578f5701c728114ee55fbf20aa0ecdaaa32cb14",
    "r10_generated": "4946431c9ce47f986b841115fbfd328036356c4e12ae7cbe912c2bf06e2b1ed3",
    "fixed_request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "fixed_spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "fixed_expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
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

TOKEN_COUNTS = {
    "[string]": 12,
    "[bool]": 2,
    "[void]": 6,
    "[Runtime.InteropServices.Marshal]": 7,
    "[IO.Path]": 2,
    "::GetFullPath(": 2,
    "-ieq": 1,
    "$matches[0]": 1,
    "$beforeNumberFormat": 3,
}
REQUIRED_RAW_FRAGMENTS = [
    "if ([IO.Path]::GetFullPath([string]$candidate.FullName) -ieq $targetPath) { $matches += $candidate }",
    "$cell.Value2 = [string]$payload.probe",
    "finally { $cell.NumberFormat = $beforeNumberFormat }",
    "$cell.Value2 -isnot [string]",
    "if ([string]$cell.PrefixCharacter -cne \\'\\')",
]
FORBIDDEN_FRAGMENTS = [
    "[string]::Equals(",
    "[StringComparison]::OrdinalIgnoreCase",
    "[string]::IsNullOrEmpty(",
    ":Equals([IO.Path]",
    "-not :IsNullOrEmpty(",
    "[IO.Path]::GetFulling]",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def normalized(value: str) -> str:
    return value.replace("\r\n", "\n").rstrip("\n")


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


R11_SCOPE = """Issue #38 EX03 / 20260917-excel-r11 候補の現在の範囲
この節だけがr10後継の追加範囲である。固定依頼・期待値、旧版、旧FAIL、成功済みprobe、558差分を変更せず、Copilot生成・EX03統合Runの成功へ転用しない。
1. r9/r10の2破損は、保存済みRobinや抽出scriptより前の最初に保全できた応答表現に既にある。r9はrendered code DOM、r10はcopied full responseが最初の確認点である。code copy、repository保存、Robin action抽出、文字列decodeは破損を追加も修復もしない。非公開のmodel/service内部原因は不明のまま確定しない。
2. 既知良好Robinはsupport scriptへ完全decodeしPowerShell parser error 0。意図的破損負例は2破損をそのままdecodeしてparser error 19となる。抽出器・decode器は修正不要である。
3. r11は検査文だけでなく内包PowerShellを88行5011 byteから58行3300 byteへ短縮する。`[string]::Equals`、`[StringComparison]::OrdinalIgnoreCase`、`[string]::IsNullOrEmpty`を使わない。
4. 絶対FullNameを正規化して`-ieq`で一冊だけ選ぶこと、JSON primitiveのsourceがSystem.Stringであること、Value2の値とSystem.String、非formula、元NumberFormatを内側finallyで復元すること、prefix空、COM解放を保持する。
5. 独立教材Robinは専用PAD 2.71.115.26224、ja-JP、Power Fx OFFへ1回貼付け、110 action・45 variableとして1回保存・1回再コピーし、LF正規化後に準備原文と一致した。教材は実行していない。
6. 同じ短縮表現の2セル合成probeは別フローへ1回貼付け・保存・再コピー後に1回だけ実行した。PAD内のsource/immediate/reopened値・JSON比較は全てTrueで、出力の文字列値・型、数値値・型、元書式、prefix空、formulaなしを読み取り専用外部照合でも確認した。これは合成2セルだけでありEX03統合受入ではない。例外注入Runは未実施で、finally構造と正常経路の復元だけを確認した。
7. r11は未送信のローカル候補である。通常M365 Copilot送信、EX03統合PAD Run1/Run2、既存output guard実機経路、GitHub書込みはいずれも0。未確認の型・別shape・別PC/PAD版へ一般化しない。
"""

EXAMPLE_MAPPING = """r11独立教材例のデータ対応:
- source-one.xlsx / 教材入力一 H3:I5 -> 教材出力一 J4:K6。各行はtext, number。
- source-two.xlsx / 教材入力二 C7:E8 -> 教材出力二 B10:D11。各行はtext, number, text。
- work-copy.xlsxだけを編集し、未存在のexample-result.xlsxへSaveAsする。
- text 7位置は同一RunのDataTableをJSON primitiveで確認して内包scriptから各1回、number 5位置は通常WriteCellで各1回だけ書く。保存・クローズ・ReadOnly再開後に12位置を個別JSON比較する。
- 固定するもの: 命令名、引数名、mode、DataTable添字、型の役割、依存順、分岐、1 RunScript、5 numeric writes、12 JSON comparisons。
- 依頼から変更するもの: 同じ確認範囲内のpath、存在するsheet名、3x2と2x3のrectangle、target、work copy、未存在output、data slot由来のerror label。
- text/number以外、異なるshape、空白、真偽値、日付、error、formula result、任意object、別PC/PAD版へ一般化しない。
"""

STRUCTURAL_CONTRACT = """EX03 r11 minimal embedded-PowerShell structural contract
1. Use the complete independent PAD-recopied Robin as the source. Change only request-derived data slots and teaching-only labels; do not paraphrase or reconstruct other lines.
2. Raw Robin must contain zero backslash-open-bracket and zero backslash-close-bracket sequences.
3. Require these exact raw token counts after adaptation: `[string]` 12; `[bool]` 2; `[void]` 6; `[Runtime.InteropServices.Marshal]` 7; `[IO.Path]` 2; `::GetFullPath(` 2; `-ieq` 1; `$matches[0]` 1; `$beforeNumberFormat` 3.
4. Require exactly once: the normalized FullName `-ieq` match; string Value2 assignment; inner-finally NumberFormat restoration; destination string-type check; empty PrefixCharacter check.
5. Require zero occurrences of the retired or observed corrupt fragments: `[string]::Equals(`; `[StringComparison]::OrdinalIgnoreCase`; `[string]::IsNullOrEmpty(`; `:Equals([IO.Path]`; `-not :IsNullOrEmpty(`; `[IO.Path]::GetFulling]`.
6. Preserve one RunScript, five numeric WriteCell actions, twelve JSON source/readback comparisons, exact workbook one-match guard, non-formula guards, and fail-before-SaveAs behavior.
7. If any check fails, emit no Robin and report the failed check. Do not repair generated output after emission. A refusal or no-code result is not a runtime PASS.
8. This contract is limited to the independently captured text/number shapes. It does not prove EX03 execution or unobserved types.
"""

R11_INSTRUCTIONS = """【Excel値転記・20260917-excel-r11候補】
標準入力は同版の指示全文＋bundle実添付です。固定依頼・期待値、旧版、r9/r10生成安全FAIL、成功済みprobe、558差分FAILを保持し、旧生成・旧Run・合成probeを今回のEX03受入へ継承しません。00/04/06末尾の「EX03 / 20260917-excel-r11」だけを追加範囲として参照します。
r9/r10の型修飾欠落は、後段のcopy・repository保存・Robin抽出・decodeより前の保全済み応答表現に既にありました。非公開のmodel/service内部原因は不明です。r11は実装を短縮し、独立教材内包PowerShellで`[string]::Equals`、`[StringComparison]::OrdinalIgnoreCase`、`[string]::IsNullOrEmpty`を使いません。
独立教材Robinは専用PAD 2.71.115.26224、ja-JP、Power Fx OFFへ1回貼付け、110 action・45 variableとして保存・再コピーし、LF正規化後に準備原文と一致しました。教材自体は未実行です。同じ短縮表現の2セル合成probeだけは別フローで1回実行し、PAD内のsource/immediate/reopened JSON比較と読み取り専用成果物照合を通過しました。これはEX03統合受入ではなく、例外注入経路も未実行です。
回答は06末尾の完全な独立PAD再コピー原文から、依頼本文で列挙されたdata slotと教材専用labelだけを一貫置換して作ります。それ以外を言い換え、短縮、修復、最適化、再構成しません。教材専用path・sheet・target・labelを残しません。固定試験のpath、sheet、target cell、grader値、完成Robinを教材から補いません。
回答確定前にraw Robinのbackslash-open-bracket/backslash-close-bracket各0件と、`[string]`12、`[bool]`2、`[void]`6、`[Runtime.InteropServices.Marshal]`7、`[IO.Path]`2、`::GetFullPath(`2、`-ieq`1、`$matches[0]`1、`$beforeNumberFormat`3を確認します。正規化FullNameの`-ieq`一冊選択、string Value2代入、内側finallyの元NumberFormat復元、destination System.String確認、prefix空確認を各1件必要とします。
`[string]::Equals(`、`[StringComparison]::OrdinalIgnoreCase`、`[string]::IsNullOrEmpty(`、`:Equals([IO.Path]`、`-not :IsNullOrEmpty(`、`[IO.Path]::GetFulling]`は各0件とします。どれか不一致ならRobinを出さず失敗項目を説明し、生成後の手修正や再表示で合格にしません。
固定するのは命令名、引数名、mode、DataTable添字、text/numberの役割、依存順、分岐、1 RunScript、5 numeric write、12 JSON compareです。依頼から変更するのは同じ確認範囲内のpath、存在sheet、3x2/2x3 rectangle、target start、work copy、未存在output、data slot由来labelです。text/number以外、別shape、空白、真偽値、日付、error、formula result、任意object、別PC/PAD版へ一般化しません。
入力と原本はReadOnlyで開き、検証者が準備したwork copyだけを編集します。既存output時はwrite経路へ入りません。文字列7位置は同じRunのDataTableからJSON化して内包scriptで各1回、数値5位置は通常WriteCellで各1回だけ書きます。固定値や1セルだけの事後修正を入れません。
内包scriptは絶対FullName正規化後の`-ieq`で一冊だけ選び、source文字列、非formula、元NumberFormat、一時@、Value2、内側finally復元、直後の値・System.String・元format・prefix空・formulaなしを検査します。失敗時はSaveAs・完了状態へ進まず、外部ps1、network、delete、overwrite、権限・security・Excel設定変更を要求しません。
SaveAs後はcloseしてReadOnly再開し、2矩形をTypedValuesで再取得して12位置を個別JSON比較します。原本・対象外cell・formula・effective formatの独立検査と558差分FAILを維持します。
回答は全工程を一つのtextコードブロックへ入れます。r11は通常M365 Copilot未送信、無修正EX03 PAD貼付け・Run1/Run2・成果物照合・既存output guard実機経路が未実施のローカル候補です。完成・実行済み・受入済みと表示しません。
"""


def build(destination: Path) -> dict[str, object]:
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Candidate exists; sealed versions must not be overwritten")

    actual = {name: sha256(path) for name, path in INPUTS.items()}
    if actual != EXPECTED:
        raise ValueError(f"Protected r10/r11/fixed input hash mismatch: {actual}")

    manifest = json.loads(INPUTS["r10_manifest"].read_bytes())
    analysis = json.loads(INPUTS["analysis"].read_bytes())
    source_capture = json.loads(INPUTS["pad_capture"].read_bytes())
    synthetic_capture = json.loads(INPUTS["synthetic_pad_capture"].read_bytes())
    synthetic_run = json.loads(INPUTS["synthetic_run"].read_bytes())
    artifact = json.loads(INPUTS["synthetic_artifact"].read_bytes())
    if manifest["version"] != "20260917-excel-r10":
        raise ValueError("Unexpected base candidate")
    if analysis["pipeline_boundary"]["classification"] != "ACQUISITION_COPY_SAVE_EXTRACTION_DECODE_NOT_CAUSAL":
        raise ValueError("Pipeline boundary analysis changed")
    if source_capture["result"] != "PASS_PAD_DESIGNER_SAVE_RECOPY_NO_EXECUTION":
        raise ValueError("Independent PAD re-copy is not passing")
    if synthetic_capture["result"] != "PASS_PAD_DESIGNER_SAVE_RECOPY_NO_EXECUTION":
        raise ValueError("Synthetic PAD re-copy is not passing")
    if synthetic_run["decision"] != "PASS_ONE_DEDICATED_SYNTHETIC_PAD_RUN":
        raise ValueError("Dedicated synthetic PAD run is not passing")
    if artifact["status"] != "PASS_EXTERNAL_ARTIFACT_CHECK_FOR_DEDICATED_PAD_PROBE":
        raise ValueError("Synthetic artifact verification is not passing")
    if not all(artifact["checks"].values()):
        raise ValueError("Synthetic artifact checks are incomplete")

    for record in manifest["source_files"]:
        if sha256(BASE / record["path"]) != record["sha256"]:
            raise ValueError(f"r10 source mismatch: {record['path']}")
    if manifest["instruction_sha256"] != actual["r10_instruction"]:
        raise ValueError("r10 instruction manifest mismatch")
    if manifest["bundle_sha256"] != actual["r10_bundle"]:
        raise ValueError("r10 bundle manifest mismatch")

    base_instruction = text(INPUTS["r10_instruction"])
    script = text(INPUTS["script"])
    prepared_robin = text(INPUTS["prepared_robin"])
    pad_recopy = text(INPUTS["pad_recopy"])
    if normalized(prepared_robin) != normalized(pad_recopy):
        raise ValueError("Prepared and PAD-recopied Robin differ beyond newline serialization")

    source_module = load_module(
        "issue38_r11_builder_source",
        ROOT / "tools/Prepare-Issue38Ex03R8IndependentSource.py",
    )
    parser_module = load_module(
        "issue38_r11_builder_parser",
        ROOT / "tools/Analyze-Issue38Ex03R10Generation.py",
    )
    action = source_module.extract_action(pad_recopy)
    decoded = source_module.decode_robin_string(source_module.action_payload(action))
    if normalized(decoded) != normalized(script):
        raise ValueError("PAD-recopied Robin does not decode exactly to the r11 script")
    if parser_module.parse_powershell(decoded):
        raise ValueError("r11 embedded PowerShell no longer parses cleanly")

    combined_source = base_instruction + pad_recopy + script
    for term in FIXED_COMPLETION_TERMS + UNIQUE_GRADER_STRINGS + [EXPECTED_TEXT]:
        if term in combined_source:
            raise ValueError(f"Fixed EX03 answer leaked into independent source: {term}")
    if pad_recopy.count(r"\[") or pad_recopy.count(r"\]"):
        raise ValueError("Authoritative Robin contains forbidden bracket backslashes")
    for token, count in TOKEN_COUNTS.items():
        if pad_recopy.count(token) != count:
            raise ValueError(f"r11 token count changed: {token}")
    for fragment in REQUIRED_RAW_FRAGMENTS:
        if pad_recopy.count(fragment) != 1:
            raise ValueError(f"r11 required fragment changed: {fragment}")
    for fragment in FORBIDDEN_FRAGMENTS:
        if fragment in pad_recopy:
            raise ValueError(f"r11 contains retired/corrupt fragment: {fragment}")
    if pad_recopy.count("Scripting.RunPowershellScript.RunScript") != 1:
        raise ValueError("r11 RunScript count changed")
    if pad_recopy.count("Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource") != 5:
        raise ValueError("r11 numeric write count changed")
    if pad_recopy.count("_ValueTypeMatch TO SourceCellJson = SavedCellJson") != 12:
        raise ValueError("r11 JSON comparison count changed")

    (destination / "knowledge").mkdir(parents=True)
    (destination / "support").mkdir(parents=True)
    shutil.copyfile(INPUTS["script"], destination / SCRIPT_SUPPORT)
    shutil.copyfile(INPUTS["pad_recopy"], destination / ROBIN_SUPPORT)
    (destination / CONTRACT_SUPPORT).write_text(
        STRUCTURAL_CONTRACT, encoding="utf-8", newline="\n"
    )

    validation_summary = f"""r11 local validation evidence
- pipeline analysis: {relative(INPUTS['analysis'])} / SHA-256 {actual['analysis']}
- independent prepared Robin: {relative(INPUTS['prepared_robin'])} / SHA-256 {actual['prepared_robin']}
- independent PAD re-copy: {relative(INPUTS['pad_recopy'])} / SHA-256 {actual['pad_recopy']} / LF-normalized exact true / executed false
- synthetic PAD re-copy: {relative(INPUTS['synthetic_pad_capture'])} / SHA-256 {actual['synthetic_pad_capture']}
- one dedicated synthetic PAD run: {relative(INPUTS['synthetic_run'])} / SHA-256 {actual['synthetic_run']} / PAD comparisons all true
- read-only synthetic artifact verification: {relative(INPUTS['synthetic_artifact'])} / SHA-256 {actual['synthetic_artifact']} / checks {len(artifact['checks'])}/{len(artifact['checks'])}
- r9/r10 generated outputs remain at SHA-256 {actual['r9_generated']} and {actual['r10_generated']}.
- Copilot send 0; EX03 integrated Run 0; GitHub write 0; legacy 558 failure and unconfirmed existing-output guard retained.
"""

    for record in manifest["source_files"]:
        source = BASE / record["path"]
        name = Path(record["path"]).name
        content = text(source)
        if name.startswith(("PAD-Robin-00-", "PAD-Robin-04-", "PAD-Robin-06-")):
            if R10_MARKER not in content:
                raise ValueError(f"r10 replacement marker missing: {name}")
            content = content.split(R10_MARKER, 1)[0].rstrip("\r\n") + "\n\n"
            content += R11_SCOPE + EXAMPLE_MAPPING
            if name.startswith("PAD-Robin-04-"):
                content += "\n" + validation_summary + "\n" + STRUCTURAL_CONTRACT
            if name.startswith("PAD-Robin-06-"):
                content += "\nEX03 r11 PAD保存・再コピー独立教材原文（別条件例・未実行・未受入）\n"
                content += f"source: {ROBIN_SUPPORT.as_posix()} / SHA-256 {actual['pad_recopy']}\n"
                content += "この見出しより後のRobinだけを逐語使用し、依頼由来data slotと教材専用label以外を変更しない。\n"
                content += pad_recopy.rstrip("\r\n") + "\n"
        (destination / record["path"]).write_bytes(content.encode("utf-8"))

    if R10_INSTRUCTION_MARKER not in base_instruction:
        raise ValueError("r10 instruction replacement marker missing")
    instructions = base_instruction.split(R10_INSTRUCTION_MARKER, 1)[0] + R11_INSTRUCTIONS
    (destination / "agent-instructions.txt").write_text(
        instructions, encoding="utf-8", newline="\n"
    )
    instruction_utf16 = len(instructions.encode("utf-16-le")) // 2
    if instruction_utf16 > 8000:
        raise ValueError(f"Instruction exceeds limit: {instruction_utf16}")
    for term in FIXED_COMPLETION_TERMS + UNIQUE_GRADER_STRINGS + [EXPECTED_TEXT]:
        if term in instructions:
            raise ValueError(f"Fixed EX03 answer leaked into r11 instruction: {term}")

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
    bundle = text(bundle_path)
    if normalized(pad_recopy) not in normalized(bundle):
        raise ValueError("Complete PAD-recopied independent Robin is missing from bundle")
    for term in FIXED_COMPLETION_TERMS + UNIQUE_GRADER_STRINGS:
        if term in bundle:
            raise ValueError(f"Fixed EX03 answer leaked into r11 bundle: {term}")
    for required in [
        "r11 minimal embedded-PowerShell structural contract",
        "[string]::Equals(",
        "one RunScript",
        "例外注入Runは未実施",
    ]:
        if required not in bundle:
            raise ValueError(f"r11 scope/contract missing from bundle: {required}")

    evidence_inputs = dict(manifest.get("evidence_inputs", {}))
    for path in INPUTS.values():
        evidence_inputs[relative(path)] = sha256(path)

    support_files = []
    for path, runtime in [
        (SCRIPT_SUPPORT, "embedded_in_robin_not_loaded_from_disk"),
        (ROBIN_SUPPORT, "authoritative_independent_pad_recopy_not_executed"),
        (CONTRACT_SUPPORT, "generation_time_structural_contract_not_runtime_code"),
    ]:
        full = destination / path
        support_files.append(
            {
                "path": path.as_posix(),
                "sha256": sha256(full),
                "bytes": full.stat().st_size,
                "runtime": runtime,
            }
        )

    manifest.update(
        version=VERSION,
        status="LOCAL_CANDIDATE_EX03_MINIMAL_POWERSHELL_PAD_RECOPIED_SYNTHETIC_VALIDATED_NOT_COPILOT_OR_INTEGRATED_ACCEPTED",
        inherits_live_acceptance=False,
        base_candidate="20260917-excel-r10",
        base_commit=BASE_COMMIT,
        instruction_sha256=sha256(destination / "agent-instructions.txt"),
        instruction_utf16=instruction_utf16,
        bundle_sha256=sha256(bundle_path),
        evidence_inputs=evidence_inputs,
        builder="tools/Build-Issue38Ex03CandidateR11.py",
        support_files=support_files,
    )
    for record in manifest["source_files"]:
        path = destination / record["path"]
        record.update(sha256=sha256(path), bytes=path.stat().st_size)
    manifest["evidence"].update(
        copilot="R9_AND_R10_ONE_SEND_EACH_STRUCTURALLY_CORRUPT_R11_NOT_SENT",
        pad="R11_INDEPENDENT_SOURCE_SAVE_RECOPY_ONLY_SYNTHETIC_ONE_RUN_EX03_INTEGRATED_RUN0",
        teaching_test_independence="PASS_R11_FIXED_EX03_COMPLETE_ANSWER_ABSENT_FROM_INSTRUCTION_BUNDLE_AND_SUPPORT",
        pipeline_failure_boundary="R9_RENDERED_CODE_DOM_R10_COPIED_FULL_RESPONSE_BEFORE_COPY_SAVE_EXTRACTION_DECODE",
        pipeline_hidden_model_or_service_cause="UNKNOWN_NOT_CLAIMED",
        extraction_good_parser_error_count=0,
        extraction_intentional_negative_parser_error_count=19,
        candidate_adaptation="UNSENT_MINIMAL_EMBEDDED_POWERSHELL_WITH_AUTHORITATIVE_PAD_RECOPY",
        candidate_script_sha256=actual["script"],
        candidate_robin_sha256=actual["pad_recopy"],
        candidate_prepared_robin_sha256=actual["prepared_robin"],
        source_pad_recopy_sha256=actual["pad_recopy"],
        source_lf_normalized_exact=True,
        source_action_decodes_to_script=True,
        source_pad_action_count=110,
        source_pad_variable_count=45,
        source_executed=False,
        synthetic_pad_run_count=1,
        synthetic_pad_run_status=synthetic_run["decision"],
        synthetic_artifact_status=artifact["status"],
        synthetic_artifact_check_count=len(artifact["checks"]),
        exception_path_runtime="NOT_RUN_STRUCTURAL_FINALLY_AND_NORMAL_PATH_RESTORATION_ONLY",
        embedded_script_old_lines=analysis["local_successor"]["old_script_lines"],
        embedded_script_new_lines=analysis["local_successor"]["new_script_lines"],
        embedded_script_old_utf8_bytes_without_final_newline=analysis["local_successor"]["old_script_utf8_bytes_without_final_newline"],
        embedded_script_new_utf8_bytes_without_final_newline=analysis["local_successor"]["new_script_utf8_bytes_without_final_newline"],
        retired_fragments=analysis["local_successor"]["avoided_fragments"],
        structural_token_expected_counts=TOKEN_COUNTS,
        required_fragment_count=len(REQUIRED_RAW_FRAGMENTS),
        forbidden_fragment_count=len(FORBIDDEN_FRAGMENTS),
        fixed_request_spec_expected_hashes_preserved=True,
        fixed_completion_terms_absent_from_independent_source=True,
        unique_grader_strings_absent_from_independent_source=True,
        expected_string_100_percent_absent_from_independent_source=True,
        copilot_send_count=0,
        integrated_ex03_run_count=0,
        github_write_count=0,
        existing_output_guard="STATIC_ONLY_NOT_LIVE_TESTED",
        legacy_558_failure_preserved=True,
        structural_contract_sha256=sha256(destination / CONTRACT_SUPPORT),
    )
    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    result = {
        "version": VERSION,
        "status": manifest["status"],
        "instruction_utf16": instruction_utf16,
        "instruction_sha256": manifest["instruction_sha256"],
        "bundle_sha256": manifest["bundle_sha256"],
        "manifest_sha256": sha256(destination / "manifest.json"),
        "teaching_robin_sha256": actual["pad_recopy"],
        "teaching_script_sha256": actual["script"],
        "copilot_send": 0,
        "integrated_ex03_run": 0,
    }
    print(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=ROOT / "copilot/versions" / VERSION
    )
    build(parser.parse_args().output)
