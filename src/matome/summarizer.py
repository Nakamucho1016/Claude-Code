"""Claude API による記事生成 — 人気まとめサイトの手法を取り入れたスタイルガイド付き"""

from __future__ import annotations

import json
import logging

import anthropic
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from matome.config import get_settings
from matome.models import Confidence, GeneratedArticle, ResearchResult

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# スタイルガイド（system プロンプト）
# 人気まとめサイト・ニュースメディアの手法をリサーチして策定
# ──────────────────────────────────────────────
STYLE_GUIDE_SYSTEM = """\
あなたは日本の人気ニュースまとめサイトのベテラン編集者です。
SNSで話題になっているトピックについて、複数の信頼できる情報源を元に、
一般読者が「面白い」「わかりやすい」と感じる解説記事を作成してください。

## タイトルの書き方（40字以内）
- 数字を含める：「3つの理由」「5分でわかる」等で具体性と信頼性を演出
- 疑問形・反語形で好奇心を喚起：「なぜ○○が話題に？」「○○は本当？」
- キーワードは先頭15字以内に配置（SNSカードや検索結果で目に入る位置）
- 読者のベネフィットを示す：「サクッとわかる」「これだけ読めばOK」
- 煽りすぎない。タイトルと本文内容は必ず一致させること
- 釣りタイトル・誇大表現は厳禁

## リード文の書き方（100〜150字）
- 共感文で始める：「○○が話題ですが、結局なにが問題なの？と感じた方も多いはず。」
- 結論ファースト：最初の1〜2文で「要するにこういう話」と要点を提示
- 読む理由を提示：「この記事では、背景・影響・今後の見通しを3分でまとめました。」

## 本文の書き方（800〜1200字、Markdown形式）
### 構成
1. **背景・経緯** — 何が起きたのか、時系列で簡潔に
2. **ポイント解説** — なぜ話題なのか、核心を2〜3点に絞って説明
3. **影響・今後の見通し** — 私たちの生活や社会にどう影響するか
4. **まとめ** — 2〜3行で要点を再整理

### 文章スタイル
- 中学生でも理解できる平易な日本語を使う
- 専門用語は初出時にカッコ書きで平易に説明する
- 1段落は60字×3〜4行（180〜240字）以内。長くなったら分割する
- 箇条書き・番号リストを積極的に使い、スマホでもスキャンしやすくする
- 見出し（##, ###）だけ読めば記事全体が把握できるように書く
- 見出しは25字以内、体言止めまたは疑問形で簡潔に
- 事実と推測は明確に書き分ける（「〜とされています」「〜という見方もあります」）
- 適宜 **太字** で重要キーワードを強調（1段落に1〜2箇所まで）
- 読了時間は約3分を目安にする

### 出典の扱い
- 本文中に [1], [2] 形式の脚注番号を埋め込む
- 出典は最低3件以上
- 原文の長文引用はしない（著作権に配慮し、要約・言い換えで伝える）

## 品質チェック
- 情報源が不十分で正確な記事が書けない場合は confidence を "low" にする
- 個人のスキャンダル・プライバシー侵害に該当するトピックは記事化しない（confidence を "low" にする）
- 特定の個人・団体を中傷する表現は使わない

## 出力形式
以下のJSON形式で出力してください。JSON以外のテキストは出力しないでください。
```json
{
  "title": "40字以内のキャッチーなタイトル",
  "lede": "100〜150字のリード文",
  "body_markdown": "Markdown形式の本文（800〜1200字）",
  "sources": [
    {"name": "媒体名", "title": "記事タイトル", "url": "https://..."}
  ],
  "tags": ["タグ1", "タグ2"],
  "reading_time_min": 3,
  "confidence": "high"
}
```
"""


def _build_user_prompt(research: ResearchResult) -> str:
    """リサーチ結果からユーザープロンプトを構築"""
    parts = [
        f"# トピック: {research.keyword}\n",
        "## 収集した情報源:\n",
    ]

    for i, src in enumerate(research.sources, 1):
        parts.append(f"[{i}] {src.name} — {src.title}")
        parts.append(f"    URL: {src.url}")
        if src.published:
            parts.append(f"    公開日: {src.published}")
        parts.append("")

    if research.snippets:
        parts.append("## 本文抜粋:\n")
        for i, snippet in enumerate(research.snippets, 1):
            parts.append(f"--- 記事{i} ---")
            parts.append(snippet[:2000])
            parts.append("")

    parts.append("上記の情報を元に、スタイルガイドに従って解説記事をJSON形式で生成してください。")
    return "\n".join(parts)


@retry(
    retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIStatusError)),
    wait=wait_exponential(multiplier=2, min=2, max=60),
    stop=stop_after_attempt(3),
)
def _call_claude(system: str, user: str, model: str, api_key: str) -> str:
    """Claude API を呼び出して応答テキストを取得"""
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def generate_article(research: ResearchResult) -> GeneratedArticle | None:
    """リサーチ結果から解説記事を生成"""
    settings = get_settings()

    if not settings.anthropic_api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY が設定されていません。"
            ".env ファイルまたは環境変数で設定してください。"
        )

    user_prompt = _build_user_prompt(research)

    logger.info("記事生成開始: %s (model=%s)", research.keyword, settings.matome_model)

    raw = _call_claude(
        system=STYLE_GUIDE_SYSTEM,
        user=user_prompt,
        model=settings.matome_model,
        api_key=settings.anthropic_api_key,
    )

    # JSON パース
    try:
        # コードブロックで囲まれている場合に対応
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.error("Claude のレスポンスが不正な JSON: %s...", raw[:200])
        return None

    try:
        article = GeneratedArticle(**data)
    except Exception:
        logger.exception("GeneratedArticle のバリデーションに失敗")
        return None

    # 低確度の記事はスキップ
    if article.confidence == Confidence.LOW:
        logger.warning("情報確度が低いためスキップ: %s (confidence=low)", research.keyword)
        return None

    logger.info("記事生成完了: %s", article.title)
    return article
