# Issue #38 / EX03 r8 教材独立性修正

## 判定

`20260916-excel-r8` は、教材と固定EX03試験条件の独立性、および専用PADでの貼付け・保存・再コピーまでPASS。通常M365 Copilot生成とEX03統合Runは未実施のため、EX03受入は未達のまま。

Copilotの拒否原文が挙げたescape破損は、実送信r6 bundleの生バイトと一致しない。実送信bundleでは `=\>`、`\_`、`\[` は各0件、rawの `=>` は184件、`_ValueTypeMatch` は60件、`Data1[0][0]` は12件だった。したがって、拒否説明だけから内部原因を確定しない。

別の機械監査により、実送信r6 bundleとr7教材には、固定EX03の4 workbook path、4 sheet name、2 source rectangle、12 target mapping、guard/read/write/save/reopen/compareを含む完全解が入っていた。これは教材と試験の結合という受入設計上の問題である。Copilot拒否の内部原因だったことまでは証明していない。

## 修正前後

- 修正前: `copilot/versions/20260916-excel-r6/knowledge/PAD-Robin-06-Examples.txt` の `EX03 r6統合構成例` と、`20260916-excel-r7` の00/04/06末尾・指示末尾・support Robinが固定EX03の完全なpath/sheet/range/target対応を保持していた。
- 修正後: `20260916-excel-r8` の00/04/06末尾・指示末尾・support Robinを、別path、別日本語sheet、別range、別target、別outputの同形教材例へ交換した。
- 固定依頼、spec、expected、fixtures、r7以前の版・証跡は無変更。knowledge 01/02/03/05はr7とバイト一致。
- 変更したのは教材例のdata slotだけ。命令名、引数名、mode、DataTable添字、text/numberの役割、依存順、分岐・block構造、1 RunScript、5 numeric write、12 JSON compareを保持した。逆置換でr7 Robinへ戻ることを確認した。
- 固定EX03の完全識別子と固有grader文字列は、r8の指示・bundle・support Robinに存在しない。`100%`は現行r8指示とsupport Robinに存在しない。bundle内に残る`100%`は旧来の独立percent-text probeであり、固定EX03のtarget対応とは結び付けていない。

## 専用PAD確認

- PAD 2.71.115.26224、日本語UI、Power Fx OFF、専用空Main `無題 (6)`。
- 貼付け1回、110 action、45 variable、保存1回、READY、再コピー1回。
- 投入前候補と再コピーは14,275文字でraw SHAを含め完全一致。
- 再コピーRobinのRunScript payloadを観測済みescapeだけ復号すると、support PowerShellと最終LFを除き一致。
- 実行0、Copilot送信0、EX03統合Run 0、GitHub書込み0。

## 固定SHA

- version: `20260916-excel-r8`
- instruction: `57f0cdb656e919f8fd83252a6adcd4d12788dac9bf6833db2f2e942eada23bcb`（6,696 UTF-16単位）
- bundle: `164c99e59204efd863f4fe283e8f84ce2902ee760ab90e45cf7c5336631aaddb`
- manifest: `9025c8869b84d27e4f39512ce157a114a5231041e641ae12ef36c061eae29d3e`
- PAD再コピーRobin: `6d9c23eabfacbcd65b1a18eabf5681805494e41171f94a9b01a28b24452815bb`
- 内包PowerShell: `65b86b0e5be4ec2da30e57a6bd858e395d1103da2d05ab2e7607362772d1dfd9`

## 検査と残件

- Issue #38関連Python回帰: 46/46 PASS（Excel oracle、EX02、EX03、EX04既存出力）。
- 版別package検査: r1、r3、r4、r5、r6、r7、r8はPASS_NON_LIVE_PACKAGE。
- r2は既知の旧FAILを保持。実指示5,911 UTF-16単位に対しmanifestは5,844で、r2配下は今回無変更。
- builderによる一時先再生成: frozen r8と全ファイルbyte一致。既存destination上書き拒否もPASS。
- 固定request/spec/expected SHA、旧版固定hash、r7以前の証跡を維持。
- 原本・対象外cell・formula・effective formatの既存検査、および書式・寸法558差分の旧FAILを維持。
- 既存output guardの実機経路は未確認のまま。
- 次段階は同版指示全文＋bundleの通常M365 Copilotへの1回送信以降。今回は行わない。
