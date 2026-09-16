# EX03-r9-G1 live-generation review
## 結論
EX03-r9-G1は**不受入**です。通常Microsoft 365 Copilotへ固定本文と同版bundleを1回だけ送信し、拒否なしで197行のRobinを得ました。しかし、無修正生成物の埋込みPowerShellに2か所の構文欠落があり、安全確認を通過しませんでした。固定停止条件に従い、専用PADへの貼付け・保存・再コピー・Run1・Run2はすべて未実施です。
## 固定版と送信
- version: `20260917-excel-r9`
- instruction SHA-256: `a699dd910a4b0529fc71c9b8045b845bf49b8a407df9da88027a0ca0ab0f51fa`
- bundle SHA-256: `b402a6c78fb39cb68dd4111590122b9f9be3364609358fd58a9ad3880d29b993`
- manifest SHA-256: `1b64005c85aee3215160c9381d956a64531863b5d838d9091009fded5007f540`
- submitted body SHA-256: `f6c6e59d719548ba54d6207fc6d6499a9ae7c699339ac855e3d4ea4a6f26aee4`
- conversation: <https://m365.cloud.microsoft/chat/conversation/b4fb07d7-41ce-4a2d-97c3-17b8145f32a4?es=SSR>
- normal M365 send: 1 / resend: 0
送信直前の可視エディタ内容は固定本文とSHA一致しました。生のエディタコピーに現れたU+200B/U+200Cは`aria-hidden`のLexical制御ノードで、これらを除く可視シリアライズは固定本文と一致しています。
## 生成物と停止理由
生のWindows clipboard UTF-8 SHA-256は`dce9d6f01de53252050b53de46283563f56226b1635a2ccdcbd71d2dfd2636bf`です。Base64保全物を復号すればCRLF・最終改行なしを含めて再現できます。閲覧用`generated.robin`はCRLFをLFへ正規化し、末尾LFを1つ追加したものです。
- Robin 50行目: `[string]::Equals([IO.Path]::GetFulling]$candidate.FullName), $targetPath, :OrdinalIgnoreCase)`
  - 期待構造: `[string]::Equals([IO.Path]::GetFullPath([string]$candidate.FullName), $targetPath, [StringComparison]::OrdinalIgnoreCase)`
- Robin 90行目: `:IsNullOrEmpty($afterPrefixCharacter)`
  - 期待構造: `[string]::IsNullOrEmpty($afterPrefixCharacter)`
埋込みPowerShellを実行せずAST解析した結果、上記2か所を起点とする22件の構文エラーが検出されました。独立教材側の対応スクリプトは同じ解析で0件です。角括弧直前のバックスラッシュは0件ですが、それだけでは構造忠実性を満たしません。
## 実行・保全
- PAD貼付け: 0
- 再コピー: NOT_RUN
- Run1: NOT_RUN
- Run2: NOT_RUN
- 出力`照合結果.xlsx`: 未作成
- `work.xlsx`とテンプレート: SHA一致
- 保護対象233ファイル: 不一致0
- 固定依頼・期待値: 変更なし
- 旧558差分FAIL: 保持
- 既存出力ガードの実機確認: 未確認のまま
- GitHub書込み: 0

## 検査

- Issue #38回帰: 55/55 PASS（EX02 18、EX03 20、EX04 4、Excel oracle 13）
- package回帰: `PASS_NON_LIVE_PACKAGE`（旧package範囲のみ。r9実受入への読み替えなし）
- `git diff --check`: PASS
- r9事前チェックポイント検証器: 送信後証跡を検出して期待どおりfail-closed
