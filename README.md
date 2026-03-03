# efso-dev-team-knowledge

EFSO 開発チームのナレッジベース。朝会（standup）の議事録を一元管理する。

## 構造

```
standup/
  templates/
    standup-template.md   # 議事録テンプレート
  YYYY/MM/
    YYYY-MM-DD.md         # 各回の議事録
.claude/
  rules/
    standup-minutes.md    # 議事録作成ルール
```

## 使い方

### 議事録の作成

1. Google Meet の Gemini 自動書き起こしをコピー
2. Claude に渡すと `.claude/rules/standup-minutes.md` のルールに従って議事録を生成
3. `standup/YYYY/MM/YYYY-MM-DD.md` に保存される

### 議事録の検索

- 特定の人の報告 → `### @handle` で grep
- 決定事項 → `## 決定事項` で grep
- アクションアイテム → `- [ ]` で grep

## TODO

- [ ] JIRA 連携: チケット番号から JIRA へのリンクを自動で紐づける
- [ ] Slack 連携: GitHub Actions から議事録作成時に Slack へ自動ポスト
- [ ] 関連プロジェクト連携: 関連リポジトリの情報（PR・Issue 等）を議事録から参照できるようにする
