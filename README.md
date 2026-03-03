# efso-dev-team-knowledge

EFSO 開発チームのナレッジベース。  
今のところは、朝会（standup）の議事録を一元管理するのみ。

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


今のところは一部手動です && 現状は以下の作業を @ryosukee が手元で動かして main に直接マージしています

1. Google Meet の Gemini 自動書き起こしをコピーし、ローカルのこのリポジトリで Claude に渡す
2. Claude がルールとテンプレートに従って議事録を生成。 `standup/YYYY/MM/YYYY-MM-DD.md` に保存される
3. 内容を確認して必要があれば手動で修正
4. main に push すると actions が発火して slack SU スレに議事録を通知

### 議事録の検索

- 特定の人の報告 → `### @handle` で grep
- 決定事項 → `## 決定事項` で grep
- アクションアイテム → `- [ ]` で grep

## TODO

- [ ] JIRA 連携: チケット番号から JIRA へのリンクを自動で紐づける
- [ ] 関連プロジェクト連携: 関連リポジトリの情報（PR・Issue 等）を議事録から参照できるようにする
