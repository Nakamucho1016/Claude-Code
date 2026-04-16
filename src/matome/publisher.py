"""HTML サイト生成 — Jinja2 テンプレートから静的ファイルを書き出す"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from datetime import date, datetime
from xml.etree.ElementTree import Element, SubElement, tostring

from jinja2 import Environment, FileSystemLoader

from matome.config import ARTICLES_JSON, DATA_DIR, SITE_DIR, TEMPLATES_DIR, get_settings
from matome.models import ArticleRecord, GeneratedArticle

logger = logging.getLogger(__name__)


def _slugify(text: str) -> str:
    """日本語テキストを URL スラグに変換"""
    # NFKC正規化
    text = unicodedata.normalize("NFKC", text)
    # ASCII文字・数字・ハイフン以外はハイフンに置換
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = text.strip("-").lower()
    # 空になった場合はタイムスタンプをスラグに
    if not text:
        text = datetime.now().strftime("%H%M%S")
    return text[:80]


def _load_articles() -> list[dict]:
    """既存の articles.json を読み込む"""
    if not ARTICLES_JSON.exists():
        return []
    try:
        return json.loads(ARTICLES_JSON.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("articles.json の読み込みに失敗、空リストで続行")
        return []


def _save_articles(records: list[dict]) -> None:
    """articles.json を保存"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARTICLES_JSON.write_text(
        json.dumps(records, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def _get_jinja_env() -> Environment:
    """Jinja2 テンプレート環境を生成"""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    # カスタムフィルタ
    env.filters["truncate_chars"] = lambda s, n: s[:n] + "…" if len(s) > n else s
    return env


def _render_markdown_to_html(md: str) -> str:
    """簡易 Markdown → HTML 変換（外部依存なし）"""
    lines = md.split("\n")
    html_parts: list[str] = []
    in_list = False
    in_ol = False

    for line in lines:
        stripped = line.strip()

        # 見出し
        if stripped.startswith("### "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            html_parts.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("## "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            html_parts.append(f"<h2>{stripped[3:]}</h2>")

        # 箇条書き
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            content = stripped[2:]
            content = _inline_md(content)
            html_parts.append(f"<li>{content}</li>")

        # 番号リスト
        elif re.match(r"^\d+\.\s", stripped):
            if not in_ol:
                html_parts.append("<ol>")
                in_ol = True
            content = re.sub(r"^\d+\.\s", "", stripped)
            content = _inline_md(content)
            html_parts.append(f"<li>{content}</li>")

        # 空行
        elif not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False

        # 通常テキスト
        else:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            content = _inline_md(stripped)
            html_parts.append(f"<p>{content}</p>")

    if in_list:
        html_parts.append("</ul>")
    if in_ol:
        html_parts.append("</ol>")

    return "\n".join(html_parts)


def _inline_md(text: str) -> str:
    """インラインの Markdown（太字、脚注リンク）を HTML に変換"""
    # 太字 **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # 脚注 [1] → 上付き文字
    text = re.sub(r"\[(\d+)\]", r'<sup class="footnote">[\1]</sup>', text)
    return text


def _generate_feed(records: list[dict], site_url: str, site_title: str) -> str:
    """RSS 2.0 フィードを生成"""
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = site_title
    SubElement(channel, "link").text = site_url
    SubElement(channel, "description").text = f"{site_title} — AI による自動トレンドまとめ"
    SubElement(channel, "language").text = "ja"

    for rec in records[:20]:
        item = SubElement(channel, "item")
        SubElement(item, "title").text = rec.get("title", "")
        SubElement(item, "link").text = f"{site_url}/{rec.get('url', '')}"
        SubElement(item, "description").text = rec.get("lede", "")
        SubElement(item, "pubDate").text = rec.get("date", "")

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(rss, encoding="unicode")


def publish(
    articles: list[tuple[str, GeneratedArticle]],
    today: date | None = None,
) -> list[ArticleRecord]:
    """生成記事を HTML ファイルとして書き出し、インデックスを更新"""
    settings = get_settings()
    today = today or date.today()
    date_str = today.isoformat()
    env = _get_jinja_env()

    # 出力ディレクトリ
    articles_dir = SITE_DIR / "articles" / date_str
    articles_dir.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "assets").mkdir(parents=True, exist_ok=True)

    existing_records = _load_articles()
    new_records: list[ArticleRecord] = []

    # 同日の他記事タイトル（関連トピックリンク用）
    sibling_titles: list[dict[str, str]] = []

    for keyword, article in articles:
        slug = _slugify(article.title)
        rel_url = f"articles/{date_str}/{slug}.html"
        record = ArticleRecord(
            slug=slug,
            title=article.title,
            lede=article.lede,
            tags=article.tags,
            date=today,
            url=rel_url,
            sources=article.sources,
            reading_time_min=article.reading_time_min,
            keyword=keyword,
        )
        new_records.append(record)
        sibling_titles.append({"title": article.title, "url": slug + ".html"})

    # 各記事を HTML に書き出し
    article_tmpl = env.get_template("article.html")
    for i, (keyword, article) in enumerate(articles):
        record = new_records[i]
        body_html = _render_markdown_to_html(article.body_markdown)

        # 関連記事（自分以外の同日記事）
        related = [s for s in sibling_titles if s["title"] != article.title]

        html = article_tmpl.render(
            article=article,
            body_html=body_html,
            record=record,
            date_str=date_str,
            related=related,
            site_title=settings.matome_site_title,
            site_url=settings.matome_site_url,
            base_path=settings.matome_base_path,
        )
        out_path = articles_dir / f"{record.slug}.html"
        out_path.write_text(html, encoding="utf-8")
        logger.info("記事出力: %s", out_path)

    # articles.json 更新
    all_records = [r.model_dump(mode="json") for r in new_records] + existing_records
    _save_articles(all_records)

    # トップページ
    index_tmpl = env.get_template("index.html")
    index_html = index_tmpl.render(
        articles=all_records[:20],
        site_title=settings.matome_site_title,
        site_url=settings.matome_site_url,
        base_path=settings.matome_base_path,
        today=date_str,
    )
    (SITE_DIR / "index.html").write_text(index_html, encoding="utf-8")

    # アーカイブページ
    archive_tmpl = env.get_template("archive.html")
    # 日付ごとにグループ化
    by_date: dict[str, list[dict]] = {}
    for rec in all_records:
        d = str(rec.get("date", ""))
        by_date.setdefault(d, []).append(rec)

    archive_html = archive_tmpl.render(
        by_date=by_date,
        site_title=settings.matome_site_title,
        base_path=settings.matome_base_path,
    )
    (SITE_DIR / "archive.html").write_text(archive_html, encoding="utf-8")

    # RSS フィード
    feed_xml = _generate_feed(all_records, settings.matome_site_url, settings.matome_site_title)
    (SITE_DIR / "feed.xml").write_text(feed_xml, encoding="utf-8")

    logger.info("サイト生成完了: %d 件の新規記事", len(new_records))
    return new_records
