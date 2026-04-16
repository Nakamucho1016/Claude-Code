"""Yahoo! リアルタイム検索のトレンド取得"""

from __future__ import annotations

import logging
import time
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from matome.config import get_settings
from matome.models import TrendItem, TrendSource

logger = logging.getLogger(__name__)

YAHOO_REALTIME_URL = "https://search.yahoo.co.jp/realtime"
YAHOO_ROBOTS_URL = "https://search.yahoo.co.jp/robots.txt"


class YahooRealtimeSource:
    """Yahoo! リアルタイム検索のトレンドワードをスクレイピング"""

    def _check_robots(self) -> bool:
        """robots.txt でアクセス許可を確認"""
        try:
            settings = get_settings()
            rp = RobotFileParser()
            rp.set_url(YAHOO_ROBOTS_URL)
            rp.read()
            allowed = rp.can_fetch(settings.http_user_agent, YAHOO_REALTIME_URL)
            if not allowed:
                logger.warning("robots.txt でアクセスが拒否されています: %s", YAHOO_REALTIME_URL)
            return allowed
        except Exception:
            logger.warning("robots.txt の取得に失敗、安全側に倒してスキップ")
            return False

    def fetch(self) -> list[TrendItem]:
        if not self._check_robots():
            return []

        settings = get_settings()
        try:
            time.sleep(settings.http_delay)
            with httpx.Client(
                timeout=settings.http_timeout,
                headers={"User-Agent": settings.http_user_agent},
                follow_redirects=True,
            ) as client:
                resp = client.get(YAHOO_REALTIME_URL)
                resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            items: list[TrendItem] = []

            # トレンドワードのリンク要素を探索（複数セレクタで堅牢性確保）
            selectors = [
                "a[data-cl-params*='trend']",
                ".trend-list a",
                "#contents a[href*='search?p=']",
                "ol li a",
            ]

            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    for rank, el in enumerate(elements[:20]):
                        keyword = el.get_text(strip=True)
                        if keyword and len(keyword) <= 50:
                            items.append(
                                TrendItem(
                                    keyword=keyword,
                                    source=TrendSource.YAHOO_REALTIME,
                                    rank=rank + 1,
                                    score=max(0, 20 - rank),
                                )
                            )
                    break

            logger.info("Yahoo! リアルタイム: %d 件取得", len(items))
            return items

        except Exception:
            logger.exception("Yahoo! リアルタイム検索の取得に失敗")
            return []
