"""Google Trends からの急上昇ワード取得"""

from __future__ import annotations

import logging

from pytrends.request import TrendReq

from matome.models import TrendItem, TrendSource

logger = logging.getLogger(__name__)


class GoogleTrendsSource:
    """pytrends を使って日本の急上昇ワードを取得"""

    def fetch(self) -> list[TrendItem]:
        try:
            pytrends = TrendReq(hl="ja-JP", tz=-540)
            df = pytrends.trending_searches(pn="japan")

            items: list[TrendItem] = []
            for rank, row in enumerate(df.values):
                keyword = str(row[0]).strip()
                if keyword:
                    items.append(
                        TrendItem(
                            keyword=keyword,
                            source=TrendSource.GOOGLE_TRENDS,
                            rank=rank + 1,
                            score=max(0, 20 - rank),  # 1位=20pt, 20位=1pt
                        )
                    )
            logger.info("Google Trends: %d 件取得", len(items))
            return items

        except Exception:
            logger.exception("Google Trends の取得に失敗")
            return []
