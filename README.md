# efso-dev-team-knowledge

EFSO 開発チームのナレッジベース。  
今のところは、朝会（standup）の議事録を一元管理するのみ。

## 構造

```
standup/
  YYYY/MM/
    YYYY-MM-DD.md                # 各回の議事録
.claude/
  skills/standup/
    SKILL.md                     # 議事録スキル（作成〜フィードバック反映）
    standup-template.md          # 議事録テンプレート
  rules/
    standup-minutes.md           # 議事録作成ルール
    misrecognition-dict.md       # 誤認識辞書・ドメイン用語集
```

## 使い方

### 議事録の作成

Claude Code の `/standup` スキルで作成します。現状は @ryosukee が手元で実行して main に直接マージしています。

1. Google Meet の Gemini 書き起こし/まとめメモをコピーし、`/standup` に渡す
2. Claude がルール・辞書・テンプレートに従って議事録を生成。`standup/YYYY/MM/YYYY-MM-DD.md` に保存される
3. 内容を確認して必要があれば手修正。修正内容は Claude が分析し、ルール・辞書の改善を提案する
4. main に push すると actions が発火して slack SU スレに議事録を通知

### Slack 投稿の仕組み

議事録の Markdown を Slack mrkdwn テキストに変換して `chat.postMessage` で投稿しています。Slack の `rich_text_list` ブロックは使っておらず、見出しの太字化・リンク変換・箇条書きの `•`/`◦` 置換などをテキストレベルで行っています（`post_standup_to_slack.py` の `md_to_slack()`）。

Slack への投稿では「各メンバー報告」セクションを省略し、GitHub リンクで詳細に誘導しています。

### Slack 投稿の手動実行

push トリガーの actions が失敗した場合や、hook の問題で自動投稿できなかった場合は、手動で再投稿できます。

1. GitHub の Actions タブ → 「Post standup to Slack (manual)」を選択
2. 「Run workflow」をクリックし、日付を `YYYY-MM-DD` 形式で入力して実行

対象日の SU スレ（「今日の SU スレです」のリマインダー投稿）が存在する必要があります。

### 議事録の検索

- 特定の人の報告 → `### @handle` で grep
- 決定事項 → `## 決定事項` で grep
- アクションアイテム → `## アクションアイテム` で grep

## TODO

- [ ] JIRA 連携: チケット番号から JIRA へのリンクを自動で紐づける
- [ ] 関連プロジェクト連携: 関連リポジトリの情報（PR・Issue 等）を議事録から参照できるようにする
