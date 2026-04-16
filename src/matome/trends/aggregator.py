"""複数のトレンドソースを統合し、上位トピックを選出する"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from datetime import date, timedelta

from matome.config import ARTICLES_JSON, get_settings
from matome.models import TrendItem
from matome.trends.google_trends import GoogleTrendsSource
from matome.trends.yahoo_realtime import YahooRealtimeSource

logger = logging.getLogger(__name__)


def _normalize(keyword: str) -> str:
    """キーワードを正規化して表記ゆれを吸収"""
    # NFKC 正規化 → 小文字化 → 空白統一
    s = unicodedata.normalize("NFKC", keyword)
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _load_recent_keywords(days: int) -> set[str]:
    """過去 N 日間に記事化済みのキーワードを取得"""
    if not ARTICLES_JSON.exists():
        return set()

    try:
        records = json.loads(ARTICLES_JSON.read_text(encoding="utf-8"))
        cutoff = date.today() - timedelta(days=days)
        recent: set[str] = set()
        for rec in records:
            rec_date = date.fromisoformat(rec.get("date", "2000-01-01"))
            if rec_date >= cutoff:
                kw = rec.get("keyword", "")
                if kw:
                    recent.add(_normalize(kw))
        return recent
    except Exception:
        logger.warning("articles.json の読み込みに失敗、重複チェックをスキップ")
        return set()


def aggregate_trends(limit: int | None = None) -> list[TrendItem]:
    """全ソースからトレンドを収集し、重複排除・スコアリングして上位を返す"""
    settings = get_settings()
    limit = limit or settings.matome_limit

    # 各ソースから取得
    sources = [
        GoogleTrendsSource(),
        YahooRealtimeSource(),
    ]

    all_items: list[TrendItem] = []
    for src in sources:
        all_items.extend(src.fetch())

    if not all_items:
        logger.warning("トレンドが 1 件も取得できませんでした")
        return []

    # 正規化キーで統合・スコア合算
    merged: dict[str, TrendItem] = {}
    for item in all_items:
        key = _normalize(item.keyword)
        if key in merged:
            merged[key].score += item.score
        else:
            merged[key] = item.model_copy()

    # 過去に記事化済みのキーワードを除外
    recent_keywords = _load_recent_keywords(settings.matome_dedup_days)
    candidates = {k: v for k, v in merged.items() if k not in recent_keywords}

    if not candidates:
        logger.warning("重複除外後のトレンドが 0 件です")
        return list(merged.values())[:limit]

    # スコア降順でソートし上位を返す
    sorted_items = sorted(candidates.values(), key=lambda t: t.score, reverse=True)
    result = sorted_items[:limit]
    logger.info(
        "トレンド集約完了: %d 件 → %d 件 (上位 %d 件選出)",
        len(all_items),
        len(candidates),
        len(result),
    )
    return result
