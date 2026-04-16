"""CLI エントリポイント — python -m matome.cli で実行"""

from __future__ import annotations

import argparse
import logging
import sys

from dotenv import load_dotenv


def _setup_logging(verbose: bool = False) -> None:
    """ログ設定"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main(argv: list[str] | None = None) -> int:
    """メインエントリポイント"""
    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="matome",
        description="SNS トレンド自動まとめサイトジェネレーター",
    )
    subparsers = parser.add_subparsers(dest="command")

    # run コマンド
    run_parser = subparsers.add_parser("run", help="まとめ記事を生成")
    run_parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="生成する最大記事数 (default: 5)",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Claude API を呼ばずトレンド収集・リサーチまでで停止",
    )
    run_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="デバッグログを表示",
    )

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    _setup_logging(args.verbose)

    if args.command == "run":
        from matome.pipeline import run_pipeline

        try:
            records = run_pipeline(limit=args.limit, dry_run=args.dry_run)
            if records:
                print(f"\n{len(records)} 件の記事を生成しました:")
                for r in records:
                    print(f"  - {r.title} ({r.url})")
            elif args.dry_run:
                print("\ndry-run モードで完了しました（記事は生成されていません）")
            else:
                print("\n記事を生成できませんでした。ログを確認してください。")
                return 1
        except ValueError as e:
            print(f"\nエラー: {e}", file=sys.stderr)
            return 1
        except Exception:
            logging.exception("予期しないエラーが発生しました")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
