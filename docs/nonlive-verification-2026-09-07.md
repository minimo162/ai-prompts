# 汎用化後の全非ライブ試験

`fd669d0`の製品3ファイルを対象に、Windows PowerShell 5.1で次を実行しました。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File tests\Run-NonLiveTests.ps1 -Suite All -IncludeUi
```

全36スイートを確認し、初回に失敗した2試験を修正して個別に再実行した後、全項目がPASSになりました。これは「初回一括実行で全PASS」という記録ではありません。製品コードは変更しておらず、試験中・再確認後も3ファイルのハッシュは一致しています。

修正した試験基盤:

- 全体入口とクリップボード試験のUTF-8 BOMを復元。PS5が日本語をANSIとして誤読しないよう、非ASCIIを含むBOMなし試験を開始前に拒否します。この拒否も独立した合成fixtureで確認しました。
- Copilot試験のAST読み込みに、Robinの新しい変数参照・整数検証関数を追加。再実行で304項目PASS。
- PAD復旧画面試験は、保存と競合する`job.json`の直接読取りをやめ、実HTTPの状態APIで復旧を確認。再実行で9項目PASS。

証拠は`.work/nonlive-453b7b1fa1014d44a2bbce9e723f204c/verification.json`（初回FAIL）と`verification-rechecked.json`（個別再確認を統合）です。各再確認ログも同じディレクトリーに保存しました。BOM検査の拒否証拠は`.work/encoding-guard-723cd3621812416a9ca8000b28283f4c/verification.json`です。

App SHA256は`1f376113a498eef977f611081cd94403ae16d78a926cef1ec38cc69049333ccf`。実M365/PAD、別PC、出荷承認はこの非ライブ結果に含めません。実機の個別結果は[実機記録](general-agent-live-2026-09-07.md)を参照してください。
