"""パイプラインのテスト（Claude API はモック）"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

from matome.models import (
    Confidence,
    GeneratedArticle,
    NewsSource,
)
from matome.publisher import _render_markdown_to_html, _slugify, publish


class TestSlugify:
    def test_ascii(self):
        assert _slugify("Hello World") == "hello-world"

    def test_empty(self):
        slug = _slugify("！？")
        assert len(slug) > 0  # タイムスタンプフォールバック

    def test_long_text(self):
        slug = _slugify("a" * 200)
        assert len(slug) <= 80


class TestRenderMarkdown:
    def test_headings(self):
        md = "## 見出し2\n### 見出し3"
        html = _render_markdown_to_html(md)
        assert "<h2>見出し2</h2>" in html
        assert "<h3>見出し3</h3>" in html

    def test_bullet_list(self):
        md = "- 項目1\n- 項目2"
        html = _render_markdown_to_html(md)
        assert "<ul>" in html
        assert "<li>項目1</li>" in html

    def test_numbered_list(self):
        md = "1. 最初\n2. 次"
        html = _render_markdown_to_html(md)
        assert "<ol>" in html
        assert "<li>最初</li>" in html

    def test_bold(self):
        md = "これは**重要**です"
        html = _render_markdown_to_html(md)
        assert "<strong>重要</strong>" in html

    def test_footnote(self):
        md = "事実です[1]。"
        html = _render_markdown_to_html(md)
        assert 'class="footnote"' in html
        assert "[1]" in html


class TestPublish:
    def test_publish_creates_files(self, tmp_path):
        """publish が HTML ファイルと articles.json を正しく生成する"""
        # テスト用にパスを上書き
        site_dir = tmp_path / "site"
        templates_dir = tmp_path / "templates"
        data_dir = site_dir / "data"
        articles_json = data_dir / "articles.json"

        # テンプレートをコピー
        templates_dir.mkdir()
        src_templates = Path(__file__).parent.parent / "templates"
        for tmpl in src_templates.glob("*.html"):
            (templates_dir / tmpl.name).write_text(tmpl.read_text(), encoding="utf-8")

        article = GeneratedArticle(
            title="テスト記事のタイトル",
            lede="これはテスト用のリード文です。テスト用のリード文です。テスト用のリード文です。テスト用のリード文です。",
            body_markdown="## 背景\n\nテスト本文です。\n\n- ポイント1\n- ポイント2",
            sources=[
                NewsSource(name="NHK", title="テストニュース", url="https://example.com/1"),
                NewsSource(name="Yahoo!", title="テスト2", url="https://example.com/2"),
                NewsSource(name="朝日", title="テスト3", url="https://example.com/3"),
            ],
            tags=["テスト", "AI"],
            reading_time_min=3,
            confidence=Confidence.HIGH,
        )

        with (
            patch("matome.publisher.SITE_DIR", site_dir),
            patch("matome.publisher.TEMPLATES_DIR", templates_dir),
            patch("matome.publisher.DATA_DIR", data_dir),
            patch("matome.publisher.ARTICLES_JSON", articles_json),
            patch("matome.publisher.get_settings") as mock_settings,
        ):
            mock_settings.return_value.matome_site_title = "テストサイト"
            mock_settings.return_value.matome_site_url = "https://test.example.com"

            records = publish(
                [("テスト", article)],
                today=date(2026, 4, 16),
            )

        assert len(records) == 1
        assert records[0].title == "テスト記事のタイトル"

        # index.html が生成されている
        assert (site_dir / "index.html").exists()

        # articles.json が生成されている
        assert articles_json.exists()
        data = json.loads(articles_json.read_text())
        assert len(data) == 1
        assert data[0]["title"] == "テスト記事のタイトル"

        # 記事 HTML が生成されている
        article_dir = site_dir / "articles" / "2026-04-16"
        assert article_dir.exists()
        html_files = list(article_dir.glob("*.html"))
        assert len(html_files) == 1

        # feed.xml が生成されている
        assert (site_dir / "feed.xml").exists()
