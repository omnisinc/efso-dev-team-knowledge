#!/usr/bin/env python3
"""Post standup minutes to the corresponding Slack thread.

Usage:
    python3 scripts/post_standup_to_slack.py standup/2026/03/2026-03-02.md

Required environment variables:
    SLACK_BOT_TOKEN   - Bot User OAuth Token (xoxb-...)
    SLACK_CHANNEL_ID  - Target channel ID (C0XXXXXXX)
    GITHUB_REPOSITORY - owner/repo (set by Actions)
    GITHUB_SHA        - commit SHA (set by Actions)
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
    """Call a Slack Web API method and return the parsed response."""
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
    """Extract YYYY-MM-DD from a standup file path."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})\.md$", filepath)
    if not m:
        raise ValueError(f"Cannot extract date from path: {filepath}")
    return m.group(1)


def find_thread_ts(token: str, channel: str, date_str: str) -> str:
    """Find the SU reminder thread for the given date (JST).

    Searches the channel history for a message containing '今日の SU スレです'
    posted on the target date in JST.
    """
    target_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=JST)
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
        if "今日の SU スレです" in text or "今日のSUスレです" in text:
            return msg["ts"]

    raise RuntimeError(
        f"SU thread not found for {date_str}. "
        "The reminder message may not have been posted (holiday?)."
    )


def md_to_slack(text: str) -> str:
    """Convert Markdown to Slack mrkdwn format."""
    lines = text.split("\n")
    result = []
    for line in lines:
        # ### Sub heading
        line = re.sub(r"^### (.+)$", r"*\1*", line)
        # ## Section heading
        line = re.sub(r"^## (.+)$", r"\n*\1*", line)
        # # Title heading
        line = re.sub(r"^# (.+)$", r"*\1*", line)
        result.append(line)
    return "\n".join(result).strip()


def build_github_url(filepath: str) -> str:
    """Build a GitHub permalink for the file."""
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

    # Read the standup file
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    date_str = extract_date(filepath)
    thread_ts = find_thread_ts(token, channel, date_str)

    # Convert and post
    slack_text = md_to_slack(content)
    github_url = build_github_url(filepath)
    if github_url:
        slack_text += f"\n\n<{github_url}|:github: GitHub で見る>"

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
