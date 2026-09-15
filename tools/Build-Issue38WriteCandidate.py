"""Create a separate candidate from frozen r1; never promote probe evidence to acceptance."""
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERSION = '20260915-excel-r3'
DEST = ROOT / 'copilot/versions' / VERSION
BASE = ROOT / 'copilot/versions/20260915-excel-r1'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
if DEST.exists():
    raise SystemExit('Candidate exists; do not overwrite a sealed version')
manifest = json.loads((BASE / 'manifest.json').read_text(encoding='utf-8'))
for record in manifest['source_files']:
    assert sha(BASE / record['path']) == record['sha256']
assert sha(BASE / manifest['instruction_path']) == manifest['instruction_sha256']
raw_path = ROOT / 'catalog/acceptance/issue38/probes/matrix-write/captured-action.robin'
assert sha(raw_path) == '39ceb68d225f61cf87e8c4c173fe3993699d52ff9e23b0457cb614945e423207'
raw = raw_path.read_text(encoding='utf-8').rstrip('\n')
appendix = '''
Issue #38 矩形値書込み追補 / 20260915-excel-r3候補
以下はPAD画面からコピーした完全な原文。入力ExcelInstanceは先に起動した作業用ブック、ExcelDataはReadCellsのTypedValues / FirstLineIsHeader: Falseで得るDataTable。
''' + raw + '''
固定構造: Excel.WriteToExcel.WriteCell / Instance / Value / Column / Row。ValueにDataTable変数をそのまま渡す。文字列化やCSV化をしない。Columnは引用された列文字列、Rowは正の整数。呼出し前にSetActiveWorksheet.ActivateWorksheetByNameで作業用ブックの既存シートを明示選択する。
採取元: catalog/acceptance/issue38/probes/matrix-write/captured-action.robin。SHA-256 39ceb68d225f61cf87e8c4c173fe3993699d52ff9e23b0457cb614945e423207。単独採取時は変数が未定義であり、単独実行をPASSにしていない。
組合せの実測: 別の専用PADフローに21アクションを貼付け・保存・再コピーしSHA一致。読取り専用の2入力（初期表示Decoy）からSource AのB2:D3、Source BのA3:B5を読み、作業コピーのTarget AのC4、Target BのB3へDataTableを書いた。別名xlsx出力を閉じ再開し、両対象矩形をReadCellsで再取得。保存xlsxの全12対象セルで文字列・数値（0、負数、小数）の値・型・位置に不一致なし。これによりDataTable指定を「未採取」として拒否しない。
未完了: 実行補助は120秒で終了を観測できず、Start無効/Stop有効が残った。全域ファイル比較は書式・寸法差分でFAIL。Excel読取り専用による代表9セルと指定寸法の追加診断は一致したが、全域の代替証明ではない。Run2未開始。実装AIの組立probeであり、通常Copilot生成・EX01〜EX05の受入はNOT_RUN。転記全体が検証済みとは記載しない。
変更可能データ: ローカル合成xlsxパス、既存シート名、固定矩形、転記開始列/行、未存在の出力名。変数名の定義と全参照を一貫して置換する。サンプルと異なるだけで構文未採取としない。日本語シート名や別矩形を含むEX03条件は実機未検証として提示可能な候補と実測を区別する。未知の引用・特殊文字、日付/空白/真偽値、結合/保護セル、数式・書式等の完全コピーは本probeの範囲外。
安全条件: 入力は読取り専用。テンプレート原本を編集せず事前に新しい作業コピーを用意する。出力は入力・原本・作業コピーと異なる未存在xlsx。シート存在・有効範囲・転記矩形・衝突を事前確認し、未確認なら依存処理を停止する。SaveAs自体に安全停止を期待しない。未知の検査命令を捏造しない。作業コピー準備や安全照合をフロー外で行う場合は明記し、全自動実装済みにしない。
全体順序: 事前確認/作業コピー準備→各入力を読取り専用起動→各指定シート選択→ReadCells→各入力を保存せず閉じる→作業コピー起動→各転記先シート選択→上記WriteCellへDataTable指定→新規xlsxへSaveAs→閉じる→出力を読取り専用再開→各シート選択/各矩形ReadCells→閉じる→全値・型・位置と対象外部分・原本SHAを独立照合。再読取り変数のプレビューだけでは照合完了にしない。
'''
(DEST / 'knowledge').mkdir(parents=True)
for record in manifest['source_files']:
    source = BASE / record['path']
    content = source.read_bytes().decode('utf-8')
    if source.name.startswith(('PAD-Robin-00-', 'PAD-Robin-04-', 'PAD-Robin-06-')):
        # r1 appendix remains explicitly historical, so its missing-operation notes cannot override r2.
        content = content.replace('Issue #38 Excel追補 / 20260915-excel-r1', '過去候補の記録（現在の能力は末尾r3追補を参照）: Issue #38 Excel追補 / 20260915-excel-r1')
        content += '\n' + appendix
    (DEST / record['path']).write_bytes(content.encode('utf-8'))
instruction = (BASE / 'agent-instructions.txt').read_bytes().decode('utf-8')
instruction = instruction.replace('20260915-excel-r1候補', VERSION + '候補')
instruction = instruction.replace('新版のExcel追補で明記した矩形書込み/型付きセル転記の不足を推測で埋めません。', '矩形書込みは末尾r3追補の採取済みDataTable指定WriteCellを使用できます。古いr1追補の未採取記録は現在の拒否理由にしません。Run1値照合と全体未受入を分け、未知の構文・型・安全検査を推測で埋めません。')
(DEST / 'agent-instructions.txt').write_bytes(instruction.encode('utf-8'))
assert len(instruction.encode('utf-16-le')) // 2 <= 8000
subprocess.run(['pwsh', '-NoProfile', '-File', str(ROOT / 'tools/Build-KnowledgeBundle.ps1'), '-Root', str(DEST), '-KnowledgeDirectory', 'knowledge', '-OutputPath', 'knowledge/PAD-Robin-Knowledge-Bundle.txt'], check=True)
manifest.update(version=VERSION, status='CANDIDATE_PRIMITIVE_CAPTURED_ACCEPTANCE_NOT_RUN', base_candidate='20260915-excel-r1', instruction_sha256=sha(DEST/'agent-instructions.txt'), instruction_utf16=len(instruction.encode('utf-16-le'))//2, bundle_sha256=sha(DEST/manifest['bundle_path']))
for record in manifest['source_files']:
    record.update(sha256=sha(DEST/record['path']), bytes=(DEST/record['path']).stat().st_size)
manifest['evidence'].update(matrix_write='CAPTURED; 12 target values/types/positions match; completion unconfirmed; full oracle FAIL; Run2 not started', matrix_write_sha256=sha(raw_path), copilot='NOT_RUN', pad='PRIMITIVE_ONLY_NOT_ACCEPTANCE')
(DEST/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'version':VERSION,'instruction_sha256':manifest['instruction_sha256'],'bundle_sha256':manifest['bundle_sha256']},ensure_ascii=False))
