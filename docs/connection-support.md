# 接続方式・対応条件の記録

公式情報の確認日: 2026-09-07。資料に示された条件と、実装/実機で確認した範囲を区別します。対象テナントの利用権・管理者承認・社内ポリシーは未確認です。

## 方式の判断

|方式|確認した条件|今回の扱い|
|---|---|---|
|EdgeのCDPとPADデザイナー制御|Edgeの`RemoteDebuggingAllowed`が無効ならリモートデバッグを利用できない。[公式ポリシー](https://learn.microsoft.com/en-us/deployedge/microsoft-edge-policies/remotedebuggingallowed)|現在の経路を維持。管理設定を変更して通過させない。対象環境での許可と実用性を確認する|
|Microsoft 365 Copilot Chat API|プレビュー。`/beta`は本番利用をサポートしない。職場/学校の委任権限のみで、下記7権限が必要。[API仕様](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/ai-services/chat/copilotconversation-chat)|今回の既定経路にしない。OAuth/Entra登録・権限同意・社内審査を経て将来評価する|
|保存済みPADフローのURL起動|PADの導入・サインインに加え、Premiumプランまたは従量課金環境へのアクセスが必要。外部起動の確認は既定で有効。[公式手順](https://learn.microsoft.com/en-us/power-automate/desktop-flows/run-desktop-flows-url-shortcuts)|追加のフロー配布/管理対象と費用が発生し得るため、初版の必須にしない。起動確認を勝手に解除しない|

Chat APIの必須委任権限は `Sites.Read.All`、`Mail.Read`、`People.Read.All`、`OnlineMeetingTranscript.Read.All`、`Chat.Read`、`ChannelMessage.Read.All`、`ExternalItem.Read.All`。本文だけの分類に対しても必要とされる権限なので、組織の同意方針に適合するか別途判断します。[権限表](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/ai-services/chat/copilotconversation-chat)

Chat APIはCopilot追加ライセンス保有者には追加API費用なしと説明されていますが、非保有者の対応はありません。長時間タスクは非対応で、タイムアウトが起き得るという制約もあります。API移行を容量・費用問題の解決済み扱いにはしません。[公式概要](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/ai-services/chat/overview)

PAD URL方式は保存済みフローを識別して起動する機能です。任意Robinを直接実行する公開APIだと解釈せず、外部起動確認の解除や利用者Cookieの転用で現在の制約を回避しません。

## このアプリの境界

|対象|実装・検証の状態|
|---|---|
|Windows PowerShell|5.1で実行。PS7を対応環境とはしていない。配布物はCMD/PS1/HTMLのみ|
|CSV|PADを使用しない固定I/Oと型付き計画。100行/1MiB、5行/24,000文字の分割上限は実装上の限界であり、実M365の実用ベンチ値ではない|
|Copilot|専用Edgeプロファイルとジョブごとの対象タブ、要求ID/終端/完全一致を確認。送信予約後の結果不明を新しいIDで自動再送しない|
|PAD|観測済み日本語UIA構造、専用Main、Power Fx無効を前提。新しい構造を推測クリックしない。現在の実機では停止・編集可能状態と読取りを確認したが、所有記録一致が取れず復元は未実施|
|非ライブ試験|実M365/PAD境界を拒否または明示mockへ置換。ネイティブ復元・意味精度・対象社内環境の証明ではない|

`Get-AgentConnectionContract`に対応版、搬送名、要求上限、安定読取り回数、準備期限を集約しました。起動・診断・送信前にHKLM/HKCUと32/64bitビューのEdgeポリシーを読みます。無効な場合は日本語で停止理由と配布担当者への案内を表示し、レジストリは変更しません。読み取れない設定も許可扱いにしません。

要求ごとの`.attempt.json`は準備、送信予約、クリック応答、生成中、応答完了、失敗/不明を記録します。時刻差・固定エラー分類・不透明IDだけを持ち、プロンプトや応答本文は保存しません。クリック応答はサービスによる業務成功ではなく、応答完了も業務結果の承認ではありません。既存の送信予約ファイルは維持し、記録があっても再送を許可しません。

CSVでは計画・分類の要求ごとに会話と所有記録を分離します。既存回答照合には保存済みの会話IDを使い、対象タブを失った場合に別タブの回答を採用しません。接続失敗の記録には例外型、HRESULT、失敗直前段階も加え、生の例外メッセージは含めません。

専用の検証Homeから実M365へ送信し、50件完了と復旧を挟んだ100件完了を確認しました。[会話分離の測定記録](live-conversation-isolation-2026-09-07.md)に介入・失敗と候補ハッシュを記載しています。標準Homeや別候補の診断と混同しません。次の必須確認は残っています: 失敗種別の追加分離、匿名fixture・対応版の索引、同じ最終候補の1/50/100件連続測定と長文、表示倍率・前面変更・スリープ・認証切れ、社内PC/別利用者の対応表。少数回の成功を全件数・全環境の保証にしません。
