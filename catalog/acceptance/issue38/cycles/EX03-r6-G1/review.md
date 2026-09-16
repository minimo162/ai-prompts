# EX03 r6 G1 live acceptance review

## 結論

`20260916-excel-r6` は固定・非ライブ検査までは通過したが、通常 Microsoft 365 Copilot Chat への唯一の実送信が、Robinコードを出さない明示的な拒否で終了した。無修正生成物が存在しないため、指定された停止条件に従ってPADへの貼付け、保存・再コピー、Run1、Run2、成果物照合はすべて未実行とした。EX03 r6は未受入である。

## 固定版と送信

- checkpoint: `726c522c77c5c24268d12e317c4bf6be26bb406c`
- version: `20260916-excel-r6`
- instruction SHA-256: `1211ee45f80427a474d15d92dbfda3b7c90d2a78b9b7520aadb76f5f22c82fe4`
- bundle SHA-256: `9c566e7f85a431f1869302c6a40985e2f81237f17ac4fbbdc9a73e62a646b580`
- manifest SHA-256: `207dfa10f34f0eb7c09a3a39ecfb25c24f870fb5e639b87a0fbce0683cbc9f89`
- embedded support script SHA-256: `d0a5df36516fcf4e27f6d789300ee5a03789aba8176571b1ab86fe84f15fba1a`
- submitted body SHA-256: `a9051689e227e74a904c20fb860f89935b5c393164629869bebbcc923e93903e`
- fixed request SHA-256: `b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370`
- fixed expected SHA-256: `49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d`

送信直前に通常M365 Copilot Chat、Think Deeper、本文7242 UTF-16 code units、添付1件 `PAD-Robin-Knowledge-Bundle.txt`、本文・添付SHA、単一の有効な送信ボタンを再確認した。ユーザーのアクション時確認後に1回だけ送信し、再送・再生成は行っていない。

## Copilot生成結果

会話 `2181a545-7f34-4909-8fe9-aaa90bad056d` は端末応答まで完了したが、応答は「今回は、契約に従ってコードブロックを出しません」と明示した。Copilotは、bundle内の候補をPADから再コピーした完成原文ではなく、説明用エスケープを含む未実行候補と判断し、逆エスケープや再構成は逐語一致条件に反するとした。

DOM確認値はコードブロック0、コードコピー操作0、インラインコード20である。サイトの応答コピーは1回だけ呼び出したがブラウザークリップボードは送信本文のままだったため再試行せず、完成済み応答のmessage body DOMを保全した。`response-rendered.txt` はDOM文字列2070文字に通常の最終LFを1つ加えた2071文字、4903 UTF-8 bytes、SHA-256 `7c6f30590b3ee7905038f142c1974d7639c4579c44a6f445ae0a9ea22f58b342` である。

生成Robinは存在しない。手修正、逆エスケープ、手組み再構成は行っていない。

## PADと照合

- PAD import / save / re-copy: `NOT_RUN`
- Run1: `NOT_RUN_STOP_RULE_TRIGGERED`、PAD呼出し0回
- Run2: `NOT_RUN_STOP_RULE_TRIGGERED`、PAD呼出し0回
- 全対象セル、対象外セル、数式、実効書式、F6の値・型・prefix・数式、2Run一致: `NOT_RUN`
- `照合結果.xlsx`: 未作成

Run1が終了して成果物が保全されるまでRun2へ進まない条件を維持した。今回はRun1の前提である安全確認済み無修正Robinが得られなかったため、Run2へ進んでいない。

## 保全と残件

送信前に固定した150ファイルを送信後に再SHA照合し、150/150一致、欠落0、差分0だった。`work.xlsx` はテンプレートと同じ SHA-256 `881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21` のままで、入力2冊、原本、固定依頼、spec、expected、r5、旧証跡は変更していない。GitHubへの書込みもない。

現r6サイクルは拒否により終了しており、再送や応答の再構成で再開しない。別途後継候補が承認される場合の最小残件は、説明用エスケープではないPAD再コピー済みの完全Robin原文を教材へ供給し、固定依頼・期待値を変えずに新しい版として凍結することである。既存出力ガードは静的確認のみで、実機未確認の残件を維持する。未確認型や別PAD版・別PCへ一般化しない。
