"""パイプラインオーケストレータ — trends → research → summarize → publish"""

from __future__ import annotations

import logging
from datetime import date

from matome.models import ArticleRecord, GeneratedArticle, ResearchResult
from matome.publisher import publish
from matome.research.fetcher import fetch_snippets
from matome.research.news_rss import search_news
from matome.summarizer import generate_article
from matome.trends.aggregator import aggregate_trends

logger = logging.getLogger(__name__)


def _research_topic(keyword: str) -> ResearchResult:
    """1 トピックについてニュースソースを収集しスニペットを取得"""
    logger.info("リサーチ開始: %s", keyword)

    sources = search_news(keyword, max_results=5)
    urls = [s.url for s in sources if s.url]
    snippets = fetch_snippets(urls, max_snippets=3)

    result = ResearchResult(
        keyword=keyword,
        sources=sources,
        snippets=snippets,
    )
    logger.info(
        "リサーチ完了: %s (情報源 %d 件, スニペット %d 件)",
        keyword,
        len(sources),
        len(snippets),
    )
    return result


def run_pipeline(
    limit: int = 5,
    dry_run: bool = False,
) -> list[ArticleRecord]:
    """全パイプラインを実行

    Args:
        limit: 生成する最大記事数
        dry_run: True の場合、Claude API を呼ばずトレンド収集・リサーチまでで停止

    Returns:
        生成した記事レコードのリスト
    """
    today = date.today()
    logger.info("=== パイプライン開始 (%s, limit=%d, dry_run=%s) ===", today, limit, dry_run)

    # 1. トレンド収集
    trends = aggregate_trends(limit=limit)
    if not trends:
        logger.error("トレンドが取得できませんでした。パイプラインを終了します。")
        return []

    logger.info("トレンド: %s", [t.keyword for t in trends])

    # 2. 各トピックをリサーチ
    researches: list[ResearchResult] = []
    for trend in trends:
        try:
            result = _research_topic(trend.keyword)
            researches.append(result)
        except Exception:
            logger.exception("リサーチ失敗: %s（スキップ）", trend.keyword)

    if dry_run:
        logger.info("=== dry-run モード: リサーチ結果 ===")
        for r in researches:
            logger.info(
                "  %s: 情報源 %d 件, スニペット %d 件",
                r.keyword,
                len(r.sources),
                len(r.snippets),
            )
        return []

    # 3. 記事生成
    generated: list[tuple[str, GeneratedArticle]] = []
    for research in researches:
        try:
            article = generate_article(research)
            if article:
                generated.append((research.keyword, article))
        except Exception:
            logger.exception("記事生成失敗: %s（スキップ）", research.keyword)

    if not generated:
        logger.warning("生成できた記事が 0 件でした")
        return []

    # 4. サイト公開
    records = publish(generated, today=today)
    logger.info("=== パイプライン完了: %d 件の記事を生成 ===", len(records))
    return records
