"""デモ用スクリプト — サンプルデータで HTML サイトを生成して出力を確認する"""

from datetime import date
from matome.models import Confidence, GeneratedArticle, NewsSource
from matome.publisher import publish

# ── サンプル記事データ（Claude が生成する想定の出力を再現）──

SAMPLE_ARTICLES = [
    (
        "AI規制法案",
        GeneratedArticle(
            title="AI規制法が国会通過へ — 私たちの生活はどう変わる？3つのポイント",
            lede="AIの利用に関する新たな法規制がいよいよ国会で審議入りし、SNSでも大きな話題になっています。「結局、何が規制されるの？」と気になっている方も多いはず。この記事では、法案の概要・影響・今後の見通しを3分でまとめました。",
            body_markdown="""## 何が起きている？ — AI規制法案の概要

2026年4月、政府は**AI利用に関する包括的な規制法案**を国会に提出しました。この法案は、生成AIを業務利用する企業に対して、AIが生成したコンテンツへの明示的なラベル表示を義務付けるものです[1]。

欧州の「AI Act」に続き、日本でも本格的なAI規制の枠組みが整備されることになります。

## なぜ話題？ — 3つの注目ポイント

### 1. AI生成コンテンツに「AIラベル」が必須に

企業がAIで作成した広告・記事・画像などには、**「AI生成」の表示が義務化**されます。違反した場合は最大500万円の罰金が科される可能性があります[2]。

### 2. 個人利用は対象外

SNSでの個人的なAI利用（ChatGPTでの文章作成など）は**規制の対象外**です。あくまで事業者向けの規制となっています。

### 3. 施行は2027年4月の見込み

法案が可決された場合でも、企業の準備期間として**約1年間の猶予期間**が設けられる方針です[3]。

## 私たちへの影響は？

一般消費者にとっては、ネット上の広告や記事が「AIで作られたもの」かどうかが明確になるメリットがあります。一方、AI関連ビジネスを展開する企業にとっては、対応コストが課題になるという見方もあります。

## まとめ

- AI規制法案が国会で審議入り、事業者にAIラベル表示を義務化
- 個人利用は規制対象外、施行は2027年4月の見込み
- 消費者にとっては透明性向上のメリット、企業は対応準備が必要""",
            sources=[
                NewsSource(name="NHK", title="AI規制法案 国会に提出 生成AIの利用に新たなルール", url="https://www3.nhk.or.jp/news/example1"),
                NewsSource(name="日本経済新聞", title="AI規制法案の全容判明 企業にラベル表示義務", url="https://www.nikkei.com/example2"),
                NewsSource(name="朝日新聞", title="AI規制、日本も本格化 欧州に続き包括法案", url="https://www.asahi.com/example3"),
                NewsSource(name="Yahoo!ニュース", title="AI規制法案 知っておくべきポイントまとめ", url="https://news.yahoo.co.jp/example4"),
            ],
            tags=["AI", "法律", "テクノロジー"],
            reading_time_min=3,
            confidence=Confidence.HIGH,
        ),
    ),
    (
        "円安150円台",
        GeneratedArticle(
            title="円安が再び150円台に — 家計への影響と今後の見通しをサクッと解説",
            lede="為替市場で円安が加速し、1ドル=150円台に突入したことがSNSで話題です。「また円安？食品もまた値上がりするの？」と不安を感じている方も多いのではないでしょうか。背景と家計への影響を整理しました。",
            body_markdown="""## 何が起きた？ — 円安150円台の背景

4月16日の外国為替市場で、円相場が**1ドル=150円台後半**まで下落しました[1]。約3か月ぶりの円安水準です。

背景には、アメリカの**FRB（連邦準備制度理事会）が利下げに慎重な姿勢**を示していることがあります。日米の金利差が縮まらないため、より金利の高いドルが買われやすい状況が続いています[2]。

## 家計への影響 — 値上がりするもの・しないもの

### 値上がりが予想されるもの

- **輸入食品**（小麦、大豆、食用油など）
- **ガソリン・灯油**
- **海外旅行の費用**

### 影響が小さいもの

- **国産の野菜・米**（為替の影響は限定的）
- **電気・ガス料金**（政府の補助金で一定程度抑制中）

## 今後はどうなる？

市場関係者の間では、「年内に140円台に戻る可能性がある」という見方と、「155円まで円安が進む可能性もある」という見方が分かれています[3]。

日銀の追加利上げの有無が大きなカギを握っており、**7月の金融政策決定会合**が注目されています。

## まとめ

- 円安が1ドル=150円台に、日米金利差が主因
- 輸入食品やガソリンの値上がりに注意
- 今後は日銀の利上げ判断次第で展開が変わる可能性""",
            sources=[
                NewsSource(name="NHK", title="円相場 1ドル=150円台後半に 約3か月ぶりの円安水準", url="https://www3.nhk.or.jp/news/example5"),
                NewsSource(name="日本経済新聞", title="円安150円台 FRBの利下げ慎重姿勢が背景", url="https://www.nikkei.com/example6"),
                NewsSource(name="Bloomberg", title="ドル円150円台、日銀の次の一手に注目集まる", url="https://www.bloomberg.co.jp/example7"),
            ],
            tags=["経済", "為替", "家計"],
            reading_time_min=3,
            confidence=Confidence.HIGH,
        ),
    ),
    (
        "新型iPhone",
        GeneratedArticle(
            title="新型iPhone 17の全貌が判明？リーク情報5つのポイントまとめ",
            lede="Appleの次期スマートフォン「iPhone 17」に関するリーク情報が相次いでおり、SNSでトレンド入りしています。デザイン刷新やAI機能の強化など、気になる情報をまとめました。",
            body_markdown="""## リーク情報で見えてきた全貌

2026年秋に発表が見込まれる**iPhone 17シリーズ**について、複数の有力リーカーから情報が出ています[1]。例年通り9月の発表が有力視されています。

## 注目の5つのポイント

### 1. デザインが大幅刷新

背面のカメラ配置が横一列の**「バー型」デザイン**に変更されるとの情報が有力です。iPhone 4以来の大幅なデザイン変更となります[2]。

### 2. AI専用チップ搭載

**Apple Intelligence**（Appleの生成AI機能）をより高速に処理するための専用ニューラルエンジンが強化される見込みです。

### 3. 全モデルに120Hz対応ディスプレイ

これまで上位モデル限定だった**ProMotion（120Hzリフレッシュレート）**が、全モデルに搭載される可能性があります[3]。

### 4. 価格は据え置きか

円安の影響が懸念されていますが、Appleは**日本市場での価格を据え置く方針**との報道も出ています。

### 5. 発売は9月下旬か

例年通り、9月中旬に発表会、9月下旬に発売というスケジュールが予想されています。

## まとめ

- iPhone 17はデザイン刷新＋AI強化が目玉
- 全モデル120Hz対応で使い勝手が向上する可能性
- 正式発表は2026年9月の見込み、価格据え置きに期待""",
            sources=[
                NewsSource(name="MacRumors", title="iPhone 17 Design Leak: Horizontal Camera Bar Confirmed", url="https://www.macrumors.com/example8"),
                NewsSource(name="ITmedia", title="iPhone 17の噂まとめ：デザイン刷新とAI強化が柱", url="https://www.itmedia.co.jp/example9"),
                NewsSource(name="日経クロステック", title="Apple次期iPhone AI専用チップを大幅強化か", url="https://xtech.nikkei.com/example10"),
            ],
            tags=["テクノロジー", "Apple", "スマートフォン"],
            reading_time_min=3,
            confidence=Confidence.HIGH,
        ),
    ),
]


if __name__ == "__main__":
    print("=== デモ: サンプル記事で HTML サイトを生成 ===\n")

    records = publish(SAMPLE_ARTICLES, today=date(2026, 4, 16))

    print(f"\n{len(records)} 件の記事を生成しました:\n")
    for r in records:
        print(f"  [{', '.join(r.tags)}] {r.title}")
        print(f"    → site/{r.url}\n")

    print("生成されたファイル:")
    from pathlib import Path
    site = Path("site")
    for f in sorted(site.rglob("*")):
        if f.is_file():
            size = f.stat().st_size
            print(f"  {f.relative_to('.')}  ({size:,} bytes)")
