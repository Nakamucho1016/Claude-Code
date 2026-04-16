"""RSS フィードからニュース記事を検索・収集"""

from __future__ import annotations

import logging
from urllib.parse import quote_plus

import feedparser

from matome.models import NewsSource

logger = logging.getLogger(__name__)

# RSS フィードテンプレート
RSS_FEEDS = {
    "Google News": "https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP:ja",
    "Yahoo!ニュース": "https://news.yahoo.co.jp/rss/topics/top-picks.xml",
}

# NHK カテゴリ別 RSS
NHK_FEEDS = [
    ("NHK 主要", "https://www.nhk.or.jp/rss/news/cat0.xml"),
    ("NHK 社会", "https://www.nhk.or.jp/rss/news/cat1.xml"),
    ("NHK 科学", "https://www.nhk.or.jp/rss/news/cat3.xml"),
    ("NHK 政治", "https://www.nhk.or.jp/rss/news/cat4.xml"),
    ("NHK 経済", "https://www.nhk.or.jp/rss/news/cat5.xml"),
    ("NHK 国際", "https://www.nhk.or.jp/rss/news/cat6.xml"),
    ("NHK スポーツ", "https://www.nhk.or.jp/rss/news/cat7.xml"),
]


def _search_google_news_rss(keyword: str, max_results: int = 5) -> list[NewsSource]:
    """Google News RSS でキーワード検索"""
    url = RSS_FEEDS["Google News"].format(query=quote_plus(keyword))
    try:
        feed = feedparser.parse(url)
        results: list[NewsSource] = []
        for entry in feed.entries[:max_results]:
            # Google News RSS は source タグに媒体名を含む
            source_name = "Google News"
            if hasattr(entry, "source") and hasattr(entry.source, "title"):
                source_name = entry.source.title

            results.append(
                NewsSource(
                    name=source_name,
                    title=entry.get("title", ""),
                    url=entry.get("link", ""),
                    published=entry.get("published", ""),
                )
            )
        return results
    except Exception:
        logger.exception("Google News RSS の取得に失敗: %s", keyword)
        return []


def _search_nhk_rss(keyword: str, max_results: int = 3) -> list[NewsSource]:
    """NHK RSS から該当キーワードを含む記事を検索"""
    keyword_lower = keyword.lower()
    results: list[NewsSource] = []

    for feed_name, feed_url in NHK_FEEDS:
        if len(results) >= max_results:
            break
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                if keyword_lower in title.lower() or keyword_lower in summary.lower():
                    results.append(
                        NewsSource(
                            name=feed_name,
                            title=title,
                            url=entry.get("link", ""),
                            published=entry.get("published", ""),
                        )
                    )
                    if len(results) >= max_results:
                        break
        except Exception:
            logger.warning("NHK RSS の取得に失敗: %s", feed_name)
            continue

    return results


def _search_yahoo_rss(keyword: str, max_results: int = 3) -> list[NewsSource]:
    """Yahoo!ニュース RSS から該当キーワードを含む記事を検索"""
    keyword_lower = keyword.lower()
    results: list[NewsSource] = []

    try:
        feed = feedparser.parse(RSS_FEEDS["Yahoo!ニュース"])
        for entry in feed.entries:
            title = entry.get("title", "")
            if keyword_lower in title.lower():
                results.append(
                    NewsSource(
                        name="Yahoo!ニュース",
                        title=title,
                        url=entry.get("link", ""),
                        published=entry.get("published", ""),
                    )
                )
                if len(results) >= max_results:
                    break
    except Exception:
        logger.exception("Yahoo! RSS の取得に失敗")

    return results


def search_news(keyword: str, max_results: int = 5) -> list[NewsSource]:
    """複数の RSS ソースからニュース記事を検索して統合"""
    all_sources: list[NewsSource] = []

    # Google News が最も網羅的なので優先
    all_sources.extend(_search_google_news_rss(keyword, max_results=max_results))

    # NHK, Yahoo! で補完
    all_sources.extend(_search_nhk_rss(keyword, max_results=3))
    all_sources.extend(_search_yahoo_rss(keyword, max_results=3))

    # URL で重複排除
    seen_urls: set[str] = set()
    unique: list[NewsSource] = []
    for src in all_sources:
        if src.url not in seen_urls:
            seen_urls.add(src.url)
            unique.append(src)

    logger.info("ニュース検索 '%s': %d 件取得", keyword, len(unique))
    return unique[:max_results]
