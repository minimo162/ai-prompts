# Issue #5 検証記録

2026-09-06 / 状態: **partial — 実機ゲート未完了**。

GitHubへの途中成果保存: [ドラフトPR #7](https://github.com/minimo162/ai-prompts/pull/7)、[ドラフトRelease](https://github.com/minimo162/ai-prompts/releases/tag/untagged-9f3591bbed1fcc24cfb2) を作成。Release対象は `1c981c6dd53d75b2c8f11659c0364820fb0cf349`、配布Appは検証済み45f版。3ファイルZIP、manifest、社内PC確認手順を添付し、GitHubからダウンロードした全添付とZIP内3entryのSHA一致を確認した。ZIP SHA `12ae88a7dca77f010810cf0c475cde87a4edac22f62af4a979a13119e706ca54`。公開版や他PC合格とは扱わない。PR check一覧は空で、GitHub Actionsは未設定。IssueはOPEN、mainへのマージは未実施。

同日22:29 JST、**実M365送信後の中止もPASS**。`.work/gate1-postsend-cancel-965937aac9a2404bb769858d2e1c71e4/`、job `6f2c544af5b841d8b3eb6fddea52db2a`、result SHA `f2609fc66750e46796d0e515a766e64001845899683df8db31143edd68079e4e`。固定PADの実行1回後、同版Appを読む別監視プロセスが開始ID・AiCall claim・送信クリック応答後のhas_sentを確認して中止ファイルをCreateNewで1回作成した。製品PAD停止1回、子結果cancelled/入力1/出力0、制御cancelled/CANCELLED、成功本文・後続成果物・完了マーカーなし。元Main復元・保存各1回/復元実行0、既存ファイル/ページ/owner/clipboard保全、監視・子・検証プロセス終了を確認。プロバイダー関数の差替えなし。実UI停止ボタンの押下とは区別する。

同日22:24 JST、**最新App45f版の正常業務通しはPASS**。session `.work/normal45f-2eac8de5df4f482ab234974c189c7b99/classify-sessions/d131679abeca4f28ba7bf44f03c0e9da/` / job `7b289291994e47699a3aedb81721e374`。実HTML開始1/HTTP200→V2 ACT→実PAD内V1分類review→下書き→観測を受けた別V2 ACT→実PAD2回目→V2 DONE。result SHA `d54d4c15eda3c3641976aa140cce7850e5d6f7749fb7c08ed90b96bdb5f80f29`。PAD2/AiCall1、異なる生成Robin、4応答の独立2読取り、旧ファイル/owner/タブ/attempt帰属保全、worker終了、最終UI一致が合格。最終ファイル83バイト/SHA `271fe047a97061f8eb4f3f2fd9a14d99973059fed1714a4256272da4ce2b4a5d` は下書きと同一。UTF-8読取り後は入力と末尾LFを含めOrdinal完全一致し、バイト差はBOMだけ。normal側出力なし。

完了画面 `complete-ui-full.png` を目視し、完了/停止無効/回答/成果物表示を確認（SHA `1e6e616c3972259b6188471ffdd2768f7e7471163dcc57f850febd1bf808c01e`）。export補助の末尾改行不足で記録が途切れ、追加exportは既存ファイルのCreateNewで拒否された。コピー本体を上書きせず、`export-verification.json` で原本/コピーのSHA一致を確認。これは製品業務失敗ではない。以後のPAD所有基準はowner SHA `7093d2d9bf7756e8bb5e1108ae4d81c6318a51563fde2a13e55982dd24d94c0d` / Main比較SHA `b5e73bdb6efeccbf57772b7f3d106da9f09492a80d3fd20c4ad07ac1f806b336`。

同日22:13 JST、修正後45f版の固定PAD→実AiCall20秒期限は **PASS**。`.work/gate1-deadline-fixed-f8415abdc9ca4d43bda0859f9f1834f3/`、job `2f91a9786c704c0398fc372f9f0b8eec`、result SHA `fa7ead8659f045bf0181fccab174e03153bc4335e61c29bd4d4a4789d78515b5`。子結果failed/timeout、実制御戻り値failed/AICALL_timeout、開始ID一致、入力1/出力0、成功本文・後続成果物・完了マーカーなし。元Main復元・保存、既存ファイル/ページ/owner/クリップボード保全成功。送信予約に加え、製品が送信クリックの応答確認後に設定する `has_sent=true` を読取専用の `send-confirmation.json` で確認。実M365送信後の期限切れとして記録する。以前のinvalid_response結果は書き換えない。

同日22:10 JST、App45f版は応答制御137件/Copilot302件PASS。通常更新 `8f340820b3654b10b060042a39d6d8b8` で実CMDからrelease `0.1.0-6079e7a56ebd98ad6365deb45729ea8a3adbda51b54bd51c1a7ab80996d8ff53` へ切り替え、新server PID25376 / port50142 / `2026-09-06T13:10:15.6866050Z` を確認。設定・既存ファイル・PAD所有記録を保持。これは更新検証であり、最新ソースの正常業務通し確認ではない。

同日22:04 JST、20秒期限の実試行 `.work/gate1-response-deadline-47832fcd0a164b5ead7101fbe23f84ca/` は送信予約後に `AICALL_invalid_response` となり、期待したtimeoutとは異なるためpartialを保持（result SHA `82dee61d64107477f20d8d4a9c9de3b9bc0547e45ec8fcd6b10e8487075916aa`）。元Main・既存ファイル・ページ・クリップボード復元はPASS、後続成果物なし。後から実回答を操作なしで2回読み、同じ完全なV1 JSONと合成テスト文の訳文を確認した（JSON SHA `d2e9be7176253f10b845bd9e4012ec2e31773628b9a2af47bfd4f7818acc6e83`）。期限内にこの形が完成していた証拠ではない。

コード上は、途中の不完全フレームの `lastError` が、その後に有効な回答を得ても残り、安定確認3回を待てず期限直前となった際にinvalid_responseへ誤分類する。追加したV1回帰で修正前のRESPONSE_INVALIDを再現し、各snapshotで判定を更新する修正後は期待どおりRESPONSE_TIMEOUTとなった。応答制御137件PASS（`.work/deadline-classification-fixed-1.json`、App SHA `45f9600171f830be7a1f010984e80ee85946b6d05c9e8bdeda3985b6662d4c7d`）。送信1回、安定確認3回、全体期限は維持。これは実試行の原因を一意に確定したことにはならない。Test-Copilot内の旧「すべての入力準備で同一期限」の期待は、既に採用済みの「操作ごとに準備期限、同じ操作のbusy再確認では不変」へ更新した。

同日21:48 JST、固定の実PAD→実AiCall子プロセスに対するプロバイダー境界の障害注入3ケースはすべてPASS。fixture Appは製品a743版の `Invoke-AgentCopilot` 関数だけを置換したもの（SHA `a94cc02cb136f723a6da32b67b0e78564d56ad79c0ac2327938185c453cb2600`）。子PID/Appパス/要求IDのboundary-hit記録を確認し、実M365送信予約なし。実M365自体の拒否/空回答発生とは区別する。

| ケース | 実制御戻り値 | result.json SHA256 |
|---|---|---|
| refusal | failed / AICALL_refusal | de5183b91ef549a236aa809bb4e5ff75ab7821eff5f3ad20da103b121a2490c5 |
| empty | failed / AICALL_empty_result | 9f3ea0d94dd9458ccdc12b34aa06fdaf4a47961ecd88e8ab712270731da11501 |
| cancelled | cancelled / CANCELLED | 6cfb12e59926cdd7a472e4ab9106eebe5002f334afa2b85470260339b0627d6d |

証拠は `.work/gate1-pad-provider-5c7e819ae3cb43a0bcafcd6340c46a38/<ケース>/`。全ケースPAD実行1回、開始ID一致、子の入力1/出力0、成功本文・後続成果物・完了マーカーなし。中止ケースは子の応答時に中止ファイルを作成し、PAD停止操作1回・子結果cancelledを確認。元Main貼戻し/保存各1回・復元時実行0、owner/既存ファイル/既存ページ/クリップボード保全成功。native Save失敗、送信後期限/中止、別利用者・社内PCの受入は残る。

同日21:42 JST、App `a743aecc068eaeec9a081e41e0a78a0c6bea0ca1d8aceea6f6ffbf638662f0cf` の固定PAD→実AiCallタイムアウトはPASS。session `.work/gate1-timeout-recorded-173b32b027454db0b426cae231f87508/`、result SHA `3777d6ce9bc377d398790968807710b632a2e2e503fb806e8ee2b1f1e7aebd97`。PAD実行1回、子結果failed/timeout、制御戻り値failed/AICALL_timeout、開始ID一致、成功本文・成果物・完了マーカーなし。元Main復元と保存各1回、復元時実行0、既存ファイル・ページ・owner・クリップボード保全PASS。5秒の期限はCopilot送信予約前に切れており、送信後の回答待ち期限の証拠ではない。

今回の製品差分は、PAD全文コピーを一度だけ要求し2秒以内で非空の結果を観測すること、中止確認、Planner指示に残ったsecond fence表記の訂正。core147/PAD335 PASS。PAD335を実機helperと同時に動かした1回は名前付きmutex競合で失敗し、helper終了後の単独再実行でPASS。実機検証とPADモック検査は直列にする。

新しい `Test-AiCallProviderFailure.ps1` は実PS5子プロセス内のプロバイダー関数だけを差し替え、拒否・空回答・期限・応答時中止の21件PASS。その他の製品ソースの同一性をAST差し戻しで確認。`.work/aicall-provider-fault-36663711ffe4491287597127c959988d/validation.json`。このテスト単体はPAD/M365を動かさない。

先行session `.work/gate1-focused-d147709b24504929b00e19503480b345/` は、子timeout・後続停止・元Main/ファイル保全を確認したものの、クリップボード例外で制御戻り値保存とクリップボード復元が未確認となりpartial。別の読取り専用記録はAICALL_timeout、開始ID一致、出力なし、Main ready/error0を確認した。元resultは変更していない。後続helperは制御戻り値を任意のクリップボード診断より先に保存する。クリップボード例外の根本原因は未確定。

同日20:16 JST、最新App `f9391133d2c52239de68a96d4f3a4a03b060f10967069d95ea2dab38c1474e45` の実V2分類通し検証は **PASS**。session `ee182d3e0c9c4e73a2be8cfa43a6cf93` / job `6e8eea67fc004355b13e76f7d8016c1a`。実HTML開始1/HTTP200→単一フェンスV2 ACT→生成PAD内V1 AiCall分類review→IF分岐/下書き→実観測を受けた異なるV2 ACT→PAD2回目→V2 DONEを確認。開始/終了マーカー・各run/call ID、4応答の独立2読戻し、ファイル/owner/全タブ/attempt帰属の保全、worker終了、UI完了一致がすべて合格。result SHA `877c11492e2473fd79194c074fee392f8e786c13dbd963df5a6fa832ba864a16`。証拠は `.work/fitted-d08798810a234ce0af71690cbf310519/classification/classify-sessions/ee182d3e0c9c4e73a2be8cfa43a6cf93/`。

最終 `final-review.txt` は83バイト/SHA `271fe047a97061f8eb4f3f2fd9a14d99973059fed1714a4256272da4ce2b4a5d`。入力は会議室が未定と明記するためreview分岐が妥当。下書きと最終ファイルは同一hash、normal側の出力は0。入力80バイトとの差はUTF-8 BOMだけで、UTF-8読取り後は末尾LFも含めてOrdinal完全一致した。完了画面 `complete-ui-full.png`（SHA `e29a54fc4bd5a98bf2041cb80dc32cb7dbc55dd99b6df45a54a0b247b16e0f33`）を目視し、完了/停止無効/最終回答/成果物パスを確認。`semantic-visual-review.json` と検証済み出力コピーを同sessionに保存。

この到達までの修正と証拠:

- 入力確認が1回約2秒かかり、6回の確認で共通15秒枠の約12秒を使うことを実画面で送信なし計測。低速キー処理を含む回帰で旧コードの準備期限切れを再現し、確認ごとの短い枠と不変の要求全体期限を分離。全体5秒を越えた入力/送信を防ぐ検査を含め、V2/V1応答制御134件PASS。
- 実AiCall timeout `ead2b7aa…` はfailed/timeout・成功本文なし・PAD runtime_errorを確認したが、旧実行器が途中のMain装飾表示でunknownとなった。元結果は保持し、実行中だけ完全な状態を期限内に再観測する対応を追加。永続不一致はunknownを維持し、Paste/Save/Runを再試行しない。PAD331件PASS。旧Main復旧は `.work/pastewait-db7901e78f01420c9451367b4080fbc6/restore-timeout.json`。
- 2フェンス間の余分なバッククォートが再発したため、既存2フェンスの検査を維持したまま、1フェンス内を明示マーカーで2セクションに分ける出力を既定とした。単一フェンス実長文 `bb4d6143…` は7794文字/26行/空行1/24 Write完全一致・保全PASS。DOMの境界/欠落/余分な行の拒否は維持。
- 実DONEの `5a165045…` は同じファイルを指す重複区切りパスが文字列比較で拒否された。`GetFullPath` でパス構文を解決後、正確な観測済みパスと現物hash、全文確認状態を照合する修正を入れた。未観測の同一内容ファイルやhash変更、全文省略は拒否。原応答/Robin/業務本文は変更しない。`needs_review` 分類の候補外ラベルも拒否し、core146件PASS。
- 実DONE `af18a3d9…` は全11行が枠内にありながらMoreが表示される状態でrenderedへ戻っていた。CSS maxHeight300px、padding込みclientHeight=scrollHeight=320pxを実測。V2メタデータ始端を持ち全行が完全に収まる表示を追加し、DOM893件PASS。元の同じ回答を再送/More操作なしで2読取りし、厳密なDONE解析と実成果物照合が成功（`done-fitted-reader.json`）。元失敗は書き換えていない。

本節の正常業務PASSを、AiCall全異常系・native Save失敗・社内/別PC・CIのPASSへ拡張しない。

同日18:06 JST追記: 修正後のV2分類 `3786d28baa0f4bcead05d685065e1ab9` / job `3236f6a3662a4769b6747662de125cb3` は実HTMLから開始し、V2 ACT・生成PAD・V1 AiCall分類review・IF分岐による下書き保存と、その実観測を受けた次のV2 ACTを確認した。下書きは原文と同じ83バイト/SHA `271fe047a97061f8eb4f3f2fd9a14d99973059fed1714a4256272da4ce2b4a5d`、分類値はreview。2回目のPAD反映が `PAD_COPY` で停止しASK_USERへ移ったため、DONEの証拠ではない。元resultはpartial、旧ファイル/owner/全タブ/新attempt帰属の保全は成功した。

追加の1回のコピー診断で、Main空・idle/error0、対象ListBoxフォーカス、Ctrl+A/C後もsentinel不変、owner不変、全clipboard形式/内容の復元一致を確認した。2回目のrunにはsubmitted.robin.txtがあるが開始/完了マーカーや成果物はない。旧成功Mainの貼戻し診断はpaste1/Run0で、キー送出から66msで戻り、2144ms時点の最初の状態観測でアクション存在とclipboard不変を確認。元失敗のタイミング原因は未確定。保存前の補助CancelPath指定不備を別記録で保持し、保存だけの新helperでsave1/copy2、最後の成功Mainとの全文一致・保存済み・owner不変・エラー0を確認した。実HTML停止1回でjob cancelled/worker終了。証拠はresume配下 `pad-copy-diagnostic.json`、`pad-copy-state-detail.json`、`paste-observation.json`、`finalize-main.json`、当該sessionの `stop-waiting-ownership.json`。

この実例に対し、空のReady/idleを貼付完了の条件から除く `-RequireActions` を追加。アクションが存在する連続2観測を得るまで提出クリップボードを保持し、コピー・再paste・Runを行わない。期限超過は `PAD_PASTE`。App `0d812b25…` のPAD325/core138 PASS。通常cacheは送信先修正版 `6119f110…` のままで、この追加条件の配布・実機受入は未実施。

同日17:35以降の配布方針: ユーザーは現共有を作り替え可能なテスト環境と明示し、実配布経路をGitHub→社内PC→社内共有フォルダーと指定した。以前のテストHTML所有者復元を継続条件から外した。開発用 `tools/Publish-AgentSource.ps1` は3ファイルすべての排他オープンと旧版バックアップを先に行い、ファイルオブジェクトを置換せず本文を更新する。ローカルファイル/ロック/ACLと単回の書込み境界例外による復元を13件検証しPASS。OS/プロセスクラッシュ時の原子性は保証しない。テスト共有への公開も成功し、操作前後のメタデータ一致を確認。これは旧失敗を合格へ書き換えたものではない。

通常更新 `171c27b7299143f3b30c572d0a41bbc2` は17:38 JSTにPASS。共有CMD1回・exit0、App `2cbe52e2…` の通常server PID32812/port63788、既存399ファイル保持を確認した。先行Prepare `1161a2d4…` は日時文字列がPowerShell 7のJSON読込みでDateTime化され、ISO引数検査で変更前に拒否された。ISOへ明示整形した新wrapper/IDでのみ続行し、旧失敗を保持した。

実HTML分類 `9557e7cdab414df9989eee35ca2ab14f` / job `80065a0fa6f349a7b5168410846cd267` は開始1回・HTTP200後に `CDP_UNAVAILABLE` で送信前停止。17:43の読取りで、入力18366文字、assistant0、has_sent=false、attempt存在、チャットと非モーダルの満足度アンケートに可視・有効な「送信」ボタンが各1個あることを確認した。スクリーンショットとDOMは `failed-classification-page.png` / `failed-classification-send-dom.json`。原因はグローバルな送信ボタン検索の競合だった。元resultはpartial、旧ファイル/owner保全とworker終了/UI一致を記録。タブ保全等の末尾監査は応答がない条件で先に拒否されたため、元のfalseを実際のタブ喪失と解釈しない。

`App.ps1` の既知 `div.fai-BebopLiteChatInput` 内のsubmit送信ボタンに対象を限定した。アンケートへのフォールバックをせず、入力領域内の候補欠落/重複/無効/非表示では拒否する。実画面のread-only再読で2ボタンが残った状態のsend_ready=trueと入力SHA不変を確認。新回帰は旧Appでsurvey-send混入を再現して失敗、新App `6119f110…` で隔離Edge DOM870、core138、Copilot302 PASS。修正版の通常更新 `59c2d1e16964416fa05e015c33ae4ce0` もPASSし、server PID12936/port61417/start UTC `2026-09-06T08:50:38.5631842Z`、保全一致。証拠は `.work/resume-279042c639354e21a630074e81e426b7/`。元失敗要求は再送していない。

同日17:27 JSTの再開検証: Issue本文と全コメント1件を再読し、HEAD `4243688`、通常server PID976/port59062、専用Edge PID12348、PAD PID25656を確認。PAD画面は専用「無題」Main、準備完了・エラー0。通常Explorerからの読取りで旧cache `0fc60b78…`、最新job DONE、owner SHA `927986a7277b956f011a2ef72dc06ff8b4fb3fd138349d63bc4a73cabf7b24eb` を照合した。

最新App `2cbe52e2…` を通常ExplorerのPS5.1 STAで直接読み込む取得診断 `8cdcfab0b1fa425d889a30c42a118d39` は **retrieved**。通常サーバー/キャッシュは旧版を別ハッシュで固定し、最新版配布の成功を前提にしていない。製品の `Invoke-AgentCopilot -Transport PlannerV2` から返ったACTは、1 Read・空行1・24 Write、7794 UTF-16文字/UTF-8 bytes・26行。期待RobinとのOrdinal完全一致、厳密parser/Robin検証、独立した2回の完全DOM・assistant・フレーム再解析一致、既存401ファイルとowner/ページの保全を確認した。送信1・再送0・PAD/clipboard/展開0。result SHA `0bd7f5edbeb5c243732cbb6ca11461652e7c00d57c30ecb679c4f0d06555885e`、Robin SHA `5d4e5ec416785d55dc62cb6093c3fbcff061f6df6c7efdaa967fc7389ab8ab11`。証拠は `.work/resume-279042c639354e21a630074e81e426b7/source-retrieval/sessions/8cdcfab0b1fa425d889a30c42a118d39/`。最新版HTML→生成AiCall→PAD→DONEの証明ではない。

同日17:22 JSTの共有更新診断 `76e4cca698984977a7b20306db277fa5` は **unknown/accepted=false**。既存の `Publish-PinnedSource-NullString.ps1` がApp/HTMLの2ファイルを置換後、HTMLの所有者/グループ/ACL変化を検出してCMD置換前に停止した。共有設定・ディレクトリACLは一致したが、旧HTMLは別アカウント所有で、File.Replace後は実行ユーザー所有になった。失敗resultと旧3ファイルのバックアップを保持し、17:23 JSTにApp/HTML本文を旧バックアップからファイルオブジェクトを置換せず復元。共有3ファイルの旧SHA一致を確認した。通常更新とサーバー再起動は未実施。

HTMLの元所有者を含むACL復元は `Set-Acl` が拒否した（`The security identifier is not allowed to be the owner of this object.`）。このメタデータ差分は未解決で、保全成功としない。復元記録は同resume配下の `share-recovery.json`。今後の公開は、全変更ファイルの所有者/ACLを置換前に検査し、維持できない場合は変更前に停止できる手順を必要とする。旧helper/消費済みclaimの再実行や、ACL検査を外して合格扱いする対応は行わない。

同日ローカル検証: READMEの引数省略実行でcore/V2解析のparam既定値にある `$PSScriptRoot` が空となる失敗を再現し、パス解決を本体開始後へ移して修正した。引数省略のcore138/V2解析108がPASS。現行AppでV2/V1応答制御118、Copilot302、PAD320、隔離Edge DOM859、launcher18、実localhost HTTP（token/Host/Origin拒否、slow-body期限、singleton再接続、質問ID/重複回答拒否、版切替、正常終了）もPASS。DOMはローカルfixture7件で外部転送0。これらは実M365/PAD業務や別PCの受入ではなく、CIも未設定。

同日17:02 JST、Planner V2の製品応答ループで1 Read・空行・24 Writeの長文を検証した（`bd1e00f891dc4ea88d4e8b63b00bdc5c`）。結果は `unknown / RESPONSE_INVALID`。製品関数の呼出しは1回、再送・PAD操作は0、既存ファイル・owner・ページの保持検証は成功した。回答後のDOMではメタデータ終端の次に、単独バッククォートの `data-line-index="3"` 行が実在した。製品はこれを正常なV2応答として取得していない。取得側が追加した文字ではないが、生成とCopilot表示変換のどちらが発生源かは未確定。元の失敗を保存し、追加DOM・snapshotの保存後に検証タブを閉じた。

この実例を受けて、生成指示にメタデータ終端直後のフェンス閉鎖と、余分な部分区切り文字を出力しないことを明記した。終端検査は緩和せず、同じ余分なバッククォートを拒否する解析回帰ケースを追加した。修正後の実Copilot受入は未検証。通常環境は16:48 JSTに更新済みの `0fc60b78…` のままであり、この生成指示修正はまだ配布していない。

通常環境の更新証跡は `.work/gate0/planner-v2-update/release-and-cleanup-186104db.json`。旧専用Edge終了による送信前失敗 `9639d2bb… / CDP_UNAVAILABLE` も保持した。製品の接続操作で専用Edgeを復旧してREADYを確認し、新しいプロセスに固定した別検証コピーで上記の実回答を観測した。コピーの事前検査は長文30件・分類62件PASSだが、分類の新V2実業務テストは未実行。

同日16:09 JST、Planner V2を本体ソースへ実装した。App SHAは `0fc60b7840dec296b4da5cf25910a959186a194ba2c3639d451f9fae53e630d9`。PlannerだけがメタデータJSON＋Robin本文の2フェンスを使用し、PAD内AiCallは既存JsonPartsV1を維持する。空行は今回IDの `AGENT_EMPTY_V2` 行だけを復号し、生empty・単独NBSP行は拒否、通常の文字・空白を保持する。元のPlanner契約、AiCall宣言・テンプレート一致、`Test-AgentRobin` は維持した。3回の安定読取り後にも中止・期限・ブラウザー所有を再確認する。

独立コードレビューで発見した旧JSON化ルールとの矛盾は修正し、旧候補で実際の全Plannerプロンプトの回帰テストが失敗すること、新版で138 core検査が通ることを確認した。DOMは859検査PASS（外部通信を転送しない隔離Edge）。メタデータ最大1MiBと空行符号を含む250行の組合せも、完全な行と表示領域を保って取得できる合成ケースを検査した。同じ変更候補の先行版 `5833c8e5…` では、未変更の解析・応答制御・PAD経路について、native PS5でCopilot302、PAD320、V2解析107、V2/V1混在・安定性・停止境界118検査がPASS。最終コードレビューはSHIP。証拠は `.work/gate3/planner-v2-product-candidate/` と `.work/gate3/planner-v2-parser-candidate/`。実行中のキャッシュはまだ旧428ea56であり、V2の実Copilot→PAD受入、配布更新、実機での長い1物理行の取得を合格扱いしない。

同日15:46 JST、短い空行診断 `fd71d463785c4daa9b4dc8e57bbb65a8` は `observed_shape`。1 Read・空行・2 Writeを実Copilotへ1回依頼し、2つの完全DOMとassistant読戻しが一致、旧392ファイル・owner・全既存タブの保全が通過した。指定した空行の位置（Robin body index 1 / DOM line-index 2）は、可視の単一テキストノード `U+00A0` 1文字だった。したがって元の空文字とは一致せず、`raw_fixture_text_values_match` とroundtripはfalseのまま保持する。PAD・Copy・More・再送は0。証拠は `.work/gate3/plain-robin-empty-feasibility/sessions/fd71d463785c4daa9b4dc8e57bbb65a8/`。この結果から、製品V2候補では空行を `AGENT_EMPTY_V2 <request_id>` という明示的な独立行で送り、今回のIDに完全一致した目印だけを空行へ復号する方式を採用する。通常の文字や空白を正規化しない。設計の独立レビューはSHIP、本体への反映とこの方式での実機受入はまだ未実施。

同日15:27 JST、保存呼出し直前の障害注入セッション `0d64ad6442bf41b68846647ba4677e52` はPASS。現行Appの `Invoke-AgentPad` が実際の所有確認・削除1・貼付1・全文読戻し2を行い、診断wrapperがSaveの呼出し直前に1回だけ例外を返した。元controller観測は `failed/G2S_INJECTED_SAVE_CALL_BOUNDARY` で保存し、controllerのnative Save・Run・Stop、開始/完了marker、成果物はいずれも0。その後、実Mainが今回のsubmitted全文と一致しownerが不変であることを2回の読取りで確認し、退避した成功Mainへ削除1・貼付1・保存1で戻した。最終読戻し、owner、旧normal/privateファイル、全ブラウザータブ、全対応形式のクリップボード復元が通過し、errorsは0。事前のnative PS5境界46検査・合成Clipboard52検査と、事前/実結果の独立レビューがSHIP。証拠は `.work/gate2/save-boundary-diagnostic/sessions/0d64ad6442bf41b68846647ba4677e52/`。これは実PAD貼付後のSave呼出し境界への障害注入であり、PAD自身のnative Save失敗や業務成功と呼ばない。

同日15:20 JST、自然な複数行Robinをメタデータと別フェンスで運ぶ限定診断 `823e82f11d2f471fb779c50260ec8bbe` は、実Copilotから24 Write・25行・7793文字を完全取得した。新規job `332b316424864e79bcf05508615a64bf`、request `4f335bf66ae543d688c2a21db451eaee`、owned target `335E773936F8CFDD9A187F9DE76075E7`、送信1回。2回の完全DOM・assistant読戻しが一致し、厳密なメタデータ、24個のパス順、Robin全文、既存の `Test-AgentRobin` が一致。Robin SHAは `4d6fe410078873d26dafd1ac1453016a13d4e4b48aa1a4f635e1e8c96c6a95ec`。モデルにhashや文字数の計算を要求せず、受信側だけで診断値を計算した。PAD・Copy・More・再送0、本体・共有・キャッシュにV2を実装した証拠ではない。診断一式は `.work/gate3/plain-robin-feasibility/`。事前にnative PS5の43検査、隔離Edge描画の26検査、独立レビューSHIPを確認した。

この診断の元 `result.json` は `unknown/PR_PRESERVATION` のまま保持する。旧384ファイル、PAD owner、新規job/attempt/targetの所有は保持したが、以前の4分割試験のタブ `3D1B12A764C0F49BAE0B1EC41F02CDFF` のURLが既存conversationから `/chat` へ変化した。旧18タブは存在し、新規タブは今回所有の1個だけ。終了後の読取専用照合で当該URLを2回確認し、target record不変・追加送信/PAD/タブ操作0。URL変化の原因は未確定であり、利用者操作やCopilotの仕様と断定しない。取得成功と診断全体の保全不成立を区別する。空行は後続15:46の別診断で形状を測定したが、製品V2経由の受入は未検証。

別PC確認用に、現行428ea56の配布3ファイルだけを含むZIPを `.work/distributions/issue-5-poc-428ea56-20260906-b69d586e48c844d6b8ccf3ca815115ea/` に作成した。全entryのSHAと実ソースが一致し、ZIP SHAは `a53a32b2d1fd4f97b107f87e05766a5291fdcd63eac0bd79865ad198d4d562df`。同フォルダーに確認手順と検証manifestを分けて置いた。別PCでの実行は未実施。

同日14:44 JST、独立レビューは分類job `4146fa7dd2d74d34b4c3a6ccc95754d0` の業務経路をSHIPと判定した。4応答のpayload長は4443/271/1849/465文字で、最初の実ACTが旧4096文字上限を超えるケースも通過した。原JSON・2つの実 `flow.robin`・各実行結果・前段の観測時刻・最終UI・ファイルSHAの対応を再確認した。レビュー記録は同セッションの `independent-business-review.json`（SHA `a667d8db…`）。補助の修正版 `Invoke-Gate45ClassifyUi-PartsOwned.ps1` は、安定した2回のcarrierを製品parserで全体検証してからIDを許可する。実4回答と4attemptの一致、nonce不一致・欠落・不安定回答・未所有attempt等を含むnative PS5の39検査がPASS。証拠は `.work/gate45/parts-ownership-helper-validation.json`。新しい業務再実行や元partial記録の書換えは行っていない。

同日14:31 JST、新版の分類セッション `adf5eabd49a046d2bf68b9edd0e9322d` の製品job `4146fa7dd2d74d34b4c3a6ccc95754d0` がDONEに到達した。実HTML開始1回・HTTP200、分類AiCall1回、生成された異なるRobinによるPAD2回が成功。最初の `review` と下書きをアプリが全文確認し、次のRobinがその2ファイルを読み直して条件分岐し、`final-review.txt` を作成した。最終83バイトは下書きとSHA `271fe047a97061f8eb4f3f2fd9a14d99973059fed1714a4256272da4ce2b4a5d` が一致し、normal側の出力は0。ACT/業務回答/ACT/DONEの4応答を2回読み戻して完全一致、最終UI「完了」と成果物表示・worker停止を確認した。全文画面 `complete-ui-full.png` はSHA `9c9f435a74738b81467819107f6f4043aa4c2a5b5c64e8af5227b7ac9c7de317`。

同セッションの `classify-acceptance.json` はpassedだが、元 `result.json` は補助の `G45_PRESERVATION_UNCONFIRMED` によりpartialのまま保持する。独立確認では、追加された4つのattempt IDは製品parserで復元した4応答のrequest_idと一致した。補助の末尾監査が `assistant.text` だけを検索し、分割回答では空のtextと別のframesに入るnonceを見落としていたことが原因。旧ファイル・PAD owner・タブ所有は確認済み。新たな業務実行や元結果の書換えをせず、補助の修正と独立した証拠照合を進める。

同日14:28 JST、コミット `428ea56` のメタデータ指示版を共有と通常起動版へ反映した。公開 `a9031ff018e7447a8428476a4a8f705c` と通常更新 `53cb744c8c924dc682676fe60015ca70` はPASS。旧348ファイル（normal294/private51/archive3）、PAD owner/content、共有ACLを保持し、新server PID9152/port62884でApp SHA `f040085c…` が一致した。証拠は `.work/gate0/release-update-428ea56-summary.json`。新規分類セッション `adf5eabd49a046d2bf68b9edd0e9322d` を実HTMLから開始した。この時点では終端と業務成果物の検証は進行中。

同日14:24 JST、AiCallメタデータの生成指示を本体へ反映した。App SHA `f040085c1f3c96aa910a314cbf498a62656e82b8cd2a75f5a3ca176076ffdf30`。変更はPlanner指示2段落のみで、テンプレート呼出しに対応する `ai_calls` の必須条件を明記した。parser・schema・Robin検証・要求作成権限は不変。最終候補と本体のhash一致、native core137/Copilot302/PAD320、欠落・空配列・宣言付き対照ケース15件のPASS、独立レビューSHIPを確認した。最初の候補は既存の文面一致テストで失敗し、元文を保って同じ段落へ必須条件を追記した。元候補・結果も保持。証拠は `.work/gate3/ai-call-metadata-candidate/validation.json` と同report。共有更新と新版実機分類はこの時点で未実施。

4ブロックを明示した同じ24 Write試験 `cc43392735074d4fae67c45f6c77d2e1` は、送信1・180秒で `unknown/RESPONSE_TIMEOUT`。終了後の読取専用観測 `Observe-PracticalFourFrameTimeout-6985dffdc96b4b179d9801905d6e1762.json` は14:23 JSTに、プロトコルmarkerを含まない生成拒否の本文が2回一致した。Copilotは厳密なマルチパート形式と完全一致生成要求に対応できないと回答した。原結果・旧データ・タブを保持し、追加送信・PAD・More・focus・scroll・clipboard操作0。この負荷での長文生成の安定性は未解決であり、成功扱いしない。

同日14:12 JST追記: コミット `54bb3e5` の8192文字対応版を共有と通常起動版へ反映した。公開 `5405a47dc9644e4b950b1071337f5c29` と通常更新 `1b70cd9cd42a4a6785fb7f9ddcd848f2` はPASS。332ファイル（normal278/private51/archive3）、PAD owner/content、共有ACLを保持し、新server PID11132/port61243でApp SHA `7bed68c3…` が一致した。証拠は `.work/gate0/release-update-54bb3e5-summary.json`。分類用起動補助の初回は日時をロケール表記で渡したため引数検証で停止し、UI/provider/PAD操作前の失敗を保存した。ISO形式に修正した別セッションで以下を実施した。

分類試験 `139fa42459ae4355a2ae6ae84defad41` は実HTML開始1回・HTTP200からACTを完全取得したが、`ROBIN_ACTION` でPAD反映前に停止した。保存した2観測のpayloadは3811文字、frame3971文字で一致。純粋PS5診断ではJSON・改行・パス・AiCallアクションそのものは正しく、回答に `ai_calls` が欠けていたため承認済みテンプレートと要求ファイルを作れないことが原因だった。元結果は `partial/G45_JOB_NOT_DONE`、末尾の `G45_PRESERVATION_UNCONFIRMED` も保持する。実UIとjob終了・worker停止、旧ファイル・PAD owner保持を確認した。診断は `.work/gate3/frame8192-generation-diagnosis/report.md`。メタデータの推測や応答修復は行わず、生成指示2段落の明確化を候補で検証中。

24 Write長文試験 `899979974a8e47e7b3d250f6e7c0a9b5` は送信1回・180秒で `unknown/RESPONSE_TIMEOUT`、raw未保存、PAD/再送0、保全成功。終了後の読取専用観測 `Observe-Practical8192Timeout-5bea5424f0e84e7687e7d9fee9e90552.json` は14:10 JSTに2回一致した。回答はACTの1/1フレームで、DATA物理行は10000文字、payload9989文字、`long-009` のパス途中で切れた未完JSONだった。終端markerは存在した。8192上限超過と欠落のある回答を実行していない。切断の発生層、元の期限以前の状態は未確定。24ファイル保持、追加送信・More・scroll・focus・clipboard・PAD操作0であり、この観測を長文取得成功へ読み替えない。

同日13:51 JST、上記候補を本体へ適用し、検証済みと同じApp SHA `7bed68c365fb8b3b328dba365bc8498764dbf0629a3bf7051f5cbe19749c525f` およびテスト2ファイルのhash一致を確認した。payload上限8192、DOM行上限8203、最大frame8648へ変更し、全体1048576・最大256ブロック・厳密な順序/nonce/終端/3回安定読取りは維持した。検証は受信アプリ側で行うことを生成指示へ明記した。native PS5 core137/Copilot302、隔離Edge DOM818はPASS。4097と実例相当4685、8192、最長frame8648、全体1048576の受理と、それぞれの超過拒否を含む。独立レビューはSHIP・must-fixなし。候補配下で最初に実行したcoreはテスト用パス長の問題で失敗したが、元の同一テストへ候補Appを指定して137件通過し、両記録を保持した。共有/通常キャッシュ更新と新版の実機通し検証はこの時点では未実施。

同日13:44 JST時点: 復旧後の分類試験 `2f98b33d2c824ca38749657286b81770` は初回Copilot取得で180秒timeout、PAD反映0でfailed。実UI表示とjob終了、worker停止、旧ファイル・owned targetの保全を確認した。後続のowned DOM観測 `Observe-OversizedFrame-b4c5c1abf907498d84e1c0d6a6d4d2e1.json`（SHA `23f576ba…`）は2回とも72ノード・4行を欠落なく採取し、各行は1個のtext node、長さ50/4696/54/42文字だった。payloadは4,685 UTF-16単位で、製品の4,096上限を超えていた。DOMの行上限2箇所だけを接頭辞込み8,203へ変えた読取専用候補は、既存の所有・構造・geometry検査を保ったまま同じ4,845文字の1フレームを取得した。元のtimeoutは保持し、受信payload上限8,192・フレーム全体8,648・全体1,048,576の候補をローカル検証中。この時点で本体・キャッシュはまだ変更していない。

同日13:36 JSTの24 Write比較試験 `9419b5c66b474418a8dd4915460300a2` も、Copilotが「製品ワイヤープロトコル断片化と完全一致JSON生成を保証できない」とする1ブロックのBLOCKEDを返した。raw取得は成功したが、長文2ブロック以上の条件を満たさずfailed。送信1・PAD/再送0、保全成功。以前の24 Write長文成功を新版の成功へ読み替えない。

同日13:30 JST、由来と全文hashを確認した専用テストフローを、最後に保存記録と一致していた成功runの本文へ戻した。復旧helperは現在 `cfef067e…`、復旧元 `1a45e064…`、ownerファイル `0d6490a8…` を照合し、削除・貼付・保存を各1回だけ実施。取得前・貼付後・保存後の全文を保存し、最終本文と旧ownerの一致、idle/editable・エラー0、clipboard全形式復元、既存10ファイルの保全を確認した。Run・provider・owner書換え0。`Read-PadOwnership-Recover-20260906.json` はrestored。これは診断用の限定復旧であり、製品に自動復旧機能を追加したものではない。

同日13:25 JST追記: 分類の保存済み2観測をnative PS5で再検証し、ACTのpayload2,500＋1,988文字、JSON4,692 UTF-8バイト、Robin3,126文字/19行が実保存 `flow.robin` と完全一致した。ASK_USERも1ブロックで製品parserが受理し、双方のnonce・attempt・key・全文境界が一致した（`multipart-transport-posthoc.json`、SHA `b4c0f86a…`）。これは実搬送の成功であり、PAD完了の証拠ではない。

通常Explorerからの専用PAD読戻し `Read-PadOwnership-20260906c.json` は、Ctrl+A/Cを各1回、全形式clipboardの復元・検証を行い、236ファイルを保全した。現在本文の比較hash `cfef067e…` は、前回のPAD_FOCUS失敗run `9e07238ab9424b97a7cb4ee91b42e739` の `submitted.robin.txt` と完全一致した。ownerのhash `1a45e064…` はその前の成功run `0d670b045a254c60ad4bf0bbb48e5e19` と一致する。前回の新フローが貼付済みでowner更新前に停止した状態を特定した。Saveへ到達したかは未確定であり、利用者が編集したと断定しない。初回2つの診断helperはパスとIDの比較ミス、次いで稼働中Edgeのprofileファイル読取りで停止し、いずれもUI操作0の元unknownを保全した。

36 Writeの指示範囲を明示した別試行 `b58369bd973046598f5ff10250cd96cf` は、送信1回から約32秒で指定形式のBLOCKEDを取得した。Copilotは36個の個別アクションの厳密生成に対応できないと回答した。1ブロックのため長文helperの2ブロック以上条件で `failed/GATE3_CAPTURE`。元結果・raw・snapshotを保持し、長文生成成功へ読み替えない。製品の取得自体は戻っており、PAD・再送0、既存保全は成功した。

同日13:18 JST時点: 新版の通常HTML経由の分類試験 `5e677d3bb4554662b5396143aca259f3` では、実Copilotの2ブロックACTを製品が完全取得し、Robin検証を通過した。続く専用PADの既存本文照合で `PAD_OWNERSHIP` となり、差し替え・保存・Run前に停止した。次のASK_USERも1ブロック形式で取得できたが、業務は未完了。回答を捏造せず、実HTMLの停止を1回押してjob `86022f2b5fa34f93854cd0214cf25e26` のcancelledとworker終了を確認した。元の結果は `partial/G45_JOB_NOT_DONE`、末尾の検証helperの `G45_PRESERVATION_UNCONFIRMED` も保持する。既存フローは上書きせず、実画面の本文と保存記録の差を調査する。

長文timeoutの後続読取 `Observe-MultipartTimeout-8288b7f9c6bc4db29ab21367120503c1.json` は13:14 JSTに2回一致・保全成功。現在の回答は194文字のBLOCKED JSONで、フェンス・分割マーカー・終端がなく、Copilotは「トップレベルJSONのみ」との不整合を理由に挙げていた。これはCopilotの説明であり、入力指示の矛盾や元の期限までに回答が完了していたことの証明ではない。元timeoutを変更せず、外側の搬送形式と内側のJSONの適用範囲を明示した別の合成検証を準備した。

2026-09-06 13:04 JST時点: コミット `1c108da` の分割回答対応版を共有と通常キャッシュへ反映した。公開 `cae5bab263e3412b9a07a1aeee23ebde` と通常更新 `29e8f41c344b4a13ad457ad363da4ede` はPASS。既存301ファイル、PAD owner/content、共有ACLを保全し、新server PID26152/port51399で同じApp SHA `8f1aeacc…` を確認した。続く新規長文検証 `3069a7ef3a3b451db586c84608816847` は、送信1回から180秒の期限内に完全な回答を取得できず `unknown/RESPONSE_TIMEOUT`。PAD実行・再送0、既存ファイルとowned targetの保全は成功した。元の結果を保持し、同じ回答の読取りで原因を調査する。この時点では分割方式の製品経由の実長文成功を主張しない。

2026-09-06 12:30 JST追記: Issue本文・コメント0件を再確認し、§10.2の「複数コードブロックを欠落なく取得」に対する未実装部分を特定した。既存の単一フェンス拒否だけではこの要件を満たさないため、番号・総数・要求ID付きの `AGENT_PART_V1` 形式を実装中。最終Planner/AiCall JSON契約を保ち、各断片を最大4096 UTF-16文字で運び、厳密な順序確認後に元のJSONへ戻す。実M365の2ブロック構造の観測と、独立したparser/DOM候補の検証を進めている。現時点ではこの方式の製品・実機成功は未確認。
2026-09-06 12:32 JST、利用者のロック解除後に通常Explorerから再確認した。アクティブコンソールはセッション1へ戻り、入力デスクトップDefaultを開ける状態になった。PAD「無題」はPID25656/start一致、ready・idle・editable・can_run・エラー0件、owner/contentハッシュ保持。以前の前面操作を妨げた状態は解消した。新規PAD処理はまだ開始していない。専用Edgeの旧PID27488とポート9223は終了しており、次の検証前に製品の起動経路で再接続する。読取証拠は `.work/gate45/unlocked-desktop-a6d0d83e394f46228ba313caf9a70ac0.json`。
同日12:38 JST、製品 `Open-AgentCopilot` を通常Explorerから1回呼び、専用Edgeのポート9223所有者PID18096を確認した。起動直後の診断はAUTH_REQUIREDだったが、ページ読込み後の別の読取専用診断はREADY。再送信・PAD操作は0回、ownerは保持した。証拠は `.work/gate3/copilot-after-unlock.json` と `copilot-after-unlock-readiness.json`。起動用タブの照合はnot_foundで、他タブは閉じていない。

実M365の2ブロック観測 `.work/gate3/two-fence-sessions/d1d3bbf5f52a4e249b0b82c82fdac9d3/result.json` はobserved。新規job `67b2aefa3e5b413591c8f5c30cb967a7`、request `55c6501f6c00412e97011466fdecd0cb`、送信1・PAD/Copy/More/再試行0。139ノードのowned DOMを2回保存し一致、3行＋4行の全フレームと139文字の元JSONが一致した。日本語・引用符・パスのバックスラッシュ・%・空白・エスケープ途中の分割を保持。既存の単一フェンス製品parserはRESPONSE_INVALIDを返しており、この観測を製品対応済みの証拠には数えていない。
同日12:53 JST、分割回答のDOM取得・厳密復元・3回安定読取・Planner/AiCallプロンプトを統合した。App SHA `8f1aeacc1bd101d2beae611ebc317af2fee5d0bf9dd4149fcfd600bc459fa2be`。統合した実ソースに対してnative Windows PowerShell 5.1 x64 STAのcore137/Copilot287、独立EdgeのDOM806がPASS。coreの旧プロンプト形式を前提とする2検査は、同じ最終schemaを保つ新形式の確認へ更新した。独立レビューはSHIP・must-fixなし。ローカル検証には1万文字超・256ブロック・4096文字境界・Unicode・エスケープ境界・欠落/重複/逆順/異なるnonce・全文境界の変化・折畳み・生成中・過去回答の検査を含む。配布と新方式の実M365/PAD受入はこの時点では未実施。

2026-09-06 11:13 JST追記: 複数行JSONの既知DOM取得と既存More操作、PlannerのRobin/JSONパス表記・同一出力への重複Write禁止、IF/ELSE後の`Keys`変数の確定代入判定を統合した。App SHAは `f2449a5f14cfb523f4cc77e7e48691b6687275f10acdaa815a4b436bf79262fc`、配布releaseは `0.1.0-0b7bc16475f5b5c861886ce6f051efc0ea2c52673c543c0add121cc039ca3c14`。統合した実ソースに対しWindows PowerShell 5.1 x64 STAでcore 137 / Copilot 232 / PAD 320、通信をすべてローカルで応答する独立EdgeでDOM 687チェックが通過した。独立ソースレビューはSHIP・must-fixなし。coreテストの最初の相対パス起動は既存の既定引数評価で失敗し、絶対AppSourcePathを指定した実ソースで完了した。共有・通常キャッシュへの反映と新しい実Copilot/PAD検証はこの時点では未実施。単一JSON文字列の1行が10,000文字を超える場合の完全取得は保証していない。

同日11:28 JST、コミット `cf00c1b` の上記版を実共有UNCへ反映し、そのCMDから通常のローカル版を更新した。共有公開 `.work/gate0/publish-pinned-source/ba520ce4f94b46d78d7f4fe2d416f2b8/result.json` はPASS（SHA `7f6f7b9b41156665be17c85f5112fbd02ee8a4d2d007a2ced6818ed2b31b938f`）。Appの置換1回、旧3ファイルのバックアップ、ローカル共有/UNCの新hash・バックアップの旧hash、既存共有の構成とACL保持を確認した。通常更新 `.work/gate0/normal-updates-pinned-source/2337e9fc5bf74a47b166334740c35024/result.json` もPASS（SHA `c08a43ed54f2e2903e823da42aa96a3dd4ae202a58fad1222222c96b84d0642c`）。旧server終了後のUNC CMD1回・exit0、新server PID32660 / `2026-09-06T02:28:02.7613149Z` / port49672、新App hash一致、既存239ファイル（normal185/private51/archive3）の保持を確認した。更新手順自体のprovider/PAD操作は0。

共有更新用ヘルパーの先行2試行は別記録で保存した。最初は準備前に停止し、追加引数`OldRelease`と同名のローカル変数の衝突を純粋再現して改名した。元例外はハッシュのみの保存で、完全な同一性は確定していない。次の試行はPowerShell 5.1の`File.Replace`への`$null`引数で置換前に失敗し、共有/UNC/バックアップは旧hashのままだった。元結果を変更せず、NullStringを使う最小修正をローカルの実ファイル置換で確認してから、新しいIDによる上記公開に成功した。これは更新用検証ヘルパーの修正であり、配布アプリ本体の追加変更ではない。

同日追記: 上記長文の実DOMは33行・188ノード・12,635 UTF-8バイトが完全に存在していた。展開後も `maxHeight=3050px / overflow=auto` となる実測状態を追加認識し、全行がスクロール内容の矩形内にあることを確認する。別のDONEではMoreの中央だけに32pxの「一番下までスクロール」ボタンが重なっていたため、中心の既存viewport条件を保ち、同じMore内の左右1/4の2点だけを追加確認する。単回クリック、nonce、全文、既知DOM、可視性の検証は維持する。修正後App SHAは `871389ed29500e337c243daff4d1729433b19e4d3399e888debfcf6617cb9fcc`、releaseは `0.1.0-2d7754fb1622a94dcace8623dd48a549ddc599a421f09dafa033b1fb7a69cde4`。統合DOM752件とcore137件、Copilot232件はPASS。候補と元のunknown/failedを保持し、新しい実行による確認は別記する。
[Issue #5](https://github.com/minimo162/ai-prompts/issues/5) 本文と全コメント（0件）を確認して実装した。ブランチは `codex/issue-5-business-agent`。この記録は成功条件の達成宣言ではない。

## 実装した範囲

配布本体はCMD・App.ps1・index.htmlの3ファイル。ローカル同期、版とハッシュの検査、localhost UI、ジョブ状態、停止、質問と回答、Copilot計画・AiCall、有限Robin検証、専用PADへの差し替え・保存・1回実行、成果物観測を実装した。

初版のRobinはUTF-8テキスト、変数、IF、有限WAIT、固定AiCallに限定する。任意のPC操作、Excel編集、任意のPowerShellコードは未対応。PADのUI操作とM365のDOM操作を含むため、コードがあることと実機で動作が確認できたことを分ける。

## 検証結果

| 検証 | 証拠と範囲 |
|---|---|
| Windows PowerShell 5.1 契約検証 | `tests/Test-App.ps1` **137 PASS**。Copilot/PADを模擬し、要求・結果・観測・再計画・パス境界・同期と実計画/AiCallプロンプトを検査する。実サービスの証拠ではない。 |
| Copilotアダプター | App SHA `7bed68c3…` に対する `tests/Test-Copilot.ps1` **302 PASS**、隔離Edgeの `tests/Test-CopilotDom.cjs` **818 PASS**。CDP応答の模擬とローカル描画で、全文・ID・終端・生成終了・排他・ジョブ分離・異常分類・他タブの保持・送信の再試行禁止を検査する。番号付き分割回答の完全復元、8192文字境界、全体1048576文字、256ブロック、Unicode、エスケープ途中の分割、欠落・重複・逆順・過去回答の拒否を含む。実M365とPADの結果は別記し、これらのローカル検査を実サービスの成功証拠には数えない。 |
| PADアダプター | `tests/Test-Pad.ps1` **320 PASS**。UI/クリップボード境界を模擬し、全文一致・所有権・失敗時の旧フロー実行拒否・結果帰属を検査する。状態別のUI構造、20種類の状態ID、保存・実行・中止、実ファイルに生成した2件のAiCallテンプレートとRobinの検証も本番関数で確認。実機の固定A/Bは下記に分けて記録する。 |
| localhost HTTP | `tests/Test-Http.ps1` PASS。実App.ps1プロセスでHTML/状態、トークン/Host/Origin拒否、不完全本文の期限、再接続、設定保持、重複回答・古い質問への回答拒否、版の引き継ぎ、停止を確認。 |
| 実ブラウザー | `tests/Test-Ui.cjs` 15 PASS。実Edgeの1280×900・390×844で入力→未接続エラー→再表示、トークン除去、同ジョブ再接続、横溢れ・JavaScriptエラーなしを確認。質問ID・Copilotジョブ分離変更を含む不変版 `a00bca7` でも再実行し、両幅のPNGを目視確認した。証跡は `.work/ui-after-question-fix-66edd1690c8a4978aae727d6e5a31807/`。隔離サーバーは専用の終了APIで停止した。 |
| 実際のCMD | リポジトリ上のCMDから実LOCALAPPDATAへ同期し、ローカルApp.ps1のHTTP応答を確認。Chromeにアプリタイトルのウィンドウが現れた。最終統合版も `Bootstrap -NoBrowser` で同期し、実LOCALAPPDATAのサーバー応答と作業コピーのApp.ps1ハッシュ一致を確認した。共有UNCからの検証は下記Gate 0記録に分ける。 |
| ランチャー回帰 | `tests/Test-Launcher.ps1` **18 PASS**。実3ファイルのBootstrapと、隔離したCMDフィクスチャの環境/終了コードを区別して検証する。 |

実CMDで、親のPowerShell 7用モジュール検索パスをWindows PowerShell 5.1が引き継ぎ `Get-FileHash` を解決できない不具合を再現した。CMDの `setlocal` 内でOS標準のPowerShellとモジュールパスに限定して修正した。`-File` ではparam既定値の `$PSScriptRoot` が空になる問題も再現し、param評価後に配布元を補うよう修正した。

初回のComputer Useによる実CMD起動後の画面撮影は、現在のブラウザーURLを十分に判定できないとの理由でツールに停止された。その検証では再試行していない。後続のPAD画面確認と専用Edgeの再起動は下記に別記する。HTTPの確認を画面表示確認へ読み替えない。

## Issueのゲート

| ゲート | 状態 | 残る実機確認 |
|---|---|---|
| 0: 配布・起動 | 実共有UNCからの初回・更新、欠落UNC時の警告付きローカル起動は合格 | 実共有の切断、利用者環境での再起動・UI停止 |
| 1: 固定PADからAiCall | 実PADから翻訳→分類の直列2回、結果受渡し、review分岐と出力を確認。a743版で送信前期限・子プロバイダー境界への拒否/空/応答時中止注入、45f版で実M365送信後期限/中止も実PADまでPASS | 拒否/空の注入検証を実M365自体の拒否/空回答発生としない。送信後中止は監視による中止ファイル作成で、UI停止ボタン押下ではない |
| 2: AIなしのA/B差し替え | 正常系A/B合格。実行中の別controllerをPAD_BUSY・UI操作0で拒否し、元の実行を中止・出力抑止する動作を確認。実PAD貼付後のSave呼出し境界への障害注入でRun0・元Main復元も合格。busy/cancel追試の元unknownは保持 | PAD自身のnative Save失敗は未検証。制御した呼出し境界の失敗と、実貼付後の異常でRun前に停止した証拠を区別 |
| 3: 生成Robin全文取得 | f939版の単一フェンスV2で7,794文字・26行・空行1・24 Writeの期待本文完全一致と独立2読取りを確認。過去の途中停止/余分な終端行を拒否した結果も保持 | 個別合格は任意の長さや全応答の生成成功を保証しない。24/36 Writeは検証用負荷で、Issueに必須文字数の指定はない |
| 4: 生成AiCallフロー | 翻訳→書出しと分類→IF分岐→書出しが実PADで成功。最新45f版でも単一フェンスV2分類ジョブの2ACT→DONEまで完了 | 固定AiCall異常系はGate 1に記載 |
| 5: 2〜3往復 | ASK_USER→回答→ACT→AiCall/PAD→DONEとBLOCKEDに加え、新版の分類2ACT→DONEも成功。最初の実成果物の再読込み・分岐・最終出力・完了画面を独立再照合済み | 確認した代表シナリオの未確認事項なし。原helperのpartialは分割応答IDの抽出漏れとして別記録で診断し、原結果を保持 |
| 6: 別利用者・別PC | 未検証 | 開発環境に依存しない導入・更新・認証・結果確認 |

2026-09-06に利用者の許可とWindowsの管理者承認を経て、専用共有 `\\localhost\AiPromptsAgentPoC$` を作成した。共有範囲は `.work/shares/AiPromptsAgentPoC` の配布3ファイル、SMB権限は利用者本人の読み取り1件で、NTFS権限・サービス・ファイアウォールは変更していない。最初の承認後試行は共有作成前のファイル名照合で失敗した。作成スクリプトがBOMなしUTF-8だったため、Windows PowerShell 5.1が日本語CMD名を誤読していた。本文を変更せずUTF-8 BOMを付け、旧版の保存と独立した構文・ファイル名照合確認後に成功した。作成・UNC読取の証拠は `.work/gate0/share-create-6a7c02fc14f34586b7c7a5cb32def3c4.json` と `share-verified-6a7c02fc14f34586b7c7a5cb32def3c4.json`。

実共有UNCのCMDを使った初回・更新の結果は `.work/gate0/sessions/ba53e2cf86914d89a514f6c5f7028b66/results/initial.json` と `update.json` に記録した。CMD子プロセスだけのLOCALAPPDATAを隔離し、`49a4535` の初回同期後に共有3ファイルを `160f130` へ更新した。再起動で更新版へ切り替わり、旧キャッシュ3ファイルのハッシュが変わらないことを確認した。各段階の隔離サーバーは所有者を照合して終了し、通常のローカル版のPID・開始時刻・版・Appハッシュは前後一致した。PAD・プロバイダーは呼び出していない。共有は最新の検証済み3ファイルを保持している。

初回・更新の独立再計算は37項目すべて一致した。切断試験の事前レビューでは、検証ハーネスがBootstrapを同じPowerShell内で呼び、未設定または古い `$LASTEXITCODE` を読む問題を修正した。別のWindows PowerShell 5.1子プロセスの終了コードと30秒の上限を使い、合成4ケース・27項目（成功、exit 7、未処理例外、タイムアウト）が通過した。これは検証用スクリプトの修正であり、実共有切断時の成功証拠ではない。

独立レビュー後、専用フォルダーだけを一時改名してUNCを利用不可にする手順を1回試みたが、Windowsの「別のプロセスが使用中」により改名前に拒否された。`results/outage-helper.json` は `status=failed`、`renamed=false`、`harness_invocations=0`、復元・UNCハッシュ確認済みを記録している。共有切断とオフライン起動は未検証のままであり、共有・初回/更新の記録・キャッシュは保持している。同手順は再実行していない。

初期調査ではPAD 2.71.115.26224のインストール済みリソースから、`StartFlowButton`、`SaveFlowButton`、`ProgramItemsListBox` 等の操作要素の候補名を得た。実UIAでの存在・一意性・操作パターンは後続の調査で確認した。初回の新規フロー画面ではComputer Useの名前入力が反映されず、作成を取り消した。その後、利用者の明示的な作成許可を得て、Power Fx無効・自動生成名「無題」の空フローを1つ作成した。`Power Automate | 無題`、Main 1個、アクション0件、準備完了の実画面を確認し、アプリ設定も「無題」に合わせた。業務フローの実行・変更は行っていない。

実画面で得たタイトル形式に合わせ、フロー特定条件を修正した。フロー名だけの形式、既知の旧形式2種類、`Power Automate | フロー名` の4種類をOrdinal完全一致で認める。似た名称や任意の接尾辞は拒否し、`PAD.Designer` プロセス条件と複数一致拒否は維持する。この純粋な判定のテスト成功は、実UIAによるフロー発見成功を証明しない。

固定A/Bのハーネスと入力用Robinを `.work/gate2/` に準備した。構文検査・実Appの許可構文検証まで実施し、PADへの貼り付け・実行は未実施、予定成果物2件とも存在しないことを確認した。メモ帳経由の手動貼り付け準備中に対象と異なる画面が返ったため、古い座標や対象情報で入力を続けていない。手動貼り付けの確認をAppドライバーのGate 2合格へ読み替えない。

後続の実ドライバー検証では、PADの画面と専用Edgeの接続が閉じられていることを確認した。PADコンソールを開き、検索が空の「自分のフロー」を更新しても0件だったため、既に許可された空フロー「無題」をPower Fx無効で1件作成した。名前はUIAのValuePatternで設定して読み戻した。空のMainで保存を要求し、一覧更新後に `MyFlowsListGrid` の「無題」を確認した。前回のデザイナーが永続保存されていたとは扱わない。

`a00bca7` の実 `Invoke-AgentPad` を固定A/Bハーネスから1回呼んだ。Aは `PAD_SELECTOR: control unavailable: StatusTextBlock` で、貼り付け・保存・実行の前に失敗し、Bは開始されなかった。開始/終了マーカー、送信用Robin、予定成果物は作成されていない。証拠は `.work/gate2/sessions/c2687af0aaa2432babb49ae6fce5c9e4/summary.json`。この結果はGate 2合格ではなく、修正すべきセレクターを実機で特定した証拠である。

実UIAで、保存・停止のIDがCustomラッパーで、その直下のButtonだけがInvokePatternを持つことを確認した。空のMainでは実行Buttonは無効、保存Buttonは有効、停止Buttonは無効だった。状態IDは `Flow_status_ready` / `Flow_status_saving_process` / `Flow_status_saved`。空フローの保存を1回だけ要求して50ミリ秒間隔で観測すると、約0.2秒で保存中、約5.3秒で保存済みとなった。証拠は `.work/gate2/save-signal-5eda148ced0947398fd65d7d88bc9a2d.json`。

インストール済みPADのBAML/IL/日本語・英語リソースも読み取り専用で調べた。保存済み表示は5秒間、エラー一覧の件数は警告を含み、実行・デバッグ中には非表示になる。根拠を `.work/pad-save-signals/findings.md` とアセンブリのハッシュに記録した。修正版は状態バーの一意性・正規構造・明示的な待機状態を確認してから、非表示のエラー件数を0と判定する。貼り付け・削除後は、固定時間ではなく中止・期限に対応した状態待ちを行う。修正後の実機診断でも、保存済みの空の「無題」を `available=true / editable=true / can_run=false / status=ready` と確認できた。貼り付けから実行までの再検証は別途必要である。

`e3d9a79` の固定Aでは貼り付けまで進んだが、`ProgramDetailsStatusBarItem` が取得できず保存・実行前に停止した。Bは未開始。証拠は `.work/gate2/sessions/e83d0a2b05d64208971e2bee64dda246/`。終了後のコピー読戻しは提出Robinと比較規則の範囲で完全一致し、開始/終了マーカー・成果物は0件だった。インストール済み処理の追跡で、コード一覧の貼り付けが `Updating` を設定し、その状態と保存中には同項目を非表示にすることが分かった（`.work/pad-save-signals/paste-status-followup.md`）。失敗瞬間の状態IDは記録されていないため、その瞬間の因果関係までは断定しない。

追加修正は、状態読取りに常設の状態欄を使い、非表示エラーを0と判断するReady/Saved時にだけProgram Detailsを要求する。状態待ちの既知セレクター欠落は期限内で再観測し、安定判定をリセットする。要素の重複や型・名前・操作パターンの不一致は即時に失敗とする。保存・貼り付け・実行の再送は行わない。

失敗Aの復旧では、セッション・run・提出コードとコピー証拠のハッシュを固定し、現在のコードとの一致と開始/終了マーカー・成果物の不在を再確認した。独立レビュー後、当該コードだけを1回削除し、専用Mainが空・待機状態へ戻ったことを確認した。保存・実行は要求していない。記録は同セッションの `reset-failed-paste.json`。元の失敗証拠は保持している。

`9893e49` の新規固定Aは、貼り付け・保存・実行まで進んだが、実行後の監視が `StartFlowButton` 不在で `unknown` となり、Bは開始されなかった。セッションは `.work/gate2/sessions/f696933d6baa419eb1471f609f80cc8e/`。再実行せずに読み取り専用で照合したところ、現在のPADがエラー0の待機状態、コードと所有記録の一致、開始/終了IDの一致、唯一の出力本文の完全一致という9項目を確認した。結果は `reconcile-0f27b78568ea473f872d9c48a72214dc/observation.json` に別記し、元の `unknown` を書き換えていない。これは固定Aの実処理が完了した証拠であり、アプリの自動結果判定やA/B一連の合格ではない。

インストール済みPADのBAML/ILから、実行中はStartを隠し、一時停止中のStartは既存実行を再開することを確認した（`.work/pad-save-signals/running-controls-followup.md`）。修正版では、実行状態と実際のStopが有効な場合にだけStart不在を許し、新規Runへは使わない。観測要素の欠落が続く場合は通常の実行期限と別に20秒で不明とし、中止要求を毎回確認する。停止は専用ウィンドウからその場で厳密に解決したStopを1回だけ要求する。

事後確認済みの固定Aは、独立レビューした手順で本文・所有記録・成果物ハッシュを再確認後に1回だけ削除した。Mainが空に戻り、成果物と開始/終了マーカーが変更されていないことを確認した（同セッションの `clear-verified-a.json`）。保存・再実行は要求していない。

`7a63f52` の固定Aも実出力まで進んだが、時間付き状態名を拒否して `unknown` となり、Bは未開始だった（セッション `8edd72c431254e3b9b10d6cb9839afed`）。別プロセスの読み取り専用ログは保存中→保存済み→解析中→実行中→準備完了を記録し、事後照合9項目はすべて一致した。元の不明判定は保持した。PADの状態名は実行時間が付くと `状態 {0} {1:N0} 秒` になるため、コロン付き表示名を一律必須にする判定を修正した。状態の識別には既知の20種類のID・一意な状態欄・Text型を用い、表示名は診断情報として保持する。

`49a4535`（App SHA-256 `6e30788593980f236807053a8177f7519c4cead2f3308f7a63e5bea8b5958844`）の固定A/Bは、実Appドライバーで両方成功した。セッション `.work/gate2/sessions/9bd4da3132e94ca78d6d63a559472220/` のAは8項目、Bは9項目の検査がすべて一致した。開始/終了ID、唯一の成果物、UTF-8本文、保存した所有記録を確認し、B後もAの出力ハッシュは変わらなかった。別プロセスの `.work/gate2/observers/b2114577ff9040a4b5712b022a0e77ec/` でも、両方の保存中→保存済み→解析中→実行中→準備完了を記録した。独立レビューは保存ファイルから全17項目を再計算して一致を確認した。以前の failed/unknown の記録は変更していない。

Gate 1の固定2回AiCallの準備中に、Windows PowerShell 5.1のJSON配列読取りが1個のObject配列となり、2件のテンプレートを正しく参照できない不具合を再現した。明示的な配列展開と6フィールド・IDの検証を共通化し、実ファイルの2件を本番生成関数→読取り→Robin検証へ通す回帰検証を追加した。`.work/gate1/` のハーネスは準備段階で、実プロバイダー呼出しは別の検証である。

Gate 1の実PAD貼り付け読戻し（`.work/gate1/sessions/7d2274ce4c8d47b6883a330f46eb5434/capture-be92b773d8294dafa32109816b0c6084/`）では、提出本文との差分が4つの同一エラーハンドラーだけだった。PADは各結果/status読取と同じインデントに `ON ERROR` / `END` を置き、本文だけを4スペース深く保持したため、生成規則と厳格バリデーターをその実観測形へ合わせた。`AgentAiReadFailed` への `ERROR` 設定、`THROW ERROR`、結果→statusの直後読取順、全文貼り付け比較は維持している。捕捉時は保存・実行0回、状態ready、エラー0、開始/終了マーカーと成果物なしであり、これは貼り付け失敗の診断であってGate 1合格ではない。

`9c6f49f` のGate 1再試行は `.work/gate1/sessions/a774f4aa434d447eacaf1ac42db4a285/summary.json` に保存した。保存・実行開始までは進んだが、最初の状態観測は `PAD_SUBFLOW: exactly one Main subflow is required.` で `status=unknown`、`accepted=false` のまま保持している。同じセッションの読み取り専用事後観測 `.work/gate1/sessions/a774f4aa434d447eacaf1ac42db4a285/posthoc-runtime-error.json` は、`Flow_status_runtime_error`、`Main, エラーあり,`、2行目 `DirectoryNotFound`（`control/started.txt`）を記録した。開始マーカー・終了マーカー・AiCall結果・成果物はいずれも0で、プロバイダー送信確認もない。これは保存→実行開始の進展と別の実行時エラー証拠であり、Gate 1成功や元の `unknown` の書換えを意味しない。

実行時エラーに限り、装飾されたMainタブ名と実機で確認した直下2要素の構造を厳密に照合する修正を加えた。修正版の読み取り専用実機確認は `posthoc-error-identity-fix.json` に記録し、`runtime_error`・エラー1件・`idle=false`・`can_run=false` を確認した。保存・実行は追加していない。125件の基本契約・119件のCopilot契約・281件のPAD契約検証が通過し、独立レビューもBLOCKER 0 / MUST FIX 0。保存先エラーは未解決であり、この修正は実行時エラーの検出改善に限る。

失敗した第2回Gate 1のフローは、提出本文・実PADからの全文読戻し・run/jobファイル・所有記録を照合した後、1回の削除・保存で空Mainへ戻した。過去の `unknown` と証拠は保持した（`sessions/a774f4aa434d447eacaf1ac42db4a285/clear-second-runtime-error.json`）。続く固定ファイル診断 `path-probes/aa72021029f64ee9b5be32fd0faeca0b` では、同じPAD実行のworkspace書込みが成功し、AppDataの書込みだけが3行目で失敗した。書込み前後とも作成元からは対象フォルダーが存在していた。

環境診断 `environment-probes/866fcb958b964966b7990dd3c17a73db` では、PADの既知フォルダー、子PowerShellの環境変数と既知フォルダーが同じAppDataを返す一方、子からは直下のAiPromptsAgent・キャッシュApp・要求ファイルが見えなかった。実行中のRobotV2と子PowerShellは同一ユーザー・同一セッションと確認した。作成元で既存ディレクトリのハンドルを解決すると、実体はCodexの `Packages/OpenAI.Codex_2p2nqsd0c76g0/LocalCache/Local/AiPromptsAgent` にあった（`host-view-50e2d69420094d0abe688449a9860207/observation.json`）。現物Codex manifestの新しい仮想化宣言はLocalAppData/OpenAIだけを除外し、Windows 11ではこの宣言が旧disabled指定に優先する。[Microsoftの仕様](https://learn.microsoft.com/en-us/windows/msix/desktop/flexible-virtualization)。今回の保存先不一致は検証を起動したCodex環境に由来し、製品の既定保存先やPADの権限設定は変更しない。上記のLOCALAPPDATA検証もこの実体に対する証拠であり、通常ユーザー起動の非仮想化領域を検証したことにはしない。

環境診断の3出力と終了GUIDは生成されたが、終了観測で状態表示と停止ボタンの有効状態が一致せず、元の結果は `unknown` のまま保持した。事後観測 `posthoc-d9c4b4291c8a45a985cb775211235751` で同じフロー全文・ready・待機中・エラー0を確認した。この正確な観測不一致だけを期限内の読取り直し対象へ追加し、状態判定・操作の再送条件は変えていない。一時不一致からの復帰、持続時の期限切れ、類似文言と型違いの拒否を含むPAD契約検証は301 PASS、独立レビューもBLOCKER 0 / MUST FIX 0。実AiCall・M365送信はこの診断に含まない。
実体パスを明示した診断 `physical-probes/437c276f2d65452db102fa9c9308137d/result.json` は7アクションで成功した。PADが書いたGUIDを同じPADと子PowerShellで読み戻し、子が既存の不変Appライブラリ（b14062cf…）をハッシュ照合して読み込み、従来は見えなかった要求ファイルの存在を確認した。controllerはf0d5791、削除・貼付け・保存・実行は各1回、終了はready・エラー0、provider呼出し0。旧環境診断の12ファイルとApp所有記録は変わっていない。これは保存先の解消を示す固定診断であり、AiCallの成功証拠ではない。

同じ実体HomeでJSON更新を試すと、対象229文字・一時ファイル256文字は作成できても、265文字のバックアップを伴うFile.Replaceが失敗した。バックアップを同じ親の独立GUID名へ短縮すると257文字となり、更新と旧内容の保存が成功したため、本体のWrite-AgentJsonもこの命名へ変更した。原子的な置換と成功・失敗時の一時ファイル清掃は維持する。Windows PowerShell 5.1で長い保存先の作成・更新・ロック時の旧JSON保持を含む133項目が通過し、独立レビューもBLOCKER 0 / MUST FIX 0。実体Homeでの本体再検証も成功した（`physical-home-json-a162063d41084633b839c021e4254f11.json`）。この再検証記録のbackup_length欄だけは検証スクリプトの旧式計算が残ったため、元記録を保持して別の `.metadata-correction.json` に257文字と訂正し、検証スクリプトの計算も修正した。

アプリの正式な `/api/copilot/open` から専用Edgeを起動できた。初回の同期確認は利用者の操作対象とし、自動応答していない。その後、専用ポートと専用プロファイルのプロセスが終了したことを読み取り専用で確認した。利用者から「もう一度m365 copilotを開いて」と依頼され、同じ機能から再度開いた。M365への業務プロンプト送信、認証完了、応答取得は未検証。

再起動時に余分な `about:blank` が残るとの報告を受け、明示的な空タブ起動と別のCopilotタブ作成が原因だとソースで確認した。今後の初回起動では空タブに一意の値を付け、Copilotまたは認証タブの表示後、その値・対象ID・専用プロファイル・接続先を確認して当該タブだけを閉じる。変更済み・曖昧・終了確認不能の場合は追加操作しない。既に開いている普通の空タブや拡張機能のタブは閉じない。修正の実ブラウザー検証は未実施。

専用EdgeのChatGPT拡張機能を読み取り専用で調査した。バージョン `1.26.901.11451`、無効化理由 `[1024]` を確認した。この値は[Chromiumの定義](https://github.com/chromium/chromium/blob/main/extensions/browser/disable_reason.h)では `DISABLE_CORRUPTED` に対応する。拡張機能の `background.js` に、初回インストール時に機能フラグが有効なら `/work/extension/installed` を開く処理も存在した。案内タブが開く仕組みと破損判定の発生原因は分けて扱う。拡張機能・認証・同期・ブラウザーのセキュリティ設定は変更していない。

拡張機能の検証対象1,629ファイルは欠損がなく、4,096バイト単位のSHA-256とメタデータ内のツリールートがすべて一致した。別のmanifestとアイコン4件は[Chromiumがインストール時変換のため検証から除外する対象](https://chromium.googlesource.com/chromium/src/%2B/lkgr/extensions/browser/content_verifier/content_verifier.cc)に一致する。署名そのものは未検証であり、破損判定の発生時点・原因・復旧は確認できていない。限定した診断記録は `.work/chatgpt-extension-integrity-20260905.md` に残した。

空タブとPADタイトルの修正版を `Bootstrap -NoBrowser` で実LOCALAPPDATAへ同期し、HTTP成功、App.ps1のハッシュ一致、フロー設定「無題」、実行中ジョブなしを確認した。同期は専用Edgeの起動・終了やタブ操作を要求しない。

固定A/B成功版もLOCALAPPDATAへ同期した。そのアプリからM365を開いたところ、Copilotのタブは開き入力欄もREADYだったが、起動時に渡した一意な `about:blank#...` はCDP一覧になく、別の `edge://newtab/` があった。専用Edgeのプロセス引数には識別子が届いていた。未確認の新規タブを閉じる操作はしていない。この場合は、確認済みのCopilotタブが開いていることを成功とし、起動タブの後処理は警告として返すよう追加修正した。重複・変更・不明な所有のタブを閉じる許可には使わない。

固定ファイル診断の成功後、同じ7アクションの全文を2回照合し、1回の削除・保存で空Mainへ戻した（`physical-probes/437c276f2d65452db102fa9c9308137d/cleanup-once/result.json`）。終了は保存済み・エラー0・実行不可であり、実行要求0、診断・旧Gate 1・所有記録は保持した。

専用Edgeの入力欄を本文を保存せずに調べると、空のSPAN/P/BR構造からinnerTextだけがLFを1文字返していた。この厳密な空構造だけを空文字に正規化し、実際の空白・改行・不可視文字・未知の入力構造は保持する。実装したDOMコードを隔離Edgeで評価する51項目と既存Copilot契約119項目が通過し、独立レビューも通過した。7ページ遷移はすべてローカルfixtureで応答し、実サービスへ転送していない。実M365でも修正版を読み取りだけで確認し、入力候補1件・正規化後0文字・生成中でないことを確認した（`copilot-empty-editor-verified-6ab9ff6113284410bce44473212ebed6.json`）。入力の消去、送信、タブの再起動は行っていない。

Windows起動経路の読み取り専用診断では、単なるShell.Application呼出しはCodex側のpwshを親に持ち、同じ仮想化領域を見た。デスクトップExplorerのautomation objectを介した呼出しはexplorer.exeを親に持ち、PADと同様に通常領域のAiPromptsAgentを未作成と判定した（`launch-context-probes/3cb3c628a97a40b5ab5b1b6d34614f0d.json`）。AppData作成・PAD実行・provider送信は0。この経路での導入や固定AiCallは未実施である。[MicrosoftのExplorer起動資料](https://devblogs.microsoft.com/oldnewthing/20131118-00/?p=2643)

修正済みの `16c0761` の3ファイルを専用共有へ公開した。App.ps1を1回の原子的な置換で更新し、旧3ファイルを別のバックアップに保持した。ローカル共有とUNCの新ハッシュ、バックアップの旧ハッシュ、共有権限とNTFS ACLの不変を確認した（`gate0/publish-latest/33b62f2a328c414b884b295055572a4d/result.json`）。

Desktop Explorer経由で共有CMDを1回起動した結果、終了コード0で通常のLOCALAPPDATAへ新キャッシュとサーバーが作成された（`gate0/normal-context/4c894cdeaf154913a8d8682db29b4f5e/result.json`）。通常Homeの最終実体パスも一致したが、後続のキャッシュ・サーバー検証は失敗として保存した。起動引数には期待文字列がすべて含まれ、末尾の空白1文字を除いた場合だけ末尾比較が一致した。元の失敗記録を書き換えず、既に起動したサーバーを読み取り専用で確認する。

同じ切替の旧履歴検証は、Codex側の結合されたフォルダー表示に新キャッシュ3ファイルが加わったため全体ダイジェストが不一致となった。元の45ファイルを仮想化領域の明示した実体パスと従来の表記の両方で再計算すると、45件すべてのハッシュが一致した（`gate0/normal-switch/4c894cdeaf154913a8d8682db29b4f5e/posthoc-private-history-74f96136e82f44a393f94b5bdfd62809.json`）。元の切替結果は `unknown` のまま保持し、導入を再実行していない。

通常Explorer環境からの事後確認では、元のキャッシュ検査は成功し、起動引数の末尾比較だけで同じ失敗を再現した。Windowsの引数解析では12個すべてが期待値と一致した。通常Homeの実体、新キャッシュ3ファイル、current.json、PS5サーバーのPID・開始時刻・localhost待受所有者、HTTP 200・版0.1.0・jobなしを確認した（`normal-context/4c894cdeaf154913a8d8682db29b4f5e/posthoc/913dbf5462d34bdfb597a542269c4df1/result.json`）。この確認は読み取りだけで、導入や設定変更を再実行していない。復旧側の例外も、StrictMode下で空の関数出力へ `.Count` を参照した検証スクリプトの不具合と特定した。新サーバーが稼働しているため旧サーバーの復旧起動は不要である。

設定引継ぎは別の1回のPOSTで成功した。通常HomeのAPI・設定ファイルが `copilot_port=9223`、`pad_flow_name=無題`、`max_rounds=6` で一致し、jobなし、source・cache・旧設定が不変だった（`settings-recovery/9d1af217e38b4b1b82fc6d751b2893e4/result.json`）。旧45ファイルも再び全件一致した。

第3回の固定AiCall実機検証は、通常Explorer環境と新キャッシュから1回実行した（`gate1/sessions/e696488ae08f43e094ce27f8aadcd795/summary.json`）。今回はPADの開始マーカー、最初のAiCall claimと結果ファイルまで進み、PADと子PowerShellが同じ保存先を利用できた。翻訳AiCallは `failed / connection / input_count=1 / output_count=0`、分類は未実行だった。ジョブ専用Copilotタブは作成されたが `has_sent=false` で送信試行記録はなく、業務プロンプト送信は確認していない。PAD観測は `PAD_SUBFLOW` により `unknown` のまま保存し、通常サーバーは復旧した。

第3回の事後UIA確認では、既存の厳密条件で `Main, エラーあり,` を取得でき、Main 5行目・エラー1件・停止中・17アクションを確認した。元の11 runファイルとjob・summaryは不変だった。Copilotの事後確認も接続・空の入力欄・会話なし・生成なしで成功した（`copilot-posthoc-2d0485b26fdc4e43b1c89a7e84508726.json`）。元の接続失敗の箇所は未特定で、初期タブの表示遷移を区別する診断が必要である。いずれも事後確認を元の失敗結果の置換や再送には使っていない。

新しい診断用タブを1件だけ作成し、実関数の作成→接続→最初のsnapshotを計測した。この試行の初回接続は成功したが、入力・送信0回のまま、後続snapshotで `generating=false→true→false` と変化した（`gate1/copilot-startup-probes/9c04fc30773e4288960e4425ae8fbfe1/result.json`）。その間も入力0文字・assistant 0件で、生成中と判定された時点のdocumentはinteractiveだった。これは初期表示中の判定変化の証拠であり、元のAiCall接続失敗の原因確定ではない。既存3タブと16ファイルの不変を確認し、診断タブも未送信のまま保持した。

第3回フローの最初の復旧は、PADの前面化を確認できず、削除・保存前に停止した（同セッションの `cleanup-once/result.json`）。標準UI AutomationのWindow.SetFocusで対象を前面化できることを確認し、その後も既存の前面・workspace確認を通す手順を独立レビューした。別の1回の復旧は、本文2回の一致確認後に削除1回・保存1回で成功した（`cleanup-after-focus-4acf38684dc64e6bb656bd94d0a9a1d9/result.json`）。終了は保存済み・空Main・エラー0・実行不可で、実行要求0。現行19ファイル・旧45ファイル・前回復旧5ファイルと所有記録を保持した。

次の診断用タブでは16回のsnapshot内で、productionの生成判定と同じ評価から原因要素を記録した（`gate1/copilot-busy-probes/17f3341dbb64416883a37b0b3960c807/result.json`）。入力・送信0回、空欄・assistant 0件のまま、1回だけ可視の `DIV[role=status][aria-busy=true]` が現れた。停止ボタンとstreaming属性はなく、約0.5秒後には消えた。documentがcompleteでもこの一時状態が発生することを確認した。旧20ファイル・既存4タブを保持し、新しい診断タブは未送信のまま残した。これは読み込み中の生成判定を再現した証拠であり、元のAiCall失敗瞬間の原因を断定するものではない。

送信前のfocus確認に15秒の共有期限を設け、生成判定中だけ入力せず再観測するよう修正した。snapshot後にbusyへ変わった場合も待機し、接続・focus失敗、入力消失、所有権喪失、初回ジョブの下書きや会話の出現は停止する。生成判定、全体期限・中止、4キー・本文挿入・送信を各1回に限定する規則は維持した。従来の入力欄出現待ち15秒は別に保持する。PADはnative前面化が成功しなかった場合だけWindow.SetFocusを1回試し、既存の前面・workspace確認を必須にした。基本契約133件、Copilot契約147件、PAD契約302件と隔離Edge DOM64件が通過した。DOM検証の7ページ遷移はすべてローカル応答で、実サービスへ転送していない。

修正版 `2b8207a`（App SHA-256 `858ba1de5a36392f3656b3ed0f9c56d7a6ce2f5bac16b5a97c8b2640cc267041`）は独立レビューを通過した。専用共有を1回のApp置換でrelease `0.1.0-b539c6916b80aefe7493e85b3e748b8cb9e2509be5447b124e37e80c04db0025`へ更新し、旧3ファイル・ACLを保持した（`gate0/publish-latest/2ff3f86f239945beb39352414d65aa1e/result.json`）。

通常Explorerから実共有CMDを1回起動した更新検証も成功した（`gate0/normal-updates/e1f56d5f17cb43b889700a456ce95bb8/result.json`）。CMD終了コード0、新しい通常Homeのキャッシュとcurrent.json、PS5サーバーのPID・開始時刻・Windowsで解析した起動引数・localhost待受所有者・HTTP応答・設定を照合し、旧サーバーの終了を確認した。現行ジョブ15ファイル・所有記録・設定・旧キャッシュ3ファイルの計20件と、Codex仮想化領域の45件は不変だった。helperから直接のPAD操作・Copilot送信・再起動API要求は行わず、更新と旧サーバー終了は製品の起動処理が行った。

第4回の固定AiCallは通常環境で新規IDを作り1回実行した（`gate1/sessions/ba98d1a912f74425b3700229699e8888/summary.json`）。最初の翻訳AiCallは再び `failed / connection` だったが、今回は製品のPAD監視が `failed / AICALL_connection` と検出した。分類・成果物出力は未実行で、通常サーバーは復旧した。外側の検証結果は `unknown / accepted=false` として元のまま保持する。実行前に旧所有記録を別ファイルへ保存し、終了時も旧normal 19ファイル・private 45ファイル・旧所有記録バックアップ・既存5タブの保持を確認した（`gate1/normal-executions/5afea4b151a049f6914b45e402de60ed/result.json`）。

第4回の事後確認では、ジョブ専用Copilotタブの入力が1273文字で、入力候補1件・送信ボタン有効・生成なし・assistant 0件だった（同セッションの `copilot-posthoc-5ae1512f82a443a289740a20201d8fc0.json`）。入力先にもfocusがあり、空の入力欄から本文入力まで進んだことを確認した。ただし `has_sent=false` であり、送信は確認していない。PADはMain 5行目の実行時エラー1件・17アクション・実行不可だった（`cleanup-once/uia-observation.json`）。いずれも読み取りのみで再送・再実行していない。

元のrequest・inputと製品内のAST代入式から送信予定本文を副作用なく再構成すると、期待した1271文字が実入力の先頭から完全一致し、改行3箇所も一致した。差分は末尾のU+200B・U+200C各1文字だけだった（`input-comparison-ca78585136e6447c8d774a585a5062c1.json`）。DOMはSPAN→P→2つのSPANで、最初のSPANは `data-lexical-text=true` の本文1271文字、後ろのSPANだけは `data-lexical-text=true / aria-hidden=true` で唯一のテキストノードが当該2文字だった（`input-suffix-2a80573875d14d729df7f4873e3924e2.json`）。この構造が現在の完全一致検査を不成立にすることを確認した。失敗瞬間の例外自体は保存されていない。旧19ファイルの不変と入力・focus・送信0回を確認した。実測した本文SPANと末尾のaria-hidden SPANだけを厳密に識別し、末尾マーカーだけを比較対象から除く修正を加えた。本文中の不可視文字・改行・空白、属性違い・未知の構造は保持する。Copilot契約147件、隔離Edge DOM99件が通過し、独立レビューも通過した。実M365の同じ未送信入力を修正版で読み取るだけの検証でも1273文字から1271文字となり、送信予定本文のSHA-256と完全一致した（`draft-input-verification-7c8e857e5b03473e8a77b47c57226b0c.json`）。この確認で入力・focus・送信・タブ操作は行っていない。

第4回の失敗フローも、独立レビュー後に全文2回の照合と1回の削除・保存で空Mainへ戻した（`sessions/ba98d1a912f74425b3700229699e8888/cleanup-once/result.json`）。終了は保存済み・エラー0・実行不可で、実行・provider呼出し0回。第4回の19ファイル、旧normal 19ファイル、private 45ファイルと旧所有記録バックアップは不変だった。

末尾マーカー修正版 `928b2f6`（App SHA-256 `b738672013e90ddf5de886dba7605bf0c72a0cb8ad419e047669f48307676919`）をrelease `0.1.0-5c4ef7d98162d2c5bbe28ef50f6ba6b9d7c12190f00e931fbcba8a05a88f3adb`として専用共有へ公開した。原子的なApp置換1回、旧3ファイルのバックアップとACL保持を確認した（`gate0/publish-latest/2fed9d4c4cd349c6b1a1a9c62b1d5392/result.json`）。通常Explorerからの共有CMD更新も終了コード0で成功し、新キャッシュ・サーバー・設定・引数・HTTP応答の一致、旧サーバー終了、現行20ファイル・旧normal19・private45・旧owner archive・第4cleanup証拠の不変を確認した（`gate0/normal-updates/3d66440be9c9409e860bcebbba604b63/result.json`）。

第5回の固定AiCallは新規ジョブで1回実行し、今回は本文の完全一致、送信クリックの応答、英訳回答まで進んだ（`gate1/sessions/501899397d424602a8e399e5e53f95ff/summary.json`）。最初のAiCallは `failed / invalid_response`、PADの監視も `failed / AICALL_invalid_response` で停止し、分類と成果物出力は未実行だった。通常サーバーは復旧し、外側 `normal-executions/32286c2453214a53b09ab57e06411cb4/result.json` のunknownは元のまま保持した。旧normal19＋19、private45、旧owner archive、既存6タブは不変。今回の旧ownerは別ファイルへバックアップした。事後snapshotでは入力0文字・assistant1件・生成なしで、正しいID群と英訳を含むsuccess JSONがあったが、取得した本文に必須の `AGENT_END_<request_id>` がなかった（`copilot-posthoc-dc2bdcdb615247e8b28b2d4207f3fed4.json`）。追加の読み取り専用DOM確認では、assistant候補は `markdown-reply` の1件だけで、`lastChatMessage` を含む4段階の祖先とその直下要素もすべて同じ330文字だった（`copilot-posthoc-5b22513e45434989a890343233466b3d.json`）。この回答では取得範囲の切り捨てではなく、表示された応答自体に終端がない。「JSONだけ」と「次行に終端」の指示を必須2行形式に統一する修正を別draftで準備し、終端なしの受理や事後補完は行わない。

第5回の失敗フローも、独立レビューと本文2回の照合後、削除1回・保存1回で空Mainへ戻った（`sessions/501899397d424602a8e399e5e53f95ff/cleanup-once/result.json`）。保存済み・エラー0・実行不可、Run/provider呼出し0回。今回の20ファイル（送信済みattemptを含む）、旧normal19＋19、private45と両owner archiveは不変だった。

2行指示のdraftだけを用いた新規の翻訳診断は、実Copilot呼出し1回・再送0回・PAD操作0回で実行した（`gate1/two-line-response-probes/a786d45c23824b50957b17a9b1de7909/result.json`）。今回の回答には正しいJSONと終端があったが、本文取得値では改行が空白となり、厳格な終端照合が通らず `unknown` となった。旧112ファイルと既存タブは不変だった。読み取り専用の追加観測では、可視の `DIV[data-testid=markdown-reply] → DIV → P → 単一テキストノード` にJSON・LF・終端がそのまま存在し、`innerText` だけがLFを空白へ変換していた（`copilot-posthoc-f6b8aae1381442ecbbf58fe93f5e21ae.json`）。元のunknownは保持し、応答の補完や終端規則の緩和はせず、取得処理の修正を別draftで検証する。

指示を2行形式へ統一し、実測した可視の単一テキストノード構造だけから原文を取得する修正を実装した。未知の構造は従来の取得方法を保持し、終端や改行の補完は行わない。修正前の取得では拒否される同じ実応答を、修正版では2回とも元テキストと完全一致で取得し、既存の厳格なJSON/終端/ID検証を通過した（`copilot-two-line-draft/7f539df426734827adc35e3042d25411/readonly-reader-1b7075adb66c4591bef244426855cdf1.json`）。基本137・Copilot154・隔離Edge DOM219件が通過し、独立レビューも通過した。DOMテスト初回のflexによる表示形式変換のfixture誤設定と、その修正も `dom-validation.json` に記録した。

新しい要求IDによる翻訳診断 `bc551ffcb5844e5182e607d3cd022a10` は、通常Explorer環境で実Copilot呼出し1回から正常に返却された。JSONと実LFと終端を含む厳密な2行、要求/ジョブ/run/AiCall ID、success・入出力各1件、取得JSONと再読取り2回の完全一致がすべて合格した（`gate1/two-line-response-probes/bc551ffcb5844e5182e607d3cd022a10/result.json`）。実行は2026-09-05 20:24:38〜20:25:14 UTC、既存115ファイル・既存8タブ・通常サーバーは保持され、再送/再試行/PAD操作は0回。過去のunknownは変更していない。適用したApp SHA-256は `32958784b503b9316c5b61d68bc1008f879f527242033e95263e7c1e15d97b00`。この診断はCopilotアダプターの実経路の証拠であり、Gate 1の固定PAD完走ではない。

修正版をコミット `b9730e5`、release `0.1.0-f771e1b04ff57d7aa960c58e14b5741eb1ce70b8d4e13a529e91ea0167126f97` として専用共有へ公開した（`gate0/publish-latest/d16a2ab3cb364b4fa193264c0e1d7871/result.json`）。Appの原子的置換1回、旧3ファイルのバックアップ、共有のローカル側・UNC側の新3ファイル一致、共有・NTFS ACLの不変を確認した。通常Explorerからの共有CMD更新も1回で終了コード0となり、新キャッシュ・サーバーPID32352/port57702の版・引数・設定・HTTP応答と旧サーバー終了を確認した（`gate0/normal-updates/5a91f82533024bcc930018b8969c4316/result.json`）。通常63ファイル、private51ファイル、過去のowner archive2件と第5回cleanup証拠は不変だった。

第6回の固定PADは新規ジョブ `1256aa873d27415f868fbec1cad6e0d6` で1回実行し、正常完走した（`gate1/sessions/8ead1dc2a51742e6b700a84f57127e20/summary.json`）。開始・終了マーカー、提出コードと所有記録、宣言2成果物と実際の2成果物、翻訳と分類のsuccess、英訳の同一フローへの受渡し、review分岐がすべて合格した。英訳成果物は `This contract contains notes that require human review.`、分類分岐成果物は `review` で、原文と指定分類条件に合っている。翻訳の意味を自動的に保証した記録ではなく、本文を別途読んで確認した。

この実行は2026-09-05 20:44:36〜20:45:44 UTC、外側の実行記録もaccepted=true/status=passedである（`gate1/normal-executions/b33c495787414bf2a810613900b67a04/result.json`）。通常サーバーは同じreleaseのPID25544/port53708として復旧した。通常の旧62ファイル、private51（旧45を含む）、旧owner archive2件、既存9タブを保持し、直前ownerは別ファイルへ保存した。元の失敗・unknownと成果物を上書きせず、実PADで正常な直列AiCallと結果分岐を確認した最初の合格である。拒否・空・タイムアウト・中止の実機異常系はこの合格に含めない。

Gate 3の初回 `df207bbf633e42f5abb4288b77030ee5` は、短文要求1回の送信後、`RESPONSE_INVALID` によりunknownで停止した（`gate3/sessions/df207bbf633e42f5abb4288b77030ee5/result.json`）。長文要求は未送信、PAD/再送/タブ終了は0回。通常84ファイルと既存10タブを保持し、補助の `private-after.json` でも明示的private Homeの51ファイルの不変を確認した。

読み取り専用の事後観測では、assistant1件・入力0文字・生成終了、本文1336文字は可視の単一テキストノードと完全一致し、正しい実LFと終端を含む2行だった。しかしJSONのartifacts内に不正な `\U` escapeがあり、厳格な構文検証を通らない（`copilot-posthoc-e93b9021a31e4df9a5f2a91ecefddc05.json`）。生成元の誤りか表示前のMarkdown処理による変換かは、レンダリング後のDOMだけでは区別できない。バックスラッシュの補完やJSON修復は行っていない。

応答コピーの診断 `c05c30524ee94ecf8f46e0dd35ebe077` は2026-09-05 21:17:47〜21:17:54 UTCに1回だけコピーした（`gate3/copy-probe/c05c30524ee94ecf8f46e0dd35ebe077/result.json`）。取得値1334文字は表示用innerTextと完全一致し、実LFが0個、二重空白も縮約され、JSONも不正のままだった。元のクリップボードは全形式の対応データをメモリ内へ独立退避し、復元後の形式・型・内容を照合して復元成功を確認した。既存150ファイルと11タブを保持し、provider送信/PAD/権限変更は0回。この結果も生成元の原文を示さず、原因の判定はinconclusiveである。次は単一textコードブロック内のJSON＋終端を用いる新規の短文診断を準備する。製品への採用や長文取得の成功は未確認。

コードブロックの新規診断 `a7d40210341141d6876928f3e6f60147` は、プロンプト3文字列だけを変更したdraft `8036c7548c47ac6088cd226e3233c0ead604de123645ee7865ea8f714a07ecc3` で実送信1回を行った。現readerは行番号・言語ラベルを含め、表示オプションの閉じたメニューをcollapsedと判定するため、元の実行はRESPONSE_INVALID/unknownで保存した（`gate3/fenced-diagnostic/sessions/a7d40210341141d6876928f3e6f60147/result.json`）。実行後の2回のDOM観測は64ノードの全構造と全textnodeが一致し、本文はdata-line-indexの0・1として存在した。各行の本文を変更せず論理行境界で結合した追補検証では、未変更の厳格JSON/Planner検証と65文字の復号値完全一致がnative PS5/STAでも合格した（`posthoc-decoded-review-native.json`）。日本語、引用符、apostrophe、Windowsパス、literal backslash-n、実LF、percent、Markdown記号、前後2空白が保持された。通常/private/旧証拠169ファイルと既存11タブを保持し、PAD/再送/clipboard/latest変更は0回。これは短い搬送用文字列の追補検証であり、製品readerの成功や生成Robinの長文合格ではない。

実測したコードブロック構造に限定する本文取得を実装し、計画・AiCall・送信時の共通指示を同じ形式に揃えた。既知の本文2行の文字だけを保持し、余分な要素・行・隠れた本文・未確認の構造を拒否する。表示オプションの閉じたメニューと本文の折り畳みを区別し、厳格JSON/終端/ID検証は変更していない。native PS5/STAの基本137・Copilot170、隔離Edge DOM366項目が合格した。実際の既存応答でも修正版App `8617c3aefb1d2b171da43ac1f79e4b9b5a65d75c6fb352dee76a070411ff0a1e` を読み取り専用で2回使用し、source_kind=fenced_plaintext/collapsed=false、本文ハッシュ一致、65文字の復号値完全一致を確認した（`gate3/fenced-diagnostic/sessions/a7d40210341141d6876928f3e6f60147/live-product-reader-37fc73617ada423ea40c4fa4774b65f0.json`）。この照合での送信・入力・clipboard・PAD操作は0回。旧unknown結果は保持し、生成Robinの新規短文・長文取得は別の検証として残す。
本文取得修正は独立レビューで必須修正0となり、`6d46ededc65e5546f1f9eea6d60034c97614f98b` にコミットした。公開セッション `909eae638a6745588d73d8216e5a730e` はAppを1回の原子的置換で共有へ反映し、旧3ファイルの保存・UNC本文・共有設定とACLの保持を確認した。通常環境の更新 `cd7d11c27e784e7191c69f9e023f0112` は、待機中の旧serverを認証付き終了要求1回で閉じ、実UNC CMDを1回起動してexit 0、新release `0.1.0-49e2d042e35ce8e9a3f9cab4fc8513d3998e1281af62e29c2f3acf86a9412239` のserver PID33172/port52365を確認した。設定・HTTP待機状態と、通常98/private51/所有記録archive3の計152ファイルの保持が合格した。PAD・Copilotへの直接操作は0回。CMDによるローカルHTML起動は製品既定の動作として記録した。
新版でのGate 3 `7688bbc3eb814afdb301ca55fe1e3f79` は短文の実送信1回後、折り畳まれた応答を拒否して `RESPONSE_INVALID/unknown` となった。長文は未送信、PAD・latest変更・再送は0回。実行開始時の既存3タブ・通常91ファイルを保持し、別追補でprivate51ファイルの全ハッシュ保持も確認した。最初の事後観測は祖先16階層の上限でincompleteとなったため保持し、別スクリプトで上限だけ64へ増やした。2回の完全観測は本文64ノードと39祖先を記録し、300px枠を超える本文と可視の「その他の行を表示する」を確認した（`fenced-observation-9fa821c656114cd3a85414c4884f6d5b.json`）。

同じ採取済み2論理行を変更せずに行境界だけで結合したnative PS5/STA追補は、厳格JSON/Planner/Robin検証を通過した。復号後のコードは881文字・7行・4アクションで、空行・特殊文字・2つの出力先を含む期待値と完全一致した（`captured-payload-review-f3628ef2b37d4e80bfc5ec1783a338aa.json` と `short-content-review-f7e40567fc0b4d1da7badfd3f6d9018a.json`）。過剰escapeの疑いは実文字の検査で否定された。これは折り畳まれたDOMから採取した値の診断であり、製品による取得成功や元のunknownの書換えではない。該当応答だけを展開する操作と、展開後の本文取得は別途検証する。
事後展開 `0c94e99aa7984fd1b558c8177e0eeba2` は、専用target・要求ID・元本文64ノード・ボタンの所有と可視性を照合し、claim保存後に当該「その他の行を表示する」を1回クリックした。前後各2回の完全DOM観測で本文2行の文字とハッシュは不変、旧結果・所有記録等も保持された（`fenced-expansion-0c94e99aa7984fd1b558c8177e0eeba2.json`）。展開後はeditorがmaxHeight=none/overflow=visibleとなり、ボタンのラベルが「簡易表示」へ変化した。実スクリーンショット `expanded-response-c22e3017c46e4e579f95fae49d12f78e.png` でもJSONと終端の全文を目視した。既存readerは未対応の展開後構造を引き続き拒否しており、製品への既知構造対応・新規要求での自動展開は別途検証する。provider/PAD/再送は0回。クリックに伴う内部のフォーカス等は、helperが明示的に呼んだ操作回数とは区別する。
実測した折り畳み・展開済み・非表示Moreの3構造を共通の本文判定へ実装した。折り畳まれた新規応答は、要求ID・assistant key・本文の厳密一致、入力空欄と生成終了、3回の安定読取り、ボタン所有・可視性・hit-testを確認して1回だけ展開する。展開後も同じkey・本文と3回の安定読取りを要求し、未知の構造や残った折り畳みを全文として受理しない。旧回答はkeyと本文の両方で除外し、送信と展開の再試行は行わない。

App SHA-256 `126ade09ba1a888969030c0de8e0b4d9a4f51aaa8d8a1aa08273e81450650d9f` はnative PS5/STAの基本137・Copilot205、隔離Edge DOM483項目が合格し、独立最終レビューは必須修正0だった。実画面の既存の展開済み応答を製品readerで2回読み、fenced_plaintext/collapsed=false、本文ハッシュと881文字のRobin・2成果物が完全一致した（`gate3/sessions/7688bbc3eb814afdb301ca55fe1e3f79/live-expanded-reader-a8f9fc304aa54f7883c001f3290d8aee.json`）。この照合での入力・送信・展開・PAD操作は0回。過去のunknownは保持し、新規要求で自動展開を伴う短文・長文E2Eは未実施である。
展開修正版を `a4db3aedd4d0f8dae42b6fbf9adfa77886331073` にコミットし、release `0.1.0-c1cc39f7dbe34a6a39e6885790278567d6dae470019d12a93ed1e6a8c5d65c7d` として共有へ反映した（`gate0/publish-fenced-expand/1ef79c048c99450bb24ba252177bf9d9/result.json`）。原子的置換1回・旧3ファイル保存・ACL保持を確認した。通常Explorerからの更新は旧serverの認証付き停止1回、実UNC CMD1回/exit 0、新server PID19372/port58508の版・設定・HTTP待機を確認し、通常105/private51/archive3の計159ファイルを保持した（`gate0/normal-updates-fenced-expand/76cba680c3864109817ac187a34b7c26/result.json`）。

この版による新規Gate 3 `11dbbf29e92b4f16b7272c8106f18573` の短文は、送信1回から製品による全文取得・再取得・厳格JSON/Planner/Robin検証まで成功した。881文字・7行・書出し2件、特殊文字と空白を含む期待コードが完全一致した（`short/result.json`）。別の事後DOM観測2回も同じ本文64ノードとハッシュを記録し、editorのoverflow=visible/maxHeight=noneと「簡易表示」を確認した。製品呼出し以外にこの応答を展開した操作はなく、新規応答の自動展開後の状態を確認できた（`fenced-observation-b2871a0a5d8d4b3cafdb1ebaa236c8b7.json`）。

続く182件・約57,903文字を要求した長文では、正しい要求IDと終端を含む応答を取得・再取得したが、state=ACT、robin空、artifacts空配列だった。未変更のPlanner検証がRESPONSE_INVALIDとして拒否したため全体結果はfailedである（同セッションの `long/returned-raw.json` と `result.json`）。原因を出力上限と断定せず、約6万文字の生成成功とは扱わない。実送信は短文/長文各1回、PAD・再送・タブ終了・latest変更0。開始前の4タブと旧ファイル、private51ファイルを保持した。次の24件の長文は別fixture・別IDで測定し、この失敗結果は保持する。
24件の別fixture `2551ea0f304746c2809fe7ebfb5ec7f3` は、先行短文の送信1回後にRESPONSE_INVALID/unknownとなり、長文は未送信だった。旧5タブと既存ファイル、private51ファイルは保持した。完全DOM観測2回は68ノード・3論理行を記録し、JSON1392文字・終端42文字に加え、末尾のindex=2に単一のNBSP（U+00A0）があった（`fenced-observation-235839a5986148e592c26faa59f54175.json`）。現readerの64ノード・2行限定がこの構造を拒否することを確認した。

採取した全3行を文字変更せずLFで結合した1437文字は、既存の厳格な応答・Planner・Robin検証を通過し、期待した881文字の短文コードと完全一致した（`three-row-nbsp-parser-review-41641866b0dd4c95bd44cf2bc097b2a4.json`）。NBSPが表示用の代替文字だとは断定せず、実測した唯一の末尾NBSP行を含む68ノード構造への対応を実装した。既存parserの末尾空白許容や送信指示は変更していない。

App draft `d02fc03ddb6177f5507047d9c42994765f1b92e749773775b31f020bdaab900e` で同じ実画面を2回読み取り、全3行・末尾LFとNBSP・1437文字のハッシュ一致を確認した（`live-folded-tail-reader-181d47c74e96444e8b0b9ab0dee02792.json`）。折り畳みはfenced_collapsed/trueとして保持し、通常parserが折り畳み専用の期待エラーで拒否することも確認した。取得値の保持を確認する読取り専用の診断であり、元のunknownを成功に変更していない。入力・送信・展開・PAD操作は0回。
末尾NBSP対応版ではnative PS5/STAの基本137・Copilot215、隔離Edge DOM618項目が合格し、独立最終レビューは必須修正0だった。元の2行経路と失敗時の拒否を維持し、3行目の別文字・複数NBSP・余分な行・属性やgeometry変更、展開後の末尾変化を拒否することを検査した。実画面の読み取りと折り畳み拒否までを確認しており、新規要求での展開・長文取得は未完了である。

末尾NBSP対応を `80df2ff2535292927f2ea65c118e88d076effaa4` にコミットし、release `0.1.0-358335e401cb305e109a83f8d16385953a5a4490d08fccb3474f344a8bae6629` を専用共有へ反映した（`gate0/publish-fenced-tail/6f09157162784aa29127756980cb7c05/result.json`）。旧配布とACLを保持した。通常環境の更新 `28b0398df75d4228a4056205c5067f84` も実UNC CMD1回/exit0で成功し、新server PID33328/port64298の版・設定・HTTP待機と、通常117/private51/archive3の計171ファイル保持を確認した。

同じ版での新規診断 `2cb92123e6bf49a9b5517d2a40864520` は短文1回後にunknown/RESPONSE_INVALID、長文は未送信だった。完全DOM観測2回は60ノード・1論理行・1319文字で一致し、表示されたJSONは2件目のartifactsパス途中で終わり、閉じ括弧と終端マーカーがなかった（`fenced-observation-b62006c0bc3b46d58fec1046238bada3.json`）。生成終了・入力空で安定しているが、providerの生データは観測していない。独立レビューでも不完全な応答の拒否は妥当と確認した。本文の修復や再送は行わず、旧6タブ・既存ファイル・private51ファイルを保持した。長文の有効コード取得は未合格のままとする。

Gate 3の未完了範囲を保持し、別の実HTML統合経路も検証するため、Gate 4/5セッション `731bd57d74cd4965a7299a38d7c554a4` を準備した。合成の日本語メモを対象とし、実フォームへの入力・読戻し後に「開始する」を1回クリックした。フロントエンドの開始通信はHTTP200で、新ジョブ `d23aeb8a961b4b198eaef6a8ef8a087d` と「手順を検討中」の表示を確認した（`ui-click.json`、`job-owned.json`、`ui-observation-001.json`）。直接のAPI POSTやjob作成では代用していない。この記録時点では実行中で、PAD完走・Gate 4/5合格は未確認である。
Gate 4/5の初回計画はRESPONSE_TIMEOUTでfailedとなり、helperは終端状態・worker終了・HTMLとの状態一致・旧ファイルとタブの保持を確認した（同セッション `result.json`）。PADとAiCallは未実行で、正常な2〜3往復の証拠ではない。ジョブ専用Copilotのhas_sent=trueと今回のattemptファイルを別に確認したが、helperのnew_attempt_ownership_verifiedはfalseのまま保持する。事後の2snapshotは6781文字で一致し、折り畳まれたJSONが2件目のai_call_id途中で切れ、Moreボタンを含んでいた。provider生データや未描画部分は未観測である。実HTMLの終了画面 `failed-ui-4d22e8897e1140fa97fa97c653673403.png` も撮影して目視し、エラー、履歴、実行ID、停止ボタン無効を確認した。

Gate 3の1319文字の折り畳み本文は約10分後の2読取りでも不変だった（`fenced-observation-ff7c646a3c7247fd8ae104c9860b57a2.json`）。同じ応答のMoreを、対象・本文・構造・ボタン所有と永続的な単回claimを固定して1回クリックした。ACKを確認し、前後2読取りとファイル・タブ保持が合格した（`partial-tail-expansion-ad3c5fbc7019404a970cf5acaa759313.json`、SHA `e429ade05cd1933c7a6fa347abffe57be6ebbadcdb52bc5ed00d598c8e0e8626`）。ラベルは「簡易表示」に変わったが、本文は60ノード・1行・1319文字・SHA `fa8c8e49e047561079c6e0b9643f2c59d787285d4c15e2fce2bbd1b934b08379` のままだった。約2分後の独立した2読取りも同じだった（`fenced-observation-680cc59f4ab7474891e5fbabd7d38d78.json`）。この応答については展開による本文増加を観測できず、終端のない応答を拒否する現処理を維持する。provider生データの完全性は未観測であり断定しない。部分JSONの受理・修復・再送・PAD実行は0、元のunknownと未送信の長文を保持した。
短文の成否で長文を未送信にしない別診断として、新規long-onlyセッション `cc2c1c91b16b4905a1fe8da3d2776f24` を実施した。24件・推定7817文字、送信上限1回、PAD0のfixtureで、request `3ec364775b2a46848d67f2ac113ece37` は2026-09-05 23:55:03〜23:58:05 UTCにRESPONSE_TIMEOUTとなった。全体はunknownのまま保存し、rawは保存されていない（`result.json`、SHA `27be913c9ad1e495e62c9f611b644ae03c767667f69204b148b7b0a7246e7a6f`）。実行helper PID32100は終了し、旧9タブ・既存ファイル・private51ファイルの保持を確認した。旧約6万文字の失敗結果と分けて記録し、長文の完全取得は未合格である。

長文の事後完全DOM観測は64ノード・2行で、JSON行がちょうど10,000文字の途中で終わる一方、次行に正しい42文字の終端マーカーが存在した。2読取りの本文ハッシュは一致し、生成終了・入力空・保全も確認した（`fenced-observation-12f62d2c93dc42cca898e819b1e481a8.json`、SHA `f9b77b48a85319559d159b767c3e712704a52185a6d106b672404972c6c8d76f`）。表示側の1行省略が仮説として残るため、コード専用のコピー結果と比較する診断を準備中。provider原文や全文取得の成功とは扱わない。

Gate 5の対応外経路は、実HTMLから合成メモをExcelブックへ保存する目的を入力した新規セッション `5435d6963bb24eabb47c5389416eafe1` で合格した。開始1回/HTTP200からjob `5c9b700086c3474abb2ea588f57c53c7` がBLOCKEDとなり、Excel操作が未対応との説明を表示した。worker終了、UI「続行できません」、job.errorとの全文一致、厳格な応答の独立2読取り一致、今回attemptの帰属、旧ファイルとタブの保持を確認した。Planner1回、PAD/AiCall/成果物ファイル0（`result.json`、SHA `abcaf68e7978fe96c81febb1d2b11f56858dac4fba589d1226956d77f3e03403`）。終了画面 `blocked-ui-55113b1400ee472f8c2718642871e215.png` を撮影・目視確認した。ASK_USERと業務完走の合格を意味しない。

Gate 5の質問待機は、実HTMLから翻訳先の言語を未指定にした新規セッション `5abb825befb04bb6ad757076276f53a6` で合格した。開始1回/HTTP200からjob `ad5f3eb1a4484c15a8e9fcb5d4b1a8c5` がwaiting_userとなり、「何語に翻訳しますか？」を表示した。question ID `4e2f42ed7cca4fdd8fb77cd72e6976e8` と質問全文、worker生存を4秒隔てて照合し、厳格なASK_USER応答の2読取り一致、PAD/AiCall/成果物/回答操作0、既存ファイルとタブの保持を確認した（`gate5/ask-sessions/.../result.json`、SHA `58c55d2ebff7dfd6326d0e6b6ff49ab7a189fa5242b8cc2a17d06d055d2436d2`）。`question-ui-9fe09e595ce3441da4b0fca0f38c7a49.png`（SHA `097fba23b70cbef73da71e22f41d63206d3c5d2d954c3003d3c361746f2b0fb0`）を目視し、回答待ち・質問・開始無効・停止有効を確認した。合格範囲はinitial_question_passedで、回答後の再開と業務完了は含めない。

同じ質問へ実HTMLで「英語」を入力し、「回答して続ける」を1回押した追試 `f607542bab404a2c897512ad93b7751b` は、回答HTTP200・同じquestion IDの受付と消費を経て完了した。Copilotが生成した2465バイトのRobinを製品が専用PADへ反映し、run `15684dff4af44ee082702d142a18a67a` で読取→AiCall翻訳→書出しを実行した。AiCall `0877e708da32419d9d044232549d7566` の結果を同じPADが受け取り、実成果物の観測を返した次の計画でDONEとなった。初回ASK_USERを含めた計画3回、実PAD/AiCallを含む完走、worker終了、厳格なDONEの2読取り一致、初回記録・旧ファイル・タブの保持、製品が更新したPAD ownerとの整合が合格した（`gate5/ask-answer-probes/.../result.json`、SHA `2ac5f12b80514f264bccafa26cbb4ceca544ffa77c62f212bff496de01a84c9a`）。直接のAPI POST、手動job書込み、回答の再試行は行っていない。

成果物 `translation.txt` は40バイト、SHA `8ed8f67d0cd9e3485e71cbdb2f9325114772852537e98cad248241b306edb748`、本文は `Tomorrow's meeting starts at 3:00 PM.`。原文の明日・打合せ・午後3時・開始を保ち、意味の追加や欠落がないとrootが確認した（`semantic-review.json`、SHA `d2eb836c1a3d5a4d8a04c4045023a1b74dd8aca7f12340bf2cdf8ed2c28214de`）。実ファイル、観測本文とハッシュ、完了画面のパスが一致した。`done-ui-6ee4550e971444b690506c2ee6832f70.png`（SHA `8da52ec5610b5c4aa436847b0e3600f5cd35188934043844f73232b82ea0be50`）を目視確認した。初回の全画面採取ではPNGが得られず、読取り専用の採取をログ付きで再実行して成功した。現在のPADはこの完了済み翻訳フローで、owner SHAは `ecb7769b01f65d468d34ce53d99ed0e2758d77d3182bd230741aedb43cc59418`。分類分岐や複数ACTによる次のRobin変更まで合格したとは扱わない。

Gate 2の実行中停止試験 `ce71b6141931453eb13ec9bc9c7abbc4` は、WAIT5秒×6と末尾の新規ファイル書込みを使い、実製品関数による差替え・保存・Run各1回、今回のstartedマーカーとrunningを確認後の停止POST1回/ACK、Stop1回を観測した。controllerはcancelled/CANCELLED、成果物・finishedマーカーなし、エラー0のidle復帰、現在ownerとsubmittedの一致を確認した。ただし末尾の保全チェックが未確認となったため全体はunknown/accepted=falseを保存している（`result.json`、SHA `a6386ac1cc789d1a14f053c286ef490ac89743fea6e4f28514e7adefed539b04`）。旧結果を変更せず、読取り専用で失敗した保全条件を切り分ける。この試験直後は保存済み中断試験フローを残し、後続の上記翻訳ジョブで製品が置き換えた。
停止試験の保全追補 `preservation-diagnostic-a0938f49426b4409aac7669902cf3abb.json` は、既存200ファイルの過不足・ハッシュ差分0、現在ownerと今回submissionの一致、旧ownerと旧Mainの保存を確認した。失敗した条件はEdgeの一覧比較で、準備時12件に対し追補時5件だった。実タブの終了・一時的な一覧からの欠落・操作主体は未確認であり、元のunknownを合格へ書き換えない。追補は読取りのみで、旧resultのSHAは不変。最初の診断helperにはエラー整形のプロパティ参照不具合があり、旧版を保存したV2で整形だけを修正して採取した。

長文コード専用コピー `c0ba12c264504777818bc54423846fb4` は2026-09-06 00:19:55〜00:20:18 UTCに1回クリックしACKを確認したが、本文を取得できずunknown/COPY_PROBE_INCOMPLETEだった（`gate3/code-copy-probe/.../result.json`、SHA `0195a9e055d207205b034e80928f7792bb7e6167ade47761eb660ca723b65da6`）。クリップボードはメモリ内へ退避した全形式・内容との一致を照合して復元し、開始時の5ページと既存ファイルは保持した。プロバイダー送信・PAD・展開・権限変更0。ブラウザーのdocument focusを前提確認していないため、コピー不成立の原因は未特定である。このrequestのコピーclaimは消費済みとして保存し、同じ診断を再試行しない。
コピー後の読取り `current-copilot-views-67584b7f295b45f29bcc3df1961f0e23.json`（SHA `95a472dd534c7f8215fd01a9b74f7ccf722da554d17e506761c037e8ac806956`）で、長文の応答に「コードをクリップボードにコピーできません- ドキュメントにフォーカスを移動して、もう一度お試しください」というエラーを確認した。2読取りともdocument.hasFocus=false/visibilityState=hiddenで、論理行は10,000文字と42文字のまま。これにより初回コピーのフォーカス不足を画面内の証拠で特定した。別のGate 4/5タブはnonceを含む応答を取得できず、前面化1回の追補でもhasFocus=true/visibilityState=hidden、assistant一覧は空だった（`gate45-foreground-fd32a4d198fa4dcda3798813ffa71d4c.json`、SHA `097b437cfeff546fe6cd301869f04d5ae3525ad427b7ca072e0d25f5a87e30b5`）。両診断とも既存ファイル・ページ一覧は保持した。初回コピー結果を保持した上で、長文の対象ウィンドウとフォーカスを確認する別の補足診断を準備する。これは同じ診断の無条件な再試行ではなく、確認できた失敗条件を修正した2回目のコピーであり、プロバイダー送信やPAD実行は繰り返さない。

前面化付きコピー補足 `92ae8aa1f7134d0c9af9fd96ef2d2c82` は、CDP上の対象ウィンドウがmaximized、Page.bringToFrontのACK後にhasFocus=trueである一方、20読取りともvisibilityState=hiddenだったため、コピー前で停止した（result SHA `555f5281bcc7779aced6f2f5c56a6e088b7f8098dde8c9cc1db4266ec12a3f58`）。この補足でのコピーとクリップボード変更は0であり、実コピーの累計は初回の1回のまま。続く `native-edge-focus-2bb891649aac4eb595e8caec03a34f16.json`（SHA `c06510ae2c76fd4939ee2ee14805b50b7dd07ef365d92facd73442e894a50146`）は、Edge PID・開始時刻・HWND・CDP矩形との一致、ウィンドウ可視・非最小化・DWM cloaked=0を確認したが、SetForegroundWindowはfalseでOSの前面取得に至らなかった。本文は77ノード・10,000文字と42文字のまま、hasFocus=true/visibilityState=hidden。コピー・権限変更・仮想デスクトップ変更0、旧記録・ファイル・ページ一覧は保持した。未表示と報告する状態の原因は未確定である。

Chromiumの固定commit `8d12fea02a097cdabadbd7c84b45fc63e6b7b908` の[writeText検査](https://chromium.googlesource.com/chromium/src/+/8d12fea02a097cdabadbd7c84b45fc63e6b7b908/third_party/blink/renderer/modules/clipboard/clipboard_promise.cc#672)は、secure context・document focus・権限を要求し、visibilityStateを独立した条件にしていない。補足診断だけに加えていたvisibility条件を外し、実測focusと既存DOM・所有権・クリップボード保護を残した `Copy-CodeLongDocumentFocusOnce.ps1`（SHA `2db995b88c80086afde357e29c70762d4baa781cdeef4f745fbc86fd7c204091`）をnormal Explorerから実行した。installed Edge 152.0.4191.62との実装同一性は推定していない。

追補 `7ce5e64fcd734f468e5e26eb940e654f` は2026-09-06 01:18:44〜01:19:09 UTCにコードコピー1回を要求し、ACKと直前のhasFocus=trueを確認したが、本文を取得できなかった。実コピーは累計2回、クリップボード復元済み、provider/PAD/権限変更0。結果SHAは `29b3c11255fe7c26c427908e468e4cf046c8720c6e80476e5b18690dd0170b4a`。コピー前後の4回のowned DOMは同じ64ノード・10,000文字と42文字の行で、コピー後はhasFocus=falseとなった。明示的な成功・失敗の表示はなく、フォーカス変化だけから原因を断定しない。末尾の保全エラーが先行コピーエラーを上書きし、実行直後のafter記録も保存されなかったため、元の結果は `unknown/PRESERVATION_FAILED` のまま保持する。

読み取り専用の現在比較 `document-focus-current-comparison-68476708d60849ce80d98f39ee05cc98.json` は、01:24:32 UTC時点で既存247ファイル・消費claim・HEADが一致し、元の7ページを保持した上で別の1ページが増えたことを確認した。これは実行直後の状態を復元した証拠ではない。最初の比較ヘルパーはWindows PowerShell 5.1でUTF-8指定を欠きJSON読取りに失敗したため、旧ファイルを保持してUTF-8明示版で比較した。長文完全取得は未検証であり、本体へのコピー処理追加は行っていない。IssueにはJSONの物理行数指定がないため、次に複数行JSONの表示構造を測定する。長いRobin文字列自体はpretty-printだけで分割されない点も残る。

Gate 0の追補 `d2dd3aa485384c29b884df9be83ff33c` は、実共有を読み取って作った隔離cacheに対し、未作成UNC子パスをSourcePathとして実AppのBootstrapを1回起動し、警告・新規serverの起動と状態確認・所有確認後の正常終了まで合格した（`gate0/outage-followups/d2dd3aa485384c29b884df9be83ff33c/result.json`）。2026-09-05 21:35:44〜21:35:51 UTC、Bootstrap exit 0、試験server PID13688/port56786は終了済み。通常server PID25544/port53708、既存158ファイル、共有3ファイル、cache4ファイルは保持した。実共有そのものの停止やCMD起動を行った試験ではなく、existing_share_outage=false/actual_cmd_invocations=0を記録している。旧outage失敗結果は変更していない。

Gate 0の実共有切断、Gate 1/2の異常系、Gate 3〜6の実機確認も残っている。

分類と2回の生成ACTを確かめる追加フィクスチャは、短い日本語メモをreview/normalに分類し、最初の実行で分類結果と下書きを保存、次の実行で実保存結果を読み直して最終ファイルへ書く自然文依頼とした。初回 `classify-sessions/08c9121e9e7c413faf025321f002b2b2` は、入力後・開始前に無関係な旧タブ1件の欠落を検証スクリプトが拒否した（result SHA `10c70a4319a99168ee4bc3a5489700e1b47a9b88e29893da4bebce200505af9b`）。開始・job作成・provider・PADは0。対象外タブの一覧変化は記録にとどめるクローンを作り、所有UI/Copilotタブ・job・ファイルの照合を必須のまま維持した。

次の `classify-sessions/a42c6852dff2424d9642978de318b4d0` は、2026-09-06 01:30:14〜01:31:48 UTCに実HTMLの開始1回/HTTP200からjob `4d4538fe3d9f45099fa721078d5e4d7d` を作成した。Copilot応答は完全なJSONとして取得されたが、Robinの最初のReadTextパスに単独バックスラッシュがあり、現行の二重バックスラッシュ契約に合わず `ROBIN_ACTION` でPAD前に停止した。AiCallのアクションは提供済みテンプレートと一致した。また、classification.txtへのWriteがIF/ELSEの両方に現れ、後段の書込1回制約にも反していた。UIエラー一致・worker終了・旧ファイル・全タブ・PAD所有記録の保持を確認した。result SHA `77db002ec916e69769827280be41f18eb27301e561ed88c973ffd36cc0b65b33`、Copilotの2読取り記録SHA `f5532d49acd40688befcd08e59fc9e4cbeb747af7b3468fa9801c106c0e79a10`。これは不正生成コードの実行前拒否の証拠であり、分類フローの完走ではない。

複数行JSONの診断 `pretty-diagnostic/sessions/846d0dd3df984619830794adb486937e` は、送信部分の表示指定だけを診断用14行へ変更し、本体を変えずに実行した。2026-09-06 01:35:38〜01:36:16 UTCに送信前の待機で `RESPONSE_TIMEOUT` となった。新規job `50ff7e1f96c344f68e20c0d38011c59c` のtarget記録は `has_sent=false`、request `a7286c4757514fccb3b1ea670ccd9ce5` のattemptファイルは存在せず、送信ACKもない。provider呼出し入口への到達を実送信と数えず、結果のprovider_callsはnullのまま保持する。旧ファイルと所有targetは保持し、PAD/コピー/展開は0。後刻の読み取り専用確認では、同じタブに空の入力欄1件、生成中表示・過去回答・busy表示0、readyState=completeを確認した。待機失敗時点の一時的な読込み状態は後刻観測から断定しない。

同じ未送信のjob/request/targetを照合し、新たな一度限りの継続claimを作った `pretty-diagnostic/continuations/1be3ec8bf6364393a1fff27b5963ec08` は、01:50:30〜01:51:17 UTCに初回送信1回のACKを確認して成功した。14論理行・268 UTF-8 bytesは期待本文と完全一致し、独立した2回の全DOM読取りも一致、既存の厳密JSONパーサーとPlanner契約を通過した。result SHA `ab00bfff2540c661b94b65b5a54a12267d01ac17ae058f680b94ac607f7f0ee1`、本文SHA `7a8220e3485dc1eb53444cf8b58a52579d52890ad0f65ab188ebeb2523e8ed94`。新規タブ・PAD・コピー・展開・権限変更0、旧ファイル・所有targetを保持。これは複数行の表示構造と送信データ保持を測った診断であり、未変更の製品アダプターの複数行対応や長文Gate合格ではない。

Gate 2の `busy-cancel-sessions/b05d8d6d6e564f1ab3a674bff92b9820` は、実PADでAの今回開始マーカーとrunningを確認後、別の通常PowerShell controller Bを1回呼び出した。A用helperの事前mutexは解放し、製品controllerが保持するmutexで `failed/PAD_BUSY: another PAD controller is active.` を返すこと、Bの全UI境界呼出し0・job未作成を確認した。Aは保存・実行・取消・停止各1回、取消ACK、`cancelled/CANCELLED`、出力/終了マーカー0、最後はidle・新ownerと提出コード一致。既存ファイル保持とブラウザー一覧不変も確認した。元result SHA `dd53bac9c6c1f809d5867bf292fbebd4132afe6ca081d0f1c653f3a795731de7` は `unknown/accepted=false` のまま保持する。

B helperの集計は `counts` 内の `keys=0` が `.Keys` を隠し、整数添字0で先頭のcontroller_calls=1をUI合計へ加算していた。読取診断 `posthoc-8e24f21fd4274d9aaeceb4e7b0f2bfbf.json`（SHA `4472c3aff47e1e30785e40a1c44b6b7472ceb5b279380f649fcbcda530efb70f`）で、保存countsをnative PS5.1へ戻し、元式1・GetEnumeratorによる正しい合計0を再現した。元式のOR条件はここで短絡し、後続のowner/startハッシュ比較には達していなかった。現在値はauthorizationと一致したが、当時の未保存値の代用にはしない。PADを再実行せず、製品の実競合拒否・取消の証拠と、helper全体の不明判定を分けて記録する。現在のMainはこのWAITフローで、owner SHA `c20a1332d5783d0b1f91dae47ff44bd47f733c828ec3b9261eb59a8def2b38fb`、content hash `67813b2da377c4bfb792b46beb091d7f05b5a1b09699bf9bc90ea12963f83fe9`。以前の翻訳フローとownerは同sessionに退避済み。

## 再現コマンド

リポジトリのルートで実行する。アプリ配布にテスト用ランタイムを含めない。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-App.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-Copilot.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-Pad.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-Http.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-Launcher.ps1
```

UIテストは開発用PlaywrightとEdgeを使う。Copilotへ接続していない隔離Homeを指定する。`PLAYWRIGHT_MODULE` にPlaywrightの解決先を設定し、そのHomeで `App.ps1 -Mode Serve -NoBrowser -HomePath <絶対パス>` を起動してから `node tests/Test-Ui.cjs <同じHome>` を実行する。

GitHub Actionsは未設定・未実行。PR作成・マージ・Issueの完了更新は行っていない。

PAD操作の追加修正は独立コードレビューで BLOCKER 0 / MUST FIX 0。固定A/Bの実機検証に進めるとの判断であり、Issue全体の完了・マージ可能性を示すものではない。実機ゲート不足は未解決のまま保持する。

2026-09-06 11:30以降のcf00c1b実機検証: 長文session `7826aacf1fed4a0e8e8ad1c39e9b1597` は単一要求後に `RESPONSE_INVALID/unknown` で停止し、PAD0・旧ファイル/所有タブ保持を確認した（result SHA `cf3f5fa368809e97ecba13702f5d880f53aa9e60950a59d42b0d831ff0bf7628`）。同じ応答の読み取り専用2観測では全188ノード・33論理行が一致し、JSON12,560文字・最長行8,424文字・厳密JSON/nonceは完全だった。保存証拠 `.work/gate3/long-pretty-observation-aceb801b39134ea8aa431206e7048521.json` のSHAは `d477616fc8b5217fae5e3a506ef3e67508b9713f75b477a5eba229a4bd2c9ed2`。『簡易表示』でもeditorがmaxHeight=3050px/overflow=autoで、末尾行が可視枠外に残るため、現在の全面内包条件を満たさずrenderedへ戻っていた。今回の失敗を10,000文字での切断とは扱わない。元の製品結果は変更せず、この実測状態に限定した修正候補を準備中。

分類session `0d882e301e7c495a972efa4082fcc9eb` は実HTMLからStart1回、job `351437fe00e343c5be53fcbca810e70a` のAiCall `8d617876c2e94e0895f5c5a018d4e7b2` がsuccess/reviewを返し、実PADの2段階（run `74c9336b08ec44819f579f76be0ba064` と `0d670b045a254c60ad4bf0bbb48e5e19`）は双方successになった。2回目の異なる生成Robinは最初のclassification.txt/review-draft.txtを読み直して分岐する。review-draft.txtとfinal-review.txtは83バイト・同一SHA `271fe047a97061f8eb4f3f2fd9a14d99973059fed1714a4256272da4ce2b4a5d`、UTF-8読取り後の本文は元メモとOrdinal完全一致した。normal側の成果物は存在しない。読み取り専用の補足検証は `two-act-artifacts-posthoc.json`（SHA `5662fb5b566f58f718bb35889a287f87b2a72238e1fef4eb75d1ba72d088a7b9`）。ただし最後のDONE要求 `67ca6fda77a146c3ba1b665bddd45de0` が単回展開を確認できずfailedになり、画面はその失敗と一致した。ヘルパー全体もpartialのまま保持する（result SHA `e5c40a82c5fe9be9e5136e70a97acfc1bb9cb26a8185da882c7dfaa0ad71eee3`）。旧ファイル/所有記録/タブ保持・worker終了を確認済み。DONEの604文字は最終2snapshotで同じfenced_collapsedとして残っており、別の読み取り専用診断で具体的な展開拒否条件を調査中。
同日11:57 JST、コミット `701a2a8` の上記スクロール・展開修正版を共有UNCと通常cacheへ更新した。公開session `2ac05baf0bde44b0bdc035dea2ea4397`（result SHA `6d86826660b2cb1d1a9383347af0b6d09360ddc2eeeb86dec6d95d14eceda254`）、更新session `50c15078a6b04cb3a104fa7065947780`（SHA `5b8d2b735fbecbc0001cdaa61b2ff22a2086eddd4c52ac8827c86e23709728be`）ともPASS。新serverはPID26936 / port59059 / `2026-09-06T02:57:18.6161372Z`。既存274ファイル、PAD owner/content、共有ACLを保全した。記録は `.work/gate0/release-update-701a2a8-summary.json`。統合ソースの独立レビューはSHIP、ローカル検証は `.work/integrated-scroll-more-validation.json`。
同日12:00 JSTの長文再検証session `db888cd9dace4e9996b2382865d5e744` は、応答JSON4,278バイト・32行を取得し、再取得とのbyte/Ordinal完全一致と厳密JSON/Planner検証を通過した。しかしRobinは `BLOCKED: missing capability` という27文字だけで、許可構文検証が `ROBIN_ACTION` を返した。24個の出力パスは正しかったが24本のWriteは生成されず、長文容量のPASSには含めない。送信1回・PAD0、元resultと取得rawを保持した。診断用プロンプト内のACT強制/BLOCKED指示と変数参照例を整合する別helperを準備した。

同日12:02の生成分類session `1a0355df5c9c41de861567b0ceee7fd8` / job `3c675d8e02d242d0b3b14853aeb428ff` はHTML開始1回・HTTP200からACTを生成したが、Run前の `PAD_FOCUS: designer foreground was not acquired.` で停止した。失敗観測を受けた次の応答はASK_USER。元helper結果はpartialのまま保存し、その後元UIの停止ボタン1回でcancelled・worker終了を確認した（`stop-waiting-focus.json`）。このFocus実装は前回2ACT成功時から不変。保存記録はRun前停止を示すが、個別のDelete/Paste/Save回数やOS前面状態は未記録。旧履歴・成果物・所有情報を保持し、同じ失敗ACTの再実行は行っていない。
同日12:09 JST、診断プロンプトの曖昧さを修正した独立長文session `7b604f37af8a4c67b3a7698471d37591` がPASS。製品ソースは `701a2a8 / 871389ed…` のまま。実M365からJSON **12,593 UTF-8バイト**、Robin **7,793文字・25行・24 Write** を取得し、厳密JSON/nonce/Planner/Robin検証と再取得との全文byte/Ordinal一致を確認した。フレーム全体は12,636バイト、source_kindはfenced_plaintext、送信1回、PAD0、旧ファイル・所有タブ保持true。元の失敗/unknownは変更していない。result SHAは `784be3aa80f2042899970188ed9209e6f71e33b62adaff870b9a0a28c02ecb69`、raw/再取得SHAは `b47b099eafca0cf4580ba981f8375c8182444cd97d0296d7f1b5eaa24e5c6f01`。これは長文生成Robinの取得検証であり、24ファイルを実PADで生成した証拠ではない。
同日12:14 JST、正常Explorerから製品 `Set-AgentPadFocus` を1回呼んだ診断も、前面HWND不一致で停止した。対象HWNDは5703820、前後と2秒の読取観測で前面HWNDは0のまま。PADはready/idle/error0、固定6ファイルとownerを保持し、Copy/Delete/Paste/Save/Runは0。結果は `.work/gate45/classify-sessions/1a0355df5c9c41de861567b0ceee7fd8/focus-fixed-files-once/result-1db744b557d8416b800d5243b0ad46ab.json`（SHA `8ab479c3136bee8258fac678580e3b5000c4a39d633ade0dcdec7fcb48158fe6`）。先行の診断helperは不要な全履歴hash前処理で停止しFocus0だったため、元結果を保持して固定ファイルだけの別helperへ絞った。

追加の読取専用OS確認 `.work/gate45/input-desktop-state.json` は、通常Explorer/PAD側のセッションID **1** に対しアクティブコンソールID **2**、前面HWND0、OpenInputDesktop失敗（error5）、同セッションのLogonUIありを記録した。PAD側セッションが現在アクティブでないため、ソースへ待機や再試行を追加せず、元のWindows画面への復帰・ロック解除・PAD前面表示を利用者へ依頼した。これを修正後2ACT→DONEの成功と扱わない。元分類jobは中止済み、長文診断は完了、追加PAD実行は開始していない。次の分類用session `a516583480d842ff9a3ee7ff580bd3c7` はIDを予約しただけでPrepare未実行。
