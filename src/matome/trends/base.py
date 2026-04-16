"""トレンドソースの基底プロトコル"""

from __future__ import annotations

from typing import Protocol

from matome.models import TrendItem


class TrendSourceProtocol(Protocol):
    """トレンド取得ソースのインターフェース"""

    def fetch(self) -> list[TrendItem]:
        """トレンドキーワードを取得して返す"""
        ...
