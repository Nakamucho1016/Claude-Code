"""設定ローダー — 環境変数から設定を読み込む"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

# プロジェクトルートディレクトリ
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
SITE_DIR = PROJECT_ROOT / "site"
DATA_DIR = SITE_DIR / "data"
ARTICLES_JSON = DATA_DIR / "articles.json"


class Settings(BaseSettings):
    """アプリケーション設定（環境変数 or .env から読み込み）"""

    # Anthropic API
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    matome_model: str = Field(
        default="claude-haiku-4-5-20251001",
        description="使用する Claude モデル",
    )

    # 生成設定
    matome_limit: int = Field(default=5, description="1回あたりの最大記事数")
    matome_dedup_days: int = Field(default=7, description="重複除外する過去日数")

    # サイト設定
    matome_site_url: str = Field(
        default="https://example.github.io/matome",
        description="サイトの公開 URL（OGP 用）",
    )
    matome_site_title: str = Field(
        default="今日のトレンドまとめ",
        description="サイトタイトル",
    )

    # HTTP 設定
    http_user_agent: str = Field(
        default="MatomeBot/0.1 (+https://github.com/matome-bot)",
        description="HTTP リクエストの User-Agent",
    )
    http_timeout: float = Field(default=15.0, description="HTTP タイムアウト秒")
    http_delay: float = Field(default=1.0, description="リクエスト間のスリープ秒")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


def get_settings() -> Settings:
    """設定シングルトンを取得"""
    return Settings()
