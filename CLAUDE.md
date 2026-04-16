# CLAUDE.md

## プロジェクト概要

SNS トレンド自動まとめサイトジェネレーター。毎日トレンドを収集し、Claude API で解説記事を生成して静的サイトとして公開する。

## 技術スタック

- Python 3.11+, Pydantic, httpx, feedparser, pytrends, trafilatura, Jinja2, Anthropic SDK
- GitHub Actions (日次 cron) + GitHub Pages

## パッケージ構成

- `src/matome/` — メインパッケージ（`pyproject.toml` の `[tool.setuptools.packages.find]` で `src` を指定）
- `templates/` — Jinja2 HTML テンプレート
- `site/` — 生成される静的サイト（GitHub Pages で配信）
- `tests/` — pytest テスト

## よく使うコマンド

```bash
# テスト
python -m pytest tests/ -v

# Lint
ruff check src/ tests/
ruff format src/ tests/

# ローカル実行
python -m matome.cli run --limit 2 --dry-run -v
python -m matome.cli run --limit 2 -v
```

## アーキテクチャメモ

- `trends/` はプラガブル設計。`TrendSourceProtocol` を実装すれば新しいソースを追加可能
- `summarizer.py` の system プロンプトにスタイルガイドを埋め込み、`cache_control` でプロンプトキャッシングを有効化
- `publisher.py` は簡易 Markdown→HTML 変換を内蔵（外部依存なし）
- `articles.json` で過去 7 日間の重複トピックを除外
