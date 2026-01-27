"""取引所の抽象インターフェース定義."""

from abc import ABC, abstractmethod
from typing import Literal, Self

from pydantic import BaseModel


class Ticker(BaseModel):
    """価格情報."""

    symbol: str
    last: float  # 最終価格
    bid: float  # 最良買い気配
    ask: float  # 最良売り気配


class Position(BaseModel):
    """ポジション情報."""

    symbol: str
    side: Literal["Buy", "Sell"] | None  # ポジションなしの場合はNone
    size: float  # ポジションサイズ（絶対値）
    entry_price: float  # 平均取得価格
    unrealized_pnl: float  # 未実現損益


class Order(BaseModel):
    """注文情報."""

    id: str
    symbol: str
    side: str  # "buy" | "sell"
    amount: float
    price: float | None  # マーケット注文の場合はNone
    # status: str  # "open" | "closed" | "canceled"


class OHLCV(BaseModel):
    """OHLCVデータ."""

    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class Orderbook(BaseModel):
    """オーダーブックデータ."""

    asks: list[list[float]]  # [[price, amount], ...]
    bids: list[list[float]]  # [[price, amount], ...]

    @property
    def best_ask(self) -> float:
        return self.asks[0][0]

    @property
    def best_bid(self) -> float:
        return self.bids[0][0]


class IExchange(ABC):
    """取引所クライアントの抽象インターフェース."""

    @classmethod
    @abstractmethod
    async def create(cls, config: dict) -> Self:
        """ファクトリメソッド: 非同期初期化が必要なクライアントを作成."""
        pass

    @abstractmethod
    async def get_orderbook(self, symbol: str) -> Orderbook:
        """指定シンボルのオーダーブックを取得."""
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker:
        """指定シンボルの価格情報を取得."""
        pass

    @abstractmethod
    async def get_position(self, symbol: str) -> Position:
        """指定シンボルのポジション情報を取得."""
        pass

    @abstractmethod
    async def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Order:
        """指値注文を発注."""
        pass

    @abstractmethod
    async def place_market_order(self, symbol: str, side: str, amount: float) -> Order:
        """成行注文を発注."""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> None:
        """注文をキャンセル."""
        pass

    @abstractmethod
    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> list[OHLCV]:
        """OHLCVデータを取得."""
        pass

    @abstractmethod
    async def get_open_orders(self, symbol: str) -> list[Order]:
        """未約定の注文一覧を取得."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """クライアントのリソースをクリーンアップ."""
        pass
