"""ニュースリサーチモジュールのテスト"""

from __future__ import annotations

import feedparser as fp

from matome.research import news_rss
from matome.research.news_rss import (
    _search_google_news_rss,
    _search_nhk_rss,
    search_news,
)

RSS_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Google News</title>
    <item>
      <title>AIが社会を変える — 最新動向</title>
      <link>https://example.com/article1</link>
      <pubDate>Wed, 16 Apr 2026 00:00:00 GMT</pubDate>
      <source url="https://example.com">テスト新聞</source>
    </item>
    <item>
      <title>AI技術の進化と課題</title>
      <link>https://example.com/article2</link>
      <pubDate>Wed, 16 Apr 2026 01:00:00 GMT</pubDate>
      <source url="https://example.com">テスト通信</source>
    </item>
  </channel>
</rss>"""

_PARSED = fp.parse(RSS_FIXTURE)


def _mock_parse(url):
    """feedparser.parse のモック — 常にフィクスチャを返す"""
    return _PARSED


class TestSearchNews:
    def test_google_news_parsing(self):
        """Google News RSS のパースが正しく動作する"""
        original = news_rss.feedparser.parse
        news_rss.feedparser.parse = _mock_parse
        try:
            results = _search_google_news_rss("AI", max_results=5)
            assert len(results) == 2
            assert results[0].title == "AIが社会を変える — 最新動向"
            assert results[0].url == "https://example.com/article1"
        finally:
            news_rss.feedparser.parse = original

    def test_nhk_rss_keyword_filter(self):
        """NHK RSS でキーワードフィルタが動作する"""
        original = news_rss.feedparser.parse
        news_rss.feedparser.parse = _mock_parse
        try:
            results = _search_nhk_rss("AI", max_results=5)
            assert len(results) >= 1
            assert all("AI" in r.title for r in results)

            results_no_match = _search_nhk_rss("量子コンピュータ", max_results=5)
            assert len(results_no_match) == 0
        finally:
            news_rss.feedparser.parse = original

    def test_dedup_urls(self):
        """同一 URL の記事は重複排除される"""
        original = news_rss.feedparser.parse
        news_rss.feedparser.parse = _mock_parse
        try:
            results = search_news("AI", max_results=10)
            urls = [r.url for r in results]
            assert len(urls) == len(set(urls))
        finally:
            news_rss.feedparser.parse = original
