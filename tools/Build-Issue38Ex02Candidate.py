"""Freeze EX02 teaching material separately from r3. Never overwrite a candidate.

--output permits deterministic rebuilding in a new temporary directory.
The assembled example is not PAD capture or Copilot acceptance evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'copilot/versions/20260915-excel-r3'
VERSION = '20260915-excel-r4'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
PREFIX = 'catalog/acceptance/issue38/probes/'
RAW = {
    'guard': PREFIX + 'output-guard/captured-uia.robin',
    'scalar': PREFIX + 'scalar-compare/captured-full.robin',
    'matrix': PREFIX + 'matrix-write/assembled-probe-rev2.robin',
}
RESULTS = {name: PREFIX + folder + '/two-run-result.json' for name, folder in
           [('guard', 'output-guard'), ('scalar', 'scalar-compare'), ('matrix', 'matrix-write')]}


def raw_section(name):
    path = ROOT / RAW[name]
    return f'完全原文: {RAW[name]} / SHA-256 {sha(path)}\n' + path.read_bytes().decode('utf-8').rstrip('\r\n') + '\n'


CURRENT = '''Issue #38 EX02 / 20260915-excel-r4 候補の現在の範囲
これは既知命令を組み合わせる教材で、実装者probeとCopilot生成物の受入は別判定です。r1/r3の途中時点の不足・Run2未開始記録は旧版内に保存されています。この版では以下の現在の採取範囲を使います。
1. File.IfFile.Exists + ELSE/END は既存/未存在パスの各分岐を2Run確認済み。既存側は状態変数の設定だけ、ELSE内に全てのExcel起動・転記・保存・再読取り・比較を置けば、既存時に書込み経路へ入らない構成候補を作れます。END後に書込みを置きません。単独EXITや未採取の停止命令は不要です。probe自体はExcel書込みを含まず、この統合形の安全性は別に確認します。
2. DataTableをWriteCellのValueへそのまま渡す矩形転記→SaveAs→Close→読取り専用再開→各シート再選択/ReadCells→Closeの21アクションは2Run終了を観測済みです。両Runの対象12セルの保存値・保存型・位置は一致。保存ファイル480セルの旧比較には書式・寸法558差分のFAILが残り、Excelネイティブの記録属性のみの一致を全体PASSに読み替えません。
3. DataTable[0][0]のテキストと[1][1]の数値の取出し、IFの一致・不一致は2Run確認済み。数値-3と引用テキストの等価比較もMATCHでした。数値1と文字列"1"についても同じ型混同を避ける必要がありますが、このprobeで直接実測した値は-3です。等価比較は厳密な型検証ではありません。
4. 全12セルへの定数添字展開と取得値/再読取り値の変数同士の比較は既知のSET/IFを使う構成候補です。直接実測した添字は[0][0]と[1][1]のみです。行列数に合わせた添字の変更は値の置換として構成できますが、別の添字の実行済み証明を付けません。変数添字や型プロパティを発明しません。
5. 型識別アクション・厳密型比較のPAD原文は未採取です。TypedValuesで取得したという設定、等価比較、一致件数、外部openpyxlの型一致だけで、生成フロー自身が型照合したとは表示しません。型照合を要求する固定EX02でこの工程が欠ければ未達です。型不足は型不足として示し、既知の転記・保存まで一律未採取と言わず、独立して提示できる構成と区別します。依頼を読取りだけへ縮小しません。
固定する構造: 各命令名、引数名、モード、列挙値、TypedValues、FirstLineIsHeader: False、DataTable型、文字列引用/パスエスケープ、IF/ELSE/ENDと依存順。Excelインスタンスは取得元ごとに区別します。
変更可能なデータ: ローカル合成xlsxパス、存在するシート名、有限矩形の列文字列/正の行数、転記先の列/行、未存在の出力名、定義と全参照を一貫させた変数名。既存シートやパスが例と異なるだけで拒否しません。日本語別シート・別矩形のEX03全体は実行未確認です。
前提: 入力/テンプレート原本は編集せず、作業コピーは検証者がフロー前に準備。入力/テンプレート/作業コピー/出力は別パス。既存シート、有限範囲、対象矩形を準備時に確認。シート不存在などの未採取検査や未知の引数を作りません。既存出力チェックはフローにも置きます。同時書込み競合は未検証です。
要求の範囲: 値の矩形転記であり、数式・書式・コメント・画像の完全コピー機能を追加条件にしません。転記先の対象外セル・数式・代表書式の保持は必要です。追加機能を理由に値転記全体を拒否しません。結合/保護セル、日付/空白/真偽値の転記は今回の固定fixture外です。
観測を分ける: フロー内は再読取り変数と各セル等価比較（型は未証明）。独立検証は保存xlsxを閉じた状態でopenpyxlの値+型タグ+座標、対象外セル/数式/コメント、旧書式比較、Excelネイティブ属性、入力2冊/テンプレートのSHAを別々に報告。外部検査は未実装のフロー工程を代替しません。
'''


def assembled_example():
    # Construction from known syntax, not a claimed raw capture. No expected answers.
    matrix = (ROOT / RAW['matrix']).read_bytes().decode('utf-8').splitlines()
    output = next(l for l in matrix if l.startswith('Excel.SaveExcel.')).split('DocumentPath: ', 1)[1]
    guard = (ROOT / RAW['guard']).read_bytes().decode('utf-8').splitlines()[1]
    guard = guard[:guard.index('File: ') + 6] + output + ') THEN'
    lines = ["SET TransferState TO $'''NOT_STARTED'''", guard,
             "    SET TransferState TO $'''OUTPUT_EXISTS_NO_WRITE'''", 'ELSE']
    lines += ['    ' + line for line in matrix]
    lines += ["    SET ValuePositionState TO $'''MATCH'''",
              "    SET TypeState TO $'''NOT_PROVEN'''", '    SET ComparedCells TO 0']
    for number, rows, cols in [(1, 2, 3), (2, 3, 2)]:
        for row in range(rows):
            for col in range(cols):
                lines += [f'    SET SourceCell TO Data{number}[{row}][{col}]',
                          f'    SET SavedCell TO Readback{number}[{row}][{col}]',
                          '    IF SourceCell = SavedCell THEN',
                          '        Variables.IncreaseVariable Value: ComparedCells IncrementValue: 1',
                          '    ELSE', "        SET ValuePositionState TO $'''DIFFERENT'''", '    END']
    lines += ["    SET TransferState TO $'''SAVED_REOPENED_TYPE_NOT_PROVEN'''", 'END']
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
    source_evidence = {p: sha(ROOT / p) for p in [*RAW.values(), *RESULTS.values()]}
    for name in ['guard', 'scalar', 'matrix']:
        result = json.loads((ROOT / RESULTS[name]).read_bytes())
        expected = result.get('raw_sha', result.get('raw_sha256', result.get('raw_sha_before_after')))
        assert sha(ROOT / RAW[name]) == expected, name
    (destination / 'knowledge').mkdir(parents=True)
    for record in manifest['source_files']:
        p = record['path']
        content = (BASE / p).read_bytes().decode('utf-8')
        if Path(p).name.startswith(('PAD-Robin-00-', 'PAD-Robin-04-', 'PAD-Robin-06-')):
            content = content.split('過去候補の記録（現在の能力は末尾r3追補を参照）:', 1)[0].rstrip() + '\n\n'
            content += CURRENT
            content += "採取済み独立シート選択:\nExcel.SetActiveWorksheet.ActivateWorksheetByName Instance: ExcelInstance Name: $'''Sheet1'''\n"
            content += (ROOT / (PREFIX + 'matrix-write/captured-action.robin')).read_bytes().decode('utf-8') + '\n'
        if Path(p).name.startswith(('PAD-Robin-02-', 'PAD-Robin-06-')):
            content += '\nEX02補助probeの完全原文（実装者/PAD UI由来、Copilot由来ではない）\n'
            content += raw_section('guard') + raw_section('scalar')
            content += '分岐は書込み経路をELSEに閉じ込める参照用。等価比較は型識別ではありません。\n'
        if Path(p).name.startswith('PAD-Robin-04-'):
            content += '\n21アクションの実測済み矩形転記・保存・再読取り原文（型比較は含まない）\n' + raw_section('matrix')
        if Path(p).name.startswith('PAD-Robin-06-'):
            content += '\nEX02統合構成例（実装者による組立、未実行。採取原文ではない）\n'
            content += '出力存在分岐内へ上記21アクションを配置し、12セルの値・位置を等価比較します。型検査を含まないため固定EX02の完成例ではありません。パスは実測probeのものなので実依頼に合わせて一貫して置換します。型不足を隠す完了マーカーは置きません。\n'
            content += assembled_example()
        (destination / p).write_bytes(content.encode('utf-8'))
    original = (BASE / 'agent-instructions.txt').read_bytes().decode('utf-8')
    prefix = original.split('【Excel値転記・', 1)[0]
    instructions = prefix + '''【Excel値転記・20260915-excel-r4候補】
標準入力は同版の指示全文＋bundle実添付です。20260913eや旧候補の受入は継承しません。00/04/06の「EX02 / 20260915-excel-r4」の現在の採取範囲を参照します。
命令名・引数名・モード・列挙値・型・引用/エスケープ・依存構造は固定し、パス、既存シート名、有限矩形、転記先、出力名と変数の一貫した定義/参照は変更可能なデータとして区別します。サンプルとデータが違うだけで一律拒否しません。変更条件の実測有無を明記します。
シート切替は独立した採取済みアクション、矩形転記はDataTable指定WriteCellです。入力は読取り専用、テンプレートは原本からの作業コピー、出力は原本/入力/作業コピーと異なる新規xlsx。原本のシートを手動選択して保存させません。CSVを1セルへ書く方法で代用しません。
出力存在分岐の完全原文は02/06にあります。既存時は状態を示すだけ、ELSE内へ全書込み経路を置きます。END後へSaveAsを漏らさず、未採取EXIT・未知の停止命令を発明しません。シート/範囲/非同一パスを準備時に確認し、衝突時は書込み前に停止します。未知の安全引数は追加しません。
保存→クローズ→読取り専用再開→両シートの対象矩形再取得→照合→クローズを含めます。固定依頼を黙って読取りだけへ縮小せず、既知工程・不足工程・追加採取を分けます。完成組合せの実測がまだないことと構文未採取を混同しません。
等価比較は数値と文字列を同じと判定することがあり、厳密な型検証ではありません。型識別原文は未採取です。値・位置の比較までの安全な候補を出す場合は型工程が未実装で依頼全体未達と明示します。TypedValues設定や外部検査を、フロー自身による型照合の代わりにしません。未採取GetType等を捏造しません。
全対象セルの値・型・位置、対象外セル・数式・代表書式、原本SHAを区別して照合します。書式558差分FAILとExcelネイティブ限定一致は両方保持します。値のみの依頼へ数式/書式/コメント完全コピーなどの新たな必須条件を追加しません。
'''
    (destination / 'agent-instructions.txt').write_bytes(instructions.encode('utf-8'))
    subprocess.run(['pwsh', '-NoProfile', '-File', str(ROOT / 'tools/Build-KnowledgeBundle.ps1'),
                    '-Root', str(destination), '-KnowledgeDirectory', 'knowledge',
                    '-OutputPath', 'knowledge/PAD-Robin-Knowledge-Bundle.txt'], check=True)
    manifest.update(version=VERSION, status='FROZEN_CANDIDATE_TYPE_GAP_NOT_ACCEPTED',
                    base_candidate='20260915-excel-r3', base_commit='d0bd39699fcc92773ef0238f29701f9e310a7693',
                    instruction_sha256=sha(destination / 'agent-instructions.txt'),
                    instruction_utf16=len(instructions.encode('utf-16-le')) // 2,
                    bundle_sha256=sha(destination / manifest['bundle_path']),
                    evidence_inputs=source_evidence,
                    builder='tools/Build-Issue38Ex02Candidate.py')
    assert manifest['instruction_utf16'] <= 8000
    for record in manifest['source_files']:
        record.update(sha256=sha(destination / record['path']), bytes=(destination / record['path']).stat().st_size)
    manifest['evidence'].update(copilot='NOT_RUN_AT_FREEZE', pad='PRIMITIVES_REUSED_NOT_CANDIDATE_ACCEPTANCE',
                               matrix_write='Two probe runs completed; 12 target cells match; 558 XML differences retained',
                               type_comparison='NOT_CAPTURED_NOT_PROVEN')
    (destination / 'manifest.json').write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({k: manifest[k] for k in ['version', 'instruction_utf16', 'instruction_sha256', 'bundle_sha256']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'copilot/versions' / VERSION)
    build(parser.parse_args().output)
