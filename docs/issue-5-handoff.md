# Issue #5 引き継ぎ（2026-09-06）

状態は **実装済みPoC・実機ゲート未完了**。Issue #5を閉じず、残りの検証と必要な修正を続ける。今回のマージはユーザーが指定した途中成果の保存であり、全要件の受入完了ではない。

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
