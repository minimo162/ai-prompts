# Issue #5 引き継ぎ（2026-09-06）

状態は **実装済みPoC・実機ゲート未完了**。Issue #5を閉じず、残りの検証と必要な修正を続ける。今回のマージはユーザーが指定した途中成果の保存であり、全要件の受入完了ではない。

## 22:04 JSTの期限判定修正

**22:13 JST追記**: 修正後45f版の固定PAD→実AiCall20秒期限はPASS。`.work/gate1-deadline-fixed-f8415abdc9ca4d43bda0859f9f1834f3/`、job `2f91a9786c704c0398fc372f9f0b8eec`、result SHA `fa7ead8659f045bf0181fccab174e03153bc4335e61c29bd4d4a4789d78515b5`。送信クリック応答確認後の製品記録 `has_sent=true`、子failed/timeout、制御failed/AICALL_timeout、開始ID一致、後続成果物/完了マーカーなし。元Main・既存ファイル・ページ・owner・clipboard復元成功。実M365送信後の期限切れを確認できた。残る作業は最新ソースの正常業務通し、実M365送信後中止、native Save失敗、社内PC/別利用者の受入とGitHub公開。過去のクリップボード例外は根本原因未確定のまま保持。

**22:10 JST更新**: 応答制御137件とCopilot302件PASS。通常更新 `8f340820b3654b10b060042a39d6d8b8` もPASSし、通常キャッシュはApp `45f9600171f830be7a1f010984e80ee85946b6d05c9e8bdeda3985b6662d4c7d` / release `0.1.0-6079e7a56ebd98ad6365deb45729ea8a3adbda51b54bd51c1a7ab80996d8ff53` に切替済み。新server PID25376 / port50142 / start UTC `2026-09-06T13:10:15.6866050Z`。既存ファイル/設定/PAD owner保持。

途中成果はローカル `d122e7868087aa10066cc16774c9222265c78ddb` に保存。a743版の3ファイルZIPは `.work/distributions/issue-5-poc-d122e78-f43e0972cbe44f81a94240364914cb61/`、ZIP SHA `7c814f92f0b5d3dee717940692bab67dcdc2c2cd266d95020be031d39f4b16ab`。GitHub公開・社内PC検証は未実施。

その後の20秒実試行 `47832fcd0a164b5ead7101fbe23f84ca` は送信予約後にinvalid_responseとなりpartial。後続処理なし、元Main/ファイル/ページ/clipboard復元成功。失敗後の独立2読取りでは有効なV1訳文を確認したが、期限内の完成を証明しない。途中の不完全フレームのエラーを後の有効な回答へ引き継ぐ誤分類は別の回帰で再現した。各snapshotでエラー判定を更新するApp `45f9600171f830be7a1f010984e80ee85946b6d05c9e8bdeda3985b6662d4c7d` は応答制御137件PASS。安定確認3回・全体期限・送信1回は維持。通常キャッシュは上記22:10 JSTの更新で45f版へ切替済み。更新wrapperは `.work/deadlinefix-479e93e05eba4b1b82ce05fe621dbda5/` にあり、この更新のPrepare/Executeは消費済みのため再使用しない。

## 21:42 JSTの再開情報（以下の履歴より優先）

**21:48 JST追記**: 実PAD→実AiCall子プロセスで、プロバイダー関数だけに拒否・空回答・応答時中止を注入した3ケースがすべてPASS。`.work/gate1-pad-provider-5c7e819ae3cb43a0bcafcd6340c46a38/` の `refusal` / `empty` / `cancelled`。制御結果はそれぞれ `failed/AICALL_refusal`、`failed/AICALL_empty_result`、`cancelled/CANCELLED`、子結果も対応する型を保持。全ケース実行1回、開始ID一致、成功本文/後続成果物/完了マーカーなし、中止ケースの停止操作1回。元Mainへの復元・保存、owner/既存ファイル/既存ページ/クリップボード保全成功。子PIDとfixture App/要求IDの記録で親関数だけの注入でないことを確認。実M365が拒否や空回答を生成した検証ではない。残る範囲はnative Save失敗、送信後期限/中止、別利用者・社内PCでの受入と最新配布物の公開。先行クリップボード例外の原因は未確定。

- 現在のApp SHAは `a743aecc068eaeec9a081e41e0a78a0c6bea0ca1d8aceea6f6ffbf638662f0cf`。通常更新 `9c583bd4482645c1a6e5a12bab06d7a1` はPASS。releaseは `0.1.0-52b61a88923fd3fdc07d62b6db5cea9b3de33a2398eb74507d101aefdda3dc04`、server PID35556 / port59995 / start UTC `2026-09-06T12:22:10.2375112Z`。再開時に現物を再確認する。
- PADコピーはSelect All/Copyを各1回だけ送り、固定150ms後の1読取りから、2秒以内の結果待ちへ変更した。コピー前と待機中の中止を確認し、空白だけの結果を受理しない。以前の `PAD_COPY` の原因を遅延だけと断定しない。Planner指示に残った「second fence」を現在のRobin sectionへ訂正した。core147/PAD335 PASS。
- `tests/Test-AiCallProviderFailure.ps1` を追加。実PS5子プロセス内のプロバイダー関数だけを差し替え、拒否・空回答・期限・応答時中止の21件PASS。ASTによる差し戻し一致でその他の製品ソースが同一と確認した。証拠 `.work/aicall-provider-fault-36663711ffe4491287597127c959988d/validation.json`。この検査単独では実PAD/M365の証拠ではない。
- **固定PAD→実AiCallのタイムアウト検証PASS**。`.work/gate1-timeout-recorded-173b32b027454db0b426cae231f87508/`、job `cc2f5ab033ba44178c5882cbd188c240`。実行ボタン1回、制御戻り値 `failed/AICALL_timeout`、子結果 `failed/timeout`、入力1/出力0、開始ID一致、成功本文・後続成果物・完了マーカーなし。元Mainへ貼戻し/保存各1回・復元時実行0、owner/既存ファイル/既存ページ/クリップボード保全成功。期限は5秒で**Copilot送信予約前**に切れており、送信後の回答待ちタイムアウトと称しない。
- 直前の `.work/gate1-focused-d147709b24504929b00e19503480b345/` は同じ子timeoutと後続停止、Main/ファイル保全を確認したが、クリップボード例外で制御戻り値保存・クリップボード復元が未確認となりpartial。読取専用の `postrun-verification.json` は `AICALL_timeout`、開始ID一致、成果物なし、Main ready/error0を確認。元resultを書き換えていない。後続helperでは制御戻り値をクリップボード診断より前に保存した。クリップボード例外の根本原因は未確定。
- PAD335の再検査を実機helperと重ねた1回は、実機側が保持する名前付きmutexとの競合でbusyゲートのアサートに失敗した。実機helper終了後の単独再実行は335 PASS。これ以降、PADテストと実機PAD検証を並行しない。

## 20:16 JSTの再開情報（履歴）

- 作業ソースと通常配布App SHAは `f9391133d2c52239de68a96d4f3a4a03b060f10967069d95ea2dab38c1474e45`。通常server PID356 / port60007 / start UTC `2026-09-06T11:08:31.5979449Z`。releaseは `0.1.0-57bf89e2c02486df7bca084fc6e77df4d7262a56a471e4ad15e1ab5ff36901c3`。通常更新 `5cdd478fea9c411284b1095796a8b54d` はPASS。
- Planner V2は **1つの物理フェンス内のメタデータ/Robinの2セクション** を既定出力にした。明示マーカーで分離し、旧2フェンスの読取りも維持。AiCallはV1のまま。単一フェンスの実長文検証 `bb4d6143aec74b3f872b6232dd94bdfd` は7794文字・26行・空行1・24 Writeの完全一致、独立2読取り・保全成功、送信1/PAD0。result SHA `c1614af19c3cefe75ac29114af3e68bf100a41f26ca70657a0a098eb8bf3a17f`。
- 入力準備で複数の確認が共通15秒枠を消費する問題を計測・再現し、各確認の枠と不変の要求全体期限を分けた。低速準備・全体期限・単一V2→V1→単一V2を含む応答制御134件PASS。PAD実行中のMain表示不一致は、20秒以内の完全な再観測でのみ回復し、持続すればunknown。PAD331件PASS。
- DONE成果物パスはWindowsの `GetFullPath` でパス構文を正規化してから、観測済みの正確なパス・現物hash・全文確認状態と照合する。Robinや業務本文は変更しない。`needs_review` の分類結果も候補ラベルに限定した。core146件PASS。
- 正しいDONEなのに「More表示あり・全行が既に枠内」の状態を拒否していた。実測は11行、CSS maxHeight300px、padding込みclientHeight=scrollHeight=320px。V2メタデータ始端を持つ、この完全な表示状態に対応しDOM893件PASS。元の実回答を再送/展開せず2回読んでDONEと成果物を検証できた（`.work/completion-7009a7601b87455a99d3bd9dedfc79b9/done-fitted-reader.json`）。元jobはfailedのまま。
- **最新V2業務通し検証はPASS**。`.work/fitted-d08798810a234ce0af71690cbf310519/classification/` のsession `ee182d3e0c9c4e73a2be8cfa43a6cf93` / job `6e8eea67fc004355b13e76f7d8016c1a` は実HTML開始1回→V2 ACT→PAD内V1分類review→分岐と下書き→実観測を受けたV2 ACT→別PAD実行→V2 DONEまで完了した。PAD2回/AiCall1回、異なる生成Robin、4応答の独立2読取り、元ファイル/owner/全タブ/attempt帰属の保全、worker終了、最終UI一致がすべてPASS。result SHA `877c11492e2473fd79194c074fee392f8e786c13dbd963df5a6fa832ba864a16`。
- 最終83バイトの `final-review.txt` は下書きとSHA `271fe047a97061f8eb4f3f2fd9a14d99973059fed1714a4256272da4ce2b4a5d` が一致。元入力80バイトとの差はUTF-8 BOMで、デコード後は末尾LFを含めOrdinal完全一致。完了画面 `complete-ui-full.png` を目視し、完了状態・停止無効・回答・正規化済み成果物パスを確認。スクリーンショットSHA `e29a54fc4bd5a98bf2041cb80dc32cb7dbc55dd99b6df45a54a0b247b16e0f33`。同sessionへ検証済み最終ファイルもコピーした。
- 最新検証後owner SHAは `1c4be84229f793e0dd3335a95df111c7ab0385c57cc2fdf37bc17c48a8ad0ee2`。現在Mainは上記2回目の成功フロー。再開時はこの所有記録と今回のsubmittedを照合する。古いowner/pid/headに固定されたhelperや消費済みclaimを再実行しない。

途中結果の保存先: `.work/pastewait-db7901e78f01420c9451367b4080fbc6/`（実AiCall timeoutとPAD runtime_errorの読取り、旧Main復旧、入力準備計測）、`.work/readiness-17c8799f71814fbdbf8ac3c0ff08bc2a/`（入力準備修正）、`.work/single-fence-803c838f4ccf4d90b59dd1ed627f802a/`（新形式・パス照合の切分け）、`.work/completion-7009a7601b87455a99d3bd9dedfc79b9/`（正しいDONEの表示状態切分け）。失敗/unknownを成功へ書き換えていない。

追加の `tests/Test-AiCallProcess.ps1` は実PS5子プロセス5回による14件PASS。空入力・開始前中止・再入・別Appのcontextを送信前に拒否する検査で、PAD途中の全異常系やプロバイダーの空回答の証拠ではない。

次の作業はAiCallの拒否/空回答/期限/実行中中止が同じPADに戻る異常系の不足分、native Save失敗、その他ゲートの監査、GitHub経由で社内PCへ渡す最新版パッケージと別PC検証。ここでのV2正常業務成功はIssue全体の受入完了ではない。GitHub Actionsは未設定で、新しいPR公開/マージは未実施。

## 配布先の確定事項と17:50 JSTの更新

**18:06 JST追記**: 現在の作業ソースAppは `0d812b25e8371e89c241f098538406b67292398f1425234583750f216221f3d0`。下記の通常配布 `6119f110…` に、貼り付け後はアクションが実際に存在するReady/idle/error0の連続2観測を要求する `Wait-AgentPadEditable -RequireActions` を追加した。空のReadyではクリップボード読戻しへ進まず、期限後は `PAD_PASTE` で停止する。PAD325/core138 PASSだが、この追加条件は未配布・実機未検証。

V2分類 `3786d28baa0f4bcead05d685065e1ab9` / job `3236f6a3662a4769b6747662de125cb3` は、実HTML開始→V2 ACT→生成PAD→V1 AiCall分類review→分岐・83バイトの下書き保存→実観測を受けた次のV2 ACTまで進んだ。2回目の反映が `PAD_COPY` で停止し、ASK_USERへ移った。2回目のsubmittedはあるが開始/完了マーカーはなく、最終ファイルは未作成。元結果はpartialのまま保持。旧ファイル/owner/タブ保全はすべて通過した。

読取診断ではMainが実際に空で、Ctrl+A/C各1回でもsentinelのまま、owner不変、clipboard復元一致だった。元成功Mainを実行せず1回貼り戻し、キー送出から66msで戻り、2144ms時点の最初の状態観測でアクション存在/clipboard不変を確認した。これだけで元失敗がタイミングだけに由来すると断定しない。診断の保存前に空CancelPathによる補助エラーがあったため、新しい保存専用helperで保存1・全文コピー2・owner一致・エラー0まで確認した（`finalize-main.json`）。現在owner SHA `2c078c05fde96fd36c21aa1c3acf46a5d16ed9ddc8350ec3483bf2d3aa966424`、Main比較SHA `cd4ca140f56d90c2a88b95751ac3aec609cdbdf742b470d7f956ea768c39ab50`。ジョブは実UI停止1回でcancelled、worker終了済み。次の検証はこの新ownerを基準にする。

記録は `.work/resume-279042c639354e21a630074e81e426b7/`。過去の失敗タブ2件の閉鎖スクリプトは自動承認レビューに拒否され未実行。タブを閉じる再試行は行っていない。旧 `2cbe52e2…` のZIP候補は `.work/distributions/issue-5-poc-4243688-9777d2c6bdba4b16a7e8e79f92f7c0d9/` に保持し、最新修正の配布物として使わない。

ユーザーから、現在の `\\localhost\AiPromptsAgentPoC$` は削除・新規作成を含めて作り替え可能なテスト共有で、実際の配布は **GitHub → 社内PC → 社内共有フォルダー** と確認された。以前のテストHTML所有者の復元を受入条件や継続の障害にしない。失敗証拠は保持するが、社内共有の設定をこのテスト環境から推定しない。

最新Appは `6119f11066b5f3e1b5e60fe1885df6a7e8de8a6dc1a3ec7e8c0c44e5db0ca144`。通常更新 `59c2d1e16964416fa05e015c33ae4ce0` はPASS、server PID12936 / port61417 / start UTC `2026-09-06T08:50:38.5631842Z`。releaseは `0.1.0-31da91be164f2f207cf1f1796494e35503066b341c9f12049267aa270982a8eb`。既存ファイルとPAD所有記録を保持した。これは後述の旧cache状態を更新する。

変更はCopilotの送信ボタン判定。実分類 `9557e7cdab414df9989eee35ca2ab14f` は、非モーダルの満足度アンケートにも有効な「送信」ボタンがあり、ページ全体から探す判定が2件となって送信前に停止した。既知のチャット入力領域にあるsubmitボタンへ限定し、アンケートを送信しない回帰を追加。旧版で回帰失敗、新版でDOM870/core138/Copilot302 PASS。実画面の読取りでも、2ボタンが存在したまま正しい送信先を一意に検出し、入力SHA不変を確認した。元失敗要求のattemptは消費済みで再送しない。

## 17:27 JSTの再開結果（履歴）

- 作業ブランチは `codex/issue-5-resume-validation`、開始HEADは `424368831c7f5d60c23c3587814451f111afd9bd`。Issue本文と全コメント1件を再読した。
- **最新ソースによるV2長文・空行の実取得は成功**。診断 `8cdcfab0b1fa425d889a30c42a118d39` は1 Read＋空行1＋24 Write、7794文字・26行を期待本文と完全一致で取得。実送信1・再送0・PAD0、独立2回のDOM/assistant読戻し一致、既存401ファイル・owner・ページ保全成功。結果SHAは `0bd7f5edbeb5c243732cbb6ca11461652e7c00d57c30ecb679c4f0d06555885e`。
- これは通常Explorerから**最新ソースの関数を直接読み込んだ取得診断**。通常キャッシュは旧 `0fc60b78…` のまま別にハッシュ固定した。最新版配布後のHTML→PAD業務受入とは数えない。証拠は `.work/resume-279042c639354e21a630074e81e426b7/source-retrieval/`。
- **共有更新は未合格**。公開診断 `76e4cca698984977a7b20306db277fa5` で `File.Replace` が旧HTMLの別アカウント所有者/ACLを変更し、App/HTML更新後・CMD更新前に停止した。3ファイル本文は固定バックアップから旧版へ復元し、全SHA一致を確認。通常更新・サーバー再起動は実施していない。
- **残る共有メタデータ差分**: `index.html` の元所有者/グループ/ACLを戻す `Set-Acl` は「The security identifier is not allowed to be the owner of this object」で失敗。共有設定を緩めたり権限を迂回したりしていない。失敗結果、旧バックアップと `share-recovery.json` を保持。旧公開helperはこの所有者差を置換前に検出できないため、そのまま再実行しない。元メタデータの復元と、全変更ファイルの所有者/ACLを事前確認する公開手順が先に必要。
- `tests/Test-App.ps1` と `tests/Test-CopilotPlannerV2.ps1` の既定ソースパス解決をparam評価から本体へ移し、PS5.1でREADMEの引数省略コマンドが失敗する問題を修正。core138、V2解析108、V2/V1応答制御118、Copilot302、PAD320、隔離Edge DOM859、launcher18、実localhost HTTP検証がPASS。Copilot/PADのモック検査を実機業務の証拠にはしない。

この時点では共有メタデータの復元を次作業としていたが、その後のユーザー指示と上記更新で扱いを変更した。V2分類業務、AiCall失敗実経路・native Save失敗・別PCの未検証を継続する。今回の取得成功で以前の失敗結果を書き換えない。

## 再開時に読むもの

1. GitHub Issue #5の本文と全コメント。
2. `README.md` と `docs/issue-5-validation.md`。後者は時刻付きの累積記録で、古い時点の状態を現在の状態と混同しない。
3. 現在のGit状態、通常環境のキャッシュ、サーバー、専用Edge、PADの実状態。下記PID等は観測時点の値であり、再開時に確認する。

作業ディレクトリは `C:\Users\yuuki\ai-prompts`、originは `https://github.com/minimo162/ai-prompts.git`。個人用Obsidianの `Codex Memory` にも検証ログがある。

## 実装と今回の確認

- 配布ソースは `業務エージェント.cmd`、`App.ps1`、`index.html` の3つ。共有からローカルへの更新、HTML UI、Planner、PAD制御、フロー内AiCall、観測・再計画を実装。
- Planner V2はメタデータJSONと生Robinの2コードブロック。空行のみ要求ID付きの `AGENT_EMPTY_V2` で搬送し、完全一致する目印を復号する。通常の空白やバックスラッシュを補修しない。AiCallは既存JsonPartsV1を維持。
- 旧版で実分類1回、PAD2回、観測を受けた再計画、DONEと最終成果物を確認済み。ただし元の検証結果にはページ保全の問題でpartialが残る。V2業務の証明には流用しない。
- 直近のソースはV2生成指示でフェンスを閉じる位置を明記したもの。App SHA256は `2cbe52e24c9f3040c548011439eee6e8d6c43e64613e0d5a1a27498899d4925e`。core138、V2解析108、V2/V1応答制御118チェックPASS。これらは実Copilot/PAD受入ではない。
- CI設定はない。過去のDOM859、Copilot302、PAD320等は検証記録に記載した各候補時点の証拠であり、最終ソース全体の新規実行と称しない。

## 直近の実回答失敗と次の作業

長文・空行の製品応答ループ検証は1 Read・空行・24 Writeを要求した。セッション `bd1e00f891dc4ea88d4e8b63b00bdc5c` は `RESPONSE_INVALID` で停止し、既存ファイル・owner・ページ保全は成功。再送0、PAD操作0。DOM上のメタデータ終端後に単独バッククォートの追加行が実在し、正しいV2応答として受理されなかった。

同一PCの証拠は以下。`.work` はGit管理外なので別PCには存在しない。

```text
.work/gate3/planner-v2-live-edge12348/sessions/bd1e00f891dc4ea88d4e8b63b00bdc5c/
  result.json
  postfailure-dom.json
  postfailure-snapshot.json
  after-preservation.json
```

取得側が追加した文字ではないが、モデル生成とCopilot表示変換のどちらが発生源かは未確定。終端検査を緩和せず生成指示を明確化し、当該追加行を拒否する回帰テストを追加した。**この指示修正は未配布・実機未検証**。

次は現在のソース・HEAD・プロセス等に合わせて新しい検証準備を作り、修正版を通常環境へ反映した上で、長文・空行取得とV2分類業務を確認する。既存のfrozen helperや失敗結果を上書きせず、実行済みclaimを再利用しない。旧helperはHEAD・App SHA・PIDに固定されており、そのままmainから実行できない。

分類の検証コピー `.work/gate45/planner-v2-classification-edge12348/` は事前62チェックPASS、実Prepare/Executeは未実施。実HTML開始→V2 ACT→フロー内V1分類→V2 ACT→V2 DONEを観測する設計。

## 通常環境と検証上の注意

- 通常Home: `C:\Users\yuuki\AppData\Local\AiPromptsAgent`。
- 配布済みApp SHA: `0fc60b7840dec296b4da5cf25910a959186a194ba2c3639d451f9fae53e630d9`。キャッシュ版: `0.1.0-d2e3d4a1cd3ac5a6ae78c436e4c76bc0f780ac3719be463ae3c01005da64aef4`。
- 観測時のサーバーPID976・port59062、開始UTC `2026-09-06T07:47:42.4260152Z`。専用Edgeは終了した18096から12348へ復旧しREADYを確認した。PAD PID25656、専用「無題」Main。
- 共有は `\\localhost\AiPromptsAgentPoC$`、実体 `.work/shares/AiPromptsAgentPoC`。同一PCのUNC検証を別PC検証としない。
- Codexのパッケージ環境とExplorer/PADの通常環境ではLocalAppDataの実体が異なる。通常実経路はExplorer経由のnative PS5.1 STAで検証してきた。既存証跡の実体確認を参照し、仮想化されたパスのファイルを通常側の証明にしない。
- 検証タブを増やしすぎない。既存のUI・サインインタブを再利用し、製品がジョブ用に作る検証タブは最終証跡保存後に閉じる。直近の失敗タブも保存後に閉じた。ユーザーの他のタブは操作しない。

## 未完了の範囲

- 修正後V2の長文・空行実取得、生成AiCallを含むV2業務の通し確認。
- AiCallの拒否・空結果・タイムアウト・中止が同じPADフローへ戻る実経路の不足分。親プロセスの関数差し替えは子AiCallの障害注入にならない。
- 保存失敗検証はSave呼出し境界の制御例外であり、ネイティブSave失敗の証明ではない。
- ASK_USER/BLOCKED等を含むIssueの各ゲートと成功条件の再監査。
- 別利用者・別PCの導入・更新・実行検証。過去の配布ZIPは一意名のまま保持する。

## Codex設定の別件

ユーザーの依頼で `C:\Users\yuuki\.codex\config.toml` に以下を設定済み。TOMLとCLI読込みを確認し、元ファイルのバックアップを保持。Gitの配布物には含まれない。現在の会話への即時反映や実際の100万トークン利用は確認していない。

```toml
model_context_window = 1000000
model_auto_compact_token_limit = 900000

[features]
context_management = { experimental_mode = true }
```

実ファイルの既存features等を省略した説明例であり、設定全文をこの例で上書きしない。
