"""Freeze the scoped EX02 type-identity successor without modifying r4.

The DataTable JSON primitive is PAD capture evidence.  The full EX02 example is
an implementation composition that still requires same-version Copilot/PAD
acceptance; this builder never promotes the primitive probe to that result.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'copilot/versions/20260915-excel-r4'
VERSION = '20260915-excel-r5'
TYPE_DIR = ROOT / 'catalog/acceptance/issue38/probes/datatable-type-identity'
TYPE_RAW = TYPE_DIR / 'captured-final.robin'
TYPE_EVIDENCE = [
    TYPE_DIR / 'acceptance.json',
    TYPE_DIR / 'capture-integrity.json',
    TYPE_DIR / 'verification.json',
    TYPE_DIR / 'run1-reconciliation.json',
    TYPE_DIR / 'run2-reconciliation.json',
]
MATRIX_RAW = ROOT / 'catalog/acceptance/issue38/probes/matrix-write/assembled-probe-rev2.robin'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


MAPPINGS = [
    (1, 0, 0, 'TargetA_C4', 'Target A', 'C4'),
    (1, 0, 1, 'TargetA_D4', 'Target A', 'D4'),
    (1, 0, 2, 'TargetA_E4', 'Target A', 'E4'),
    (1, 1, 0, 'TargetA_C5', 'Target A', 'C5'),
    (1, 1, 1, 'TargetA_D5', 'Target A', 'D5'),
    (1, 1, 2, 'TargetA_E5', 'Target A', 'E5'),
    (2, 0, 0, 'TargetB_B3', 'Target B', 'B3'),
    (2, 0, 1, 'TargetB_C3', 'Target B', 'C3'),
    (2, 1, 0, 'TargetB_B4', 'Target B', 'B4'),
    (2, 1, 1, 'TargetB_C4', 'Target B', 'C4'),
    (2, 2, 0, 'TargetB_B5', 'Target B', 'B5'),
    (2, 2, 1, 'TargetB_C5', 'Target B', 'C5'),
]


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def measured_type_section():
    raw = TYPE_RAW.read_bytes().decode('utf-8').rstrip('\r\n')
    evidence = json.loads((TYPE_DIR / 'acceptance.json').read_bytes())
    assert evidence['status'] == 'PASS_EXCEL_DATATABLE_TYPE_IDENTITY_EVIDENCE_AUDIT'
    assert evidence['actual_cell_json']['A2']['run1'] == '{"probe":1.0}'
    assert evidence['actual_cell_json']['B2']['run1'] == '{"probe":"1"}'
    return (
        f'完全原文: {relative(TYPE_RAW)} / SHA-256 {sha(TYPE_RAW)}\n'
        + raw + '\n'
        + '確認済み範囲: synthetic.xlsx の TypeProbe!A2:B2 を TypedValues/ヘッダーなしでDataTableへ取得し、'
          'DataTable[0][0]の数値1とDataTable[0][1]の文字列"1"を変換せず同じprobeキーのカスタムオブジェクトへ包み、JSON化した。'
          'Run1/Run2とも数値は {"probe":1.0}、文字列は {"probe":"1"}。同型正例2件はTrue、交差型負例2件はFalse。'
          'これはExcel DataTableセルの限定probeであり、EX02全体の生成・貼付け・保存・再読込受入ではない。\n'
        + '未確認: 日付、空白、真偽値、エラー、数式結果、カスタムオブジェクト、他PC/PAD版、任意型の一般GetType。'
          'これらへ適用範囲を広げず、未知の型が要求された場合は追加採取を求める。\n'
    )


def mapping_section():
    lines = ['固定EX02の12セル位置対応（完成フローでは各組を定数添字で個別比較）:']
    for data, row, col, name, sheet, cell in MAPPINGS:
        lines.append(f'- Data{data}[{row}][{col}] -> Readback{data}[{row}][{col}] -> {sheet}!{cell} -> {name}_ValueTypeMatch')
    lines += [
        '上記12組の値は固定fixture内では文字列または数値だけ。probe済みなのは数値1/文字列"1"の識別構文であり、他の具体値を含む12組への接続はこのr5で初めて受入する組合せである。',
        '各SourceCell/SavedCellを同じprobeキーでJSON化して文字列を比較する。PADの緩い直接等価比較だけを型一致としない。位置は上記の定数添字と固定転記先の対応で検査する。変数添字、ループ、GetType、未知の変換を発明しない。',
        '固定期待値は検証者側expected.jsonから独立照合し、Copilotへ正解として渡さない。フロー内の照合は同じRunで取得したsourceと保存・クローズ・読取り専用再読込後targetの12組に限る。',
    ]
    return '\n'.join(lines) + '\n'


CURRENT = '''Issue #38 EX02 / 20260915-excel-r5 候補の現在の範囲
この節はr4の型不足節を限定的に更新する。r4本体・r4実生成拒否・成功済み単体probeは変更も再採取もしない。実装者probeと、今回のCopilot生成物を無修正でPAD受入する結果は別判定である。
1. r4で確認済みの出力存在分岐、21アクション矩形転記、保存・クローズ・読取り専用再開、12セルの定数添字対応を保持する。入力/テンプレート原本は編集せず、未存在の別出力だけを作る。既存出力側では状態変数だけを設定し、ELSE内に全Excel書込み経路を閉じ込める。
2. 78ccbcfで採取したDataTable JSON identity原文により、同じ表示の数値1と文字列"1"を2Runで区別できた。確認したセル・設定・値・PAD環境だけが単体probeのPASSであり、EX02全体の成功ではない。
3. 固定EX02 fixtureの対象12セルは文字列または数値だけである。各source/readbackセルを変換せず同じprobeキーのカスタムオブジェクトへ包み、採取済みConvertCustomObjectToJson原文でJSON化し、対応するJSON同士を個別比較する構成候補を使う。12組すべてを定数添字で明示し、結果変数を個別に残す。
4. 日付、空白、真偽値、エラー、数式結果、任意オブジェクト、他PC/PAD版へ一般化しない。未確認型へGetTypeなどを捏造しない。12セルへの接続自体はこのr5で初めて実Copilot生成・無修正PAD 2Run・保存後再読込を受入する対象である。
5. 固定期待値は検証者だけが保持し、Copilot本文やbundleへ正解として混ぜない。フロー内ではsource/readbackの値・JSON型・定数位置を比較し、検証者が閉じた保存xlsxを固定期待値、原本SHA、対象外全セル、数式、コメント、書式・寸法に対して独立照合する。
6. 480セルの旧比較に残る書式・寸法558差分FAILを保持する。480セルの値/型/数式一致やExcelネイティブ限定属性一致を、書式保持の全体PASSに読み替えない。負例は正例出力の別コピー1セルだけを同表示の別型へ変え、少なくとも対象セルの型不一致を検出する。正例Run2の代用にはしない。
固定する構造: 各命令名、引数名、モード、列挙値、TypedValues、FirstLineIsHeader: False、DataTable型、JSONのprobeキー、文字列引用/パスエスケープ、IF/ELSE/ENDと依存順、保存→閉じる→読取り専用再開→両対象矩形再読取り→12組比較→閉じる。
変更可能なデータ: 固定依頼に示されたローカル合成xlsxパス、既存シート名、有限矩形、転記先、未存在出力名、および全参照を一貫させた変数名。型やアクション設定を変更可能データにしない。
観測を分ける: 単体probe、Copilot応答原文、コードコピー原文、PAD貼付け/保存/再コピー、各Run終了、12結果変数、保存xlsx独立検査、負例検出を別証跡にする。手組みprobeや外部検査の成功をCopilot生成フローの成功へ転用しない。
'''


def assembled_example():
    """Full fixed-path composition, explicitly not a capture or acceptance result."""
    matrix = MATRIX_RAW.read_bytes().decode('utf-8').splitlines()
    matrix = [line.replace('runs\\\\probe-matrix-A', 'runs\\\\EX02-attempt1') for line in matrix]
    output = next(line for line in matrix if line.startswith('Excel.SaveExcel.')).split('DocumentPath: ', 1)[1]
    guard_capture = (ROOT / 'catalog/acceptance/issue38/probes/output-guard/captured-uia.robin').read_bytes().decode('utf-8').splitlines()[1]
    guard = guard_capture[:guard_capture.index('File: ') + 6] + output + ') THEN'
    lines = ["SET TransferState TO $'''NOT_STARTED'''", guard,
             "    SET TransferState TO $'''OUTPUT_EXISTS_NO_WRITE'''", 'ELSE']
    lines += ['    ' + line for line in matrix]
    for data, row, col, name, _, _ in MAPPINGS:
        lines += [
            f'    SET SourceCell TO Data{data}[{row}][{col}]',
            f'    SET SavedCell TO Readback{data}[{row}][{col}]',
            "    Variables.ConvertCustomObjectToJson CustomObject: { 'probe': SourceCell } Json=> SourceCellJson",
            "    Variables.ConvertCustomObjectToJson CustomObject: { 'probe': SavedCell } Json=> SavedCellJson",
            f'    SET {name}_ValueTypeMatch TO SourceCellJson = SavedCellJson',
        ]
    lines += ["    SET TransferState TO $'''SAVED_REOPENED_12_JSON_COMPARISONS_READY'''", 'END']
    return '\n'.join(lines) + '\n'


def build(destination):
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Candidate exists; sealed versions must not be overwritten')
    manifest = json.loads((BASE / 'manifest.json').read_bytes())
    for record in manifest['source_files']:
        assert sha(BASE / record['path']) == record['sha256']
    assert sha(BASE / manifest['instruction_path']) == manifest['instruction_sha256']
    assert sha(BASE / manifest['bundle_path']) == manifest['bundle_sha256']
    (destination / 'knowledge').mkdir(parents=True)
    measured = measured_type_section()
    mappings = mapping_section()
    for record in manifest['source_files']:
        source = BASE / record['path']
        content = source.read_bytes().decode('utf-8')
        name = Path(record['path']).name
        if name.startswith(('PAD-Robin-00-', 'PAD-Robin-04-', 'PAD-Robin-06-')):
            content = content.rstrip('\r\n') + '\n\n' + CURRENT + mappings
        if name.startswith(('PAD-Robin-04-', 'PAD-Robin-06-')):
            content += '\n78ccbcfで採取済みのDataTable型identity原文（Copilot生成物ではない）\n' + measured
        if name.startswith('PAD-Robin-06-'):
            content += '\nEX02 r5統合構成例（実装者による組立、未実行・未受入。固定期待値は含まない）\n'
            content += 'r4の出力ガードと21アクションへ、上記の採取済みJSON identity構文を12個の定数位置に接続した例。Copilotは固定依頼に従う一つのRobinブロックとして出し、現版のPAD受入前に完成・実行済みと表示しない。\n'
            content += assembled_example()
        (destination / record['path']).write_bytes(content.encode('utf-8'))
    original = (BASE / 'agent-instructions.txt').read_bytes().decode('utf-8')
    prefix = original.split('【Excel値転記・', 1)[0]
    instructions = prefix + '''【Excel値転記・20260915-excel-r5候補】
標準入力は同版の指示全文＋bundle実添付です。20260913eやr4を含む旧候補の受入は継承しません。00/04/06末尾の「EX02 / 20260915-excel-r5」の範囲だけを現候補として参照します。
出力存在分岐、矩形転記、保存→クローズ→読取り専用再開、両対象矩形再読取りはr4の採取済み構造を保持します。既存出力時は書込み経路へ入らず、ELSE内だけに全Excel処理を置きます。入力/テンプレート/作業コピー/出力は別パスとし、未存在出力へだけSaveAsします。
DataTable型identityは78ccbcfの完全原文を使います。確認済みなのはTypeProbe!A2:B2の数値1と文字列"1"をTypedValuesで取得し、同じprobeキーのカスタムオブジェクトをJSON化して2Runで区別できた範囲だけです。未採取GetTypeや未知の変換を追加しません。
固定EX02の12対象セルは文字列/数値だけです。sourceと保存・クローズ・再読込後targetの対応セルを、00/04/06に列挙した12個の定数添字で個別に取り出し、それぞれ同じprobeキーでJSON化して対応JSONを比較します。12個の結果変数を残します。直接等価比較、TypedValues設定、外部検査だけで型一致としません。12セルへの接続は現版の実受入対象で、単体probe成功を完成フロー成功へ転用しません。
日付、空白、真偽値、エラー、数式結果、任意オブジェクト、他PC/PAD版へ一般化しません。固定fixture外の型が必要ならコードを出さず追加採取を示します。変数添字やループは使わず、位置対応を定数で明示します。
固定期待値は検証者専用で、回答へ推測値を埋めません。フロー内は同じRunのsource/readbackを比較し、検証者が保存xlsxを固定期待値、原本SHA、対象外全セル、数式、コメント、書式・寸法に対して独立照合します。書式・寸法558差分FAILとExcelネイティブ限定一致を両方保持し、全体PASSへ読み替えません。
回答は部分フローにせず、固定依頼の全工程を一つのRobinコードブロックへ入れます。未知の命令を発明する場合はコードを出しません。生成後の手修正を前提にせず、現版の無修正貼付け・保存・再コピー・2Run前には実行済みと書きません。
'''
    (destination / 'agent-instructions.txt').write_bytes(instructions.encode('utf-8'))
    subprocess.run([
        'pwsh', '-NoProfile', '-File', str(ROOT / 'tools/Build-KnowledgeBundle.ps1'),
        '-Root', str(destination), '-KnowledgeDirectory', 'knowledge',
        '-OutputPath', 'knowledge/PAD-Robin-Knowledge-Bundle.txt'
    ], check=True)
    evidence_inputs = dict(manifest.get('evidence_inputs', {}))
    for path in [TYPE_RAW, *TYPE_EVIDENCE]:
        evidence_inputs[relative(path)] = sha(path)
    manifest.update(
        version=VERSION,
        status='FROZEN_CANDIDATE_SCOPED_TYPE_IDENTITY_NOT_LIVE_ACCEPTED',
        base_candidate='20260915-excel-r4',
        base_commit='78ccbcf10551542d7891ac25af6a2445a3381443',
        instruction_sha256=sha(destination / 'agent-instructions.txt'),
        instruction_utf16=len(instructions.encode('utf-16-le')) // 2,
        bundle_sha256=sha(destination / manifest['bundle_path']),
        evidence_inputs=evidence_inputs,
        builder='tools/Build-Issue38Ex02CandidateR5.py',
    )
    assert manifest['instruction_utf16'] <= 8000
    for record in manifest['source_files']:
        record.update(
            sha256=sha(destination / record['path']),
            bytes=(destination / record['path']).stat().st_size,
        )
    manifest['evidence'].update(
        copilot='NOT_RUN_AT_FREEZE',
        pad='SCOPED_DATATABLE_TYPE_PRIMITIVE_REUSED_NOT_CANDIDATE_ACCEPTANCE',
        matrix_write='Two prior probe runs completed; 12 target cells match; 558 XML differences retained',
        type_comparison='DATATABLE_NUMBER_TEXT_JSON_IDENTITY_TWO_RUNS_SCOPED',
        type_comparison_sha256=sha(TYPE_RAW),
        type_comparison_scope='TypeProbe!A2:B2 number 1 versus text 1 only; full EX02 connection requires r5 live acceptance',
    )
    (destination / 'manifest.json').write_bytes(
        (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    )
    print(json.dumps({
        key: manifest[key]
        for key in ['version', 'instruction_utf16', 'instruction_sha256', 'bundle_sha256']
    }))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'copilot/versions' / VERSION)
    build(parser.parse_args().output)
