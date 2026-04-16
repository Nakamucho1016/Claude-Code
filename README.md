# 今日のトレンドまとめ — SNS トレンド自動まとめサイトジェネレーター

SNS（X、Instagram 等）で話題になっているトレンドを毎日自動で収集し、信頼できるニュースソースから情報を裏取りした上で、一般読者向けのわかりやすい解説記事を自動生成・公開するシステムです。

## 仕組み

```
Google Trends ─┐
               ├→ 上位5件選出 → NHK/Yahoo!/Google News
Yahoo! RT検索 ─┘     ↓              ↓
                  トレンド      ニュース記事収集
                     ↓              ↓
                  Claude API で平易な解説記事を生成
                     ↓
                  静的 HTML サイトとして公開 (GitHub Pages)
```

### パイプライン

1. **トレンド収集** — Google Trends・Yahoo! リアルタイム検索から急上昇ワードを取得
2. **ニュースリサーチ** — NHK / Yahoo!ニュース / Google News の RSS から関連記事を収集
3. **記事生成** — Claude API（Anthropic）で、人気まとめサイトの手法を取り入れたスタイルガイドに基づき解説記事を生成
4. **サイト公開** — Jinja2 テンプレートで HTML を生成し、GitHub Pages にデプロイ

### 記事の特長

- キャッチーだが煽りすぎないタイトル（40 字以内）
- 結論ファーストのリード文で「読む価値」を即座に伝達
- 見出しだけで記事全体が把握できる構成
- 中学生でも理解できる平易な日本語
- 最低 3 件以上の出典リンク付き
- AI 生成コンテンツである旨を明記

## セットアップ

### 前提条件

- Python 3.11 以上
- [Anthropic API キー](https://console.anthropic.com/)

### ローカル実行

```bash
# 依存インストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
# .env を編集して ANTHROPIC_API_KEY を記入

# ドライラン（API を呼ばずにトレンド収集・リサーチまで確認）
python -m matome.cli run --limit 2 --dry-run -v

# 記事を生成
python -m matome.cli run --limit 2 -v

# 生成結果を確認
open site/index.html
```

### GitHub Actions による自動実行

1. リポジトリの **Settings > Secrets and variables > Actions** で `ANTHROPIC_API_KEY` を登録
2. **Settings > Pages** で Source を **GitHub Actions** に設定
3. 毎朝 JST 07:00 に自動実行されます（手動実行も可: **Actions > Daily Matome Generation > Run workflow**）

## 設定項目

| 環境変数 | デフォルト | 説明 |
|---|---|---|
| `ANTHROPIC_API_KEY` | （必須） | Anthropic API キー |
| `MATOME_MODEL` | `claude-haiku-4-5-20251001` | 使用する Claude モデル |
| `MATOME_LIMIT` | `5` | 1 回あたりの最大記事数 |
| `MATOME_SITE_URL` | `https://example.github.io/matome` | サイト公開 URL（OGP 用） |
| `MATOME_SITE_TITLE` | `今日のトレンドまとめ` | サイトタイトル |

## 開発

```bash
# 開発用依存を含めてインストール
pip install -e ".[dev]"

# テスト実行
python -m pytest tests/ -v

# Lint
ruff check src/ tests/
ruff format src/ tests/
```

## プロジェクト構成

```
src/matome/
├── config.py          # 設定ローダー
├── models.py          # データモデル（Pydantic）
├── trends/            # トレンド収集
│   ├── aggregator.py  # ソース統合・スコアリング
│   ├── google_trends.py
│   └── yahoo_realtime.py
├── research/          # ニュースリサーチ
│   ├── news_rss.py    # RSS フィード検索
│   └── fetcher.py     # 記事本文抽出
├── summarizer.py      # Claude API による記事生成
├── publisher.py       # HTML サイト生成
├── pipeline.py        # パイプラインオーケストレータ
└── cli.py             # CLI エントリポイント
```

## 法務・倫理

- 各記事に **AI 生成コンテンツである旨** を明記しています
- 出典リンクを記事内に明示し、原文の長文引用は行いません
- スクレイピングは `robots.txt` を遵守し、User-Agent を明示、低レートで実行します
- 個人のプライバシーを侵害するリスクのあるトピックは自動フィルタで記事化をスキップします

## ライセンス

コード: MIT License  
生成記事: CC BY 4.0 相当（出典の明記をお願いします）
