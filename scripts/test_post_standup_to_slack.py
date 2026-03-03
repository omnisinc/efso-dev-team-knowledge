#!/usr/bin/env python3
"""Tests for post_standup_to_slack.py"""

import json
import os
import unittest
from unittest.mock import patch, MagicMock

from post_standup_to_slack import extract_date, md_to_slack, find_thread_ts, build_github_url


class TestExtractDate(unittest.TestCase):
    def test_normal_path(self):
        self.assertEqual(extract_date("standup/2026/03/2026-03-02.md"), "2026-03-02")

    def test_deep_path(self):
        self.assertEqual(extract_date("foo/bar/standup/2025/12/2025-12-31.md"), "2025-12-31")

    def test_invalid_path(self):
        with self.assertRaises(ValueError):
            extract_date("standup/readme.md")


class TestMdToSlack(unittest.TestCase):
    def test_h1(self):
        self.assertIn("*Standup 2026-03-02*", md_to_slack("# Standup 2026-03-02"))

    def test_h2(self):
        result = md_to_slack("## 全体共有事項")
        self.assertIn("*全体共有事項*", result)

    def test_h3(self):
        self.assertIn("*miyazaki*", md_to_slack("### miyazaki"))

    def test_list_preserved(self):
        md = "- item1\n    - nested"
        result = md_to_slack(md)
        self.assertIn("- item1", result)
        self.assertIn("    - nested", result)

    def test_checkbox_preserved(self):
        md = "- [ ] @shima: do something"
        result = md_to_slack(md)
        self.assertIn("- [ ] @shima: do something", result)

    def test_full_document(self):
        md = """# Standup 2026-03-02

## 参加者
- kent-san, miyazaki-san

## 全体共有事項
- some topic

### miyazaki
- これまでやったこと:
    - task1"""
        result = md_to_slack(md)
        self.assertIn("*Standup 2026-03-02*", result)
        self.assertIn("*参加者*", result)
        self.assertIn("*miyazaki*", result)
        self.assertIn("- some topic", result)
        self.assertIn("    - task1", result)


class TestBuildGithubUrl(unittest.TestCase):
    @patch.dict(os.environ, {"GITHUB_REPOSITORY": "omnisinc/efso-dev-team-knowledge", "GITHUB_SHA": "abc123"})
    def test_with_env(self):
        url = build_github_url("standup/2026/03/2026-03-02.md")
        self.assertEqual(
            url,
            "https://github.com/omnisinc/efso-dev-team-knowledge/blob/abc123/standup/2026/03/2026-03-02.md",
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_without_env(self):
        url = build_github_url("standup/2026/03/2026-03-02.md")
        self.assertEqual(url, "")


class TestFindThreadTs(unittest.TestCase):
    @patch("post_standup_to_slack.slack_api")
    def test_finds_thread(self, mock_api):
        mock_api.return_value = {
            "ok": True,
            "messages": [
                {"text": "random message", "ts": "111"},
                {"text": "Reminder: @efso-dev 今日の SU スレです。", "ts": "222"},
            ],
        }
        ts = find_thread_ts("token", "C123", "2026-03-02")
        self.assertEqual(ts, "222")

    @patch("post_standup_to_slack.slack_api")
    def test_finds_thread_no_space(self, mock_api):
        mock_api.return_value = {
            "ok": True,
            "messages": [
                {"text": "今日のSUスレです。議題と議事録をスレに記載してください。", "ts": "333"},
            ],
        }
        ts = find_thread_ts("token", "C123", "2026-03-02")
        self.assertEqual(ts, "333")

    @patch("post_standup_to_slack.slack_api")
    def test_not_found(self, mock_api):
        mock_api.return_value = {
            "ok": True,
            "messages": [{"text": "unrelated", "ts": "111"}],
        }
        with self.assertRaises(RuntimeError):
            find_thread_ts("token", "C123", "2026-03-02")

    @patch("post_standup_to_slack.slack_api")
    def test_passes_correct_time_range(self, mock_api):
        mock_api.return_value = {"ok": True, "messages": []}
        try:
            find_thread_ts("token", "C123", "2026-03-02")
        except RuntimeError:
            pass
        call_args = mock_api.call_args
        params = call_args[0][2]
        # JST 2026-03-02 00:00:00 = UTC 2026-03-01 15:00:00
        oldest = float(params["oldest"])
        latest = float(params["latest"])
        self.assertAlmostEqual(latest - oldest, 86399, delta=1)


if __name__ == "__main__":
    unittest.main()
