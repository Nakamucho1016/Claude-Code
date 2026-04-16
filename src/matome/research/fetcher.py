"""記事本文の取得 — robots.txt を遵守しつつ本文を抽出"""

from __future__ import annotations

import logging
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
import trafilatura

from matome.config import get_settings

logger = logging.getLogger(__name__)

# robots.txt のキャッシュ（ドメイン単位）
_robots_cache: dict[str, RobotFileParser | None] = {}

MAX_BODY_CHARS = 3000


def _get_robot_parser(url: str) -> RobotFileParser | None:
    """指定 URL のドメインの robots.txt をパースしてキャッシュ"""
    parsed = urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}"

    if domain in _robots_cache:
        return _robots_cache[domain]

    try:
        robots_url = f"{domain}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        _robots_cache[domain] = rp
        return rp
    except Exception:
        logger.warning("robots.txt の取得に失敗: %s", domain)
        _robots_cache[domain] = None
        return None


def _can_fetch(url: str) -> bool:
    """robots.txt でアクセス許可を確認"""
    settings = get_settings()
    rp = _get_robot_parser(url)
    if rp is None:
        # robots.txt 取得失敗 → 安全側に倒してスキップ
        return False
    return rp.can_fetch(settings.http_user_agent, url)


def fetch_article_text(url: str) -> str:
    """URL から記事本文テキストを抽出。失敗時は空文字"""
    if not _can_fetch(url):
        logger.info("robots.txt でブロック: %s", url)
        return ""

    settings = get_settings()
    time.sleep(settings.http_delay)

    try:
        with httpx.Client(
            timeout=settings.http_timeout,
            headers={"User-Agent": settings.http_user_agent},
            follow_redirects=True,
        ) as client:
            resp = client.get(url)
            resp.raise_for_status()

        text = trafilatura.extract(resp.text) or ""
        if len(text) > MAX_BODY_CHARS:
            text = text[:MAX_BODY_CHARS] + "…"

        return text

    except Exception:
        logger.warning("記事本文の取得に失敗: %s", url)
        return ""


def fetch_snippets(urls: list[str], max_snippets: int = 3) -> list[str]:
    """複数 URL から本文スニペットを収集"""
    snippets: list[str] = []
    for url in urls:
        if len(snippets) >= max_snippets:
            break
        text = fetch_article_text(url)
        if text:
            snippets.append(text)
    return snippets
