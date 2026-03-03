#!/usr/bin/env python3
"""standup 議事録を対応する Slack スレッドに投稿する。

使い方:
    python3 scripts/post_standup_to_slack.py standup/2026/03/2026-03-02.md

必要な環境変数:
    SLACK_BOT_TOKEN   - Bot User OAuth Token (xoxb-...)
    SLACK_CHANNEL_ID  - 投稿先チャンネル ID (C0XXXXXXX)
    GITHUB_REPOSITORY - owner/repo (Actions が自動設定)
    GITHUB_SHA        - コミット SHA (Actions が自動設定)

処理フロー:
    1. ファイルパスから日付を抽出
    2. conversations.history で対象日 (JST) のメッセージを取得
    3. 「今日の SU スレです」を含むリマインダーメッセージの ts を特定
    4. Markdown → Slack mrkdwn に変換し、スレッドに返信として投稿
"""

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))


def slack_api(method: str, token: str, params: dict) -> dict:
    """Slack Web API を呼び出してレスポンスを返す。ok=false の場合は例外。"""
    url = f"https://slack.com/api/{method}"
    data = json.dumps(params).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode())
    if not body.get("ok"):
        raise RuntimeError(f"Slack API {method} failed: {body.get('error', body)}")
    return body


def extract_date(filepath: str) -> str:
    """ファイルパスから YYYY-MM-DD を抽出する。"""
    m = re.search(r"(\d{4}-\d{2}-\d{2})\.md$", filepath)
    if not m:
        raise ValueError(f"Cannot extract date from path: {filepath}")
    return m.group(1)


def find_thread_ts(token: str, channel: str, date_str: str) -> str:
    """対象日 (JST) の SU リマインダースレッドの ts を返す。

    Bot が毎朝投稿する「今日の SU スレです」を含むメッセージを探す。
    見つからない場合 (祝日等) は RuntimeError。
    """
    target_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=JST)
    # JST の 00:00:00 〜 23:59:59 を UNIX timestamp に変換
    oldest = target_date.replace(hour=0, minute=0, second=0).timestamp()
    latest = target_date.replace(hour=23, minute=59, second=59).timestamp()

    body = slack_api(
        "conversations.history",
        token,
        {
            "channel": channel,
            "oldest": str(oldest),
            "latest": str(latest),
            "limit": 100,
        },
    )

    for msg in body.get("messages", []):
        text = msg.get("text", "")
        # 全角スペースの有無どちらにも対応
        if "今日の SU スレです" in text or "今日のSUスレです" in text:
            return msg["ts"]

    raise RuntimeError(
        f"SU thread not found for {date_str}. "
        "The reminder message may not have been posted (holiday?)."
    )


def md_to_slack(text: str) -> str:
    """Markdown の見出しを Slack mrkdwn の太字に変換する。

    リストやチェックボックスはそのまま保持される。
    """
    lines = text.split("\n")
    result = []
    for line in lines:
        line = re.sub(r"^### (.+)$", r"*\1*", line)
        line = re.sub(r"^## (.+)$", r"\n*\1*", line)
        line = re.sub(r"^# (.+)$", r"*\1*", line)
        result.append(line)
    return "\n".join(result).strip()


def load_user_map(config_path: str) -> dict[str, str]:
    """users.yml を読み込み {handle: slack_userid} の辞書を返す。

    PyYAML に依存せず正規表現で簡易パースする。
    ファイルが存在しない場合は空辞書を返す。
    """
    user_map: dict[str, str] = {}
    if not os.path.isfile(config_path):
        return user_map
    with open(config_path, encoding="utf-8") as f:
        content = f.read()
    for m in re.finditer(
        r"^  (\w+):\s*\n\s+slack_userid:\s*\"([^\"]+)\"", content, re.MULTILINE
    ):
        user_map[m.group(1)] = m.group(2)
    return user_map


def replace_mentions(text: str, user_map: dict[str, str]) -> str:
    """@handle を <@SLACK_USER_ID> に置換する。

    マッピングにない handle はそのまま残す。
    """
    def _replace(m: re.Match) -> str:
        handle = m.group(1)
        slack_id = user_map.get(handle)
        if slack_id:
            return f"<@{slack_id}>"
        return m.group(0)

    return re.sub(r"@(\w+)", _replace, text)


def build_github_url(filepath: str) -> str:
    """GitHub 上のファイルへのパーマリンクを生成する。"""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    sha = os.environ.get("GITHUB_SHA", "")
    if repo and sha:
        return f"https://github.com/{repo}/blob/{sha}/{filepath}"
    return ""


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: post_standup_to_slack.py <standup-file>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    token = os.environ["SLACK_BOT_TOKEN"]
    channel = os.environ["SLACK_CHANNEL_ID"]

    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    date_str = extract_date(filepath)
    thread_ts = find_thread_ts(token, channel, date_str)

    # Markdown → Slack mrkdwn に変換し、@handle をメンションに置換
    slack_text = md_to_slack(content)
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "users.yml")
    user_map = load_user_map(config_path)
    slack_text = replace_mentions(slack_text, user_map)
    github_url = build_github_url(filepath)
    if github_url:
        slack_text += f"\n\n<{github_url}|:link: GitHub で見る>"

    slack_api(
        "chat.postMessage",
        token,
        {
            "channel": channel,
            "thread_ts": thread_ts,
            "text": slack_text,
            "unfurl_links": False,
        },
    )
    print(f"Posted {filepath} to Slack thread (date={date_str}, ts={thread_ts})")


if __name__ == "__main__":
    main()
