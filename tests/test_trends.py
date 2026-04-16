"""トレンド収集モジュールのテスト"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from matome.models import TrendItem, TrendSource
from matome.trends.aggregator import _normalize, aggregate_trends


class TestNormalize:
    def test_basic(self):
        assert _normalize("  Hello World  ") == "hello world"

    def test_nfkc(self):
        # 全角 → 半角
        assert _normalize("Ｈｅｌｌｏ") == "hello"

    def test_whitespace(self):
        assert _normalize("a  b\t c") == "a b c"


class TestAggregateTrends:
    @patch("matome.trends.aggregator.YahooRealtimeSource")
    @patch("matome.trends.aggregator.GoogleTrendsSource")
    def test_merges_and_deduplicates(self, mock_google_cls, mock_yahoo_cls):
        """同一キーワードが複数ソースから出た場合にスコアが合算される"""
        mock_google = MagicMock()
        mock_google.fetch.return_value = [
            TrendItem(keyword="AI", source=TrendSource.GOOGLE_TRENDS, rank=1, score=20),
            TrendItem(keyword="Python", source=TrendSource.GOOGLE_TRENDS, rank=2, score=19),
        ]
        mock_google_cls.return_value = mock_google

        mock_yahoo = MagicMock()
        mock_yahoo.fetch.return_value = [
            TrendItem(keyword="ai", source=TrendSource.YAHOO_REALTIME, rank=1, score=20),
            TrendItem(keyword="Rust", source=TrendSource.YAHOO_REALTIME, rank=2, score=19),
        ]
        mock_yahoo_cls.return_value = mock_yahoo

        with patch("matome.trends.aggregator._load_recent_keywords", return_value=set()):
            with patch("matome.trends.aggregator.get_settings") as mock_settings:
                mock_settings.return_value.matome_limit = 5
                mock_settings.return_value.matome_dedup_days = 7
                result = aggregate_trends(limit=3)

        assert len(result) == 3
        # "AI" / "ai" は合算されてトップスコアになるはず
        assert result[0].keyword.lower() == "ai"
        assert result[0].score == 40  # 20 + 20

    @patch("matome.trends.aggregator.YahooRealtimeSource")
    @patch("matome.trends.aggregator.GoogleTrendsSource")
    def test_empty_sources(self, mock_google_cls, mock_yahoo_cls):
        """全ソースが空の場合"""
        mock_google_cls.return_value.fetch.return_value = []
        mock_yahoo_cls.return_value.fetch.return_value = []

        with patch("matome.trends.aggregator.get_settings") as mock_settings:
            mock_settings.return_value.matome_limit = 5
            mock_settings.return_value.matome_dedup_days = 7
            result = aggregate_trends(limit=5)

        assert result == []

    @patch("matome.trends.aggregator.YahooRealtimeSource")
    @patch("matome.trends.aggregator.GoogleTrendsSource")
    def test_dedup_recent(self, mock_google_cls, mock_yahoo_cls):
        """過去に記事化済みのキーワードは除外される"""
        mock_google_cls.return_value.fetch.return_value = [
            TrendItem(keyword="AI", source=TrendSource.GOOGLE_TRENDS, rank=1, score=20),
            TrendItem(keyword="Python", source=TrendSource.GOOGLE_TRENDS, rank=2, score=19),
        ]
        mock_yahoo_cls.return_value.fetch.return_value = []

        with patch(
            "matome.trends.aggregator._load_recent_keywords",
            return_value={"ai"},  # "AI" は既出
        ):
            with patch("matome.trends.aggregator.get_settings") as mock_settings:
                mock_settings.return_value.matome_limit = 5
                mock_settings.return_value.matome_dedup_days = 7
                result = aggregate_trends(limit=5)

        assert len(result) == 1
        assert result[0].keyword == "Python"
