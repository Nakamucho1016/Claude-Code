"""データモデル定義"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class TrendSource(str, Enum):
    """トレンドの取得元"""

    GOOGLE_TRENDS = "google_trends"
    YAHOO_REALTIME = "yahoo_realtime"


class TrendItem(BaseModel):
    """トレンドトピック 1 件"""

    keyword: str = Field(description="トレンドキーワード")
    source: TrendSource = Field(description="取得元")
    rank: int = Field(default=0, description="取得元でのランク")
    score: float = Field(default=0.0, description="スコアリング後の重み")


class NewsSource(BaseModel):
    """ニュース記事の出典"""

    name: str = Field(description="媒体名 (例: NHK)")
    title: str = Field(description="記事タイトル")
    url: str = Field(description="記事 URL")
    published: str = Field(default="", description="公開日時")


class ResearchResult(BaseModel):
    """1 トピックに対するリサーチ結果"""

    keyword: str = Field(description="トレンドキーワード")
    sources: list[NewsSource] = Field(default_factory=list, description="収集した出典一覧")
    snippets: list[str] = Field(default_factory=list, description="本文抜粋テキスト一覧")


class Confidence(str, Enum):
    """記事の情報確度"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GeneratedArticle(BaseModel):
    """Claude が生成した記事"""

    title: str = Field(description="40 字以内のキャッチーなタイトル")
    lede: str = Field(description="100〜150 字のリード文")
    body_markdown: str = Field(description="Markdown 形式の本文")
    sources: list[NewsSource] = Field(description="出典リスト")
    tags: list[str] = Field(default_factory=list, description="タグ一覧")
    reading_time_min: int = Field(default=3, description="推定読了時間（分）")
    confidence: Confidence = Field(default=Confidence.HIGH, description="情報の確度")


class ArticleRecord(BaseModel):
    """articles.json に保存する記事レコード"""

    slug: str = Field(description="URL スラグ")
    title: str
    lede: str
    tags: list[str] = Field(default_factory=list)
    date: date
    url: str = Field(description="記事の相対パス")
    sources: list[NewsSource] = Field(default_factory=list)
    reading_time_min: int = Field(default=3)
    generated_at: datetime = Field(default_factory=datetime.now)
    keyword: str = Field(default="", description="元のトレンドキーワード")
