"""Hyperliquid取引所クライアント実装."""

from typing import Literal, Self

import ccxt.async_support as ccxt_async

from exchange_core.interface import IExchange, OHLCV, Order, Orderbook, Position, Ticker


class HyperliquidExchange(IExchange):
    """ccxt経由のHyperliquid取引所クライアント."""

    def __init__(self, exchange: ccxt_async.hyperliquid):
        self._exchange = exchange

    @classmethod
    async def create(cls, config: dict) -> Self:
        """
        ファクトリメソッド.

        Args:
            config: ccxt設定辞書
                - walletAddress: str - ウォレットアドレス
                - privateKey: str - 秘密鍵
        """
        exchange = ccxt_async.hyperliquid(config)
        await exchange.load_markets()
        return cls(exchange)

    async def get_orderbook(self, symbol: str) -> Orderbook:
        """
        指定シンボルのオーダーブックを取得.

        Args:
            symbol: ccxt形式のシンボル（例: "BTC/USDC:USDC"）
        """
        response = await self._exchange.fetch_order_book(symbol)
        return Orderbook(
            asks=[[float(ask[0]), float(ask[1])] for ask in response["asks"]],
            bids=[[float(bid[0]), float(bid[1])] for bid in response["bids"]],
        )

    async def get_ticker(self, symbol: str) -> Ticker:
        """
        指定シンボルの価格情報を取得.

        Args:
            symbol: ccxt形式のシンボル（例: "BTC/USDC:USDC"）
        """
        response = await self._exchange.fetch_ticker(symbol)
        return Ticker(
            symbol=symbol,
            last=float(response["last"]),
            bid=float(response["bid"]),
            ask=float(response["ask"]),
        )

    async def get_position(self, symbol: str) -> Position:
        """
        指定シンボルのポジション情報を取得.

        Args:
            symbol: ccxt形式のシンボル（例: "BTC/USDC:USDC"）
        """
        positions = await self._exchange.fetch_positions([symbol])

        # ポジションがない場合
        if not positions:
            return Position(
                symbol=symbol,
                side=None,
                size=0.0,
                entry_price=0.0,
                unrealized_pnl=0.0,
            )

        # 該当シンボルのポジションを探す
        for pos in positions:
            if pos["symbol"] == symbol:
                size = float(pos["contracts"] or 0)
                if size == 0:
                    return Position(
                        symbol=symbol,
                        side=None,
                        size=0.0,
                        entry_price=0.0,
                        unrealized_pnl=0.0,
                    )

                # ccxtの"long"/"short"を"Buy"/"Sell"に変換
                side: Literal["Buy", "Sell"] = "Buy" if pos["side"] == "long" else "Sell"
                return Position(
                    symbol=symbol,
                    side=side,
                    size=abs(size),
                    entry_price=float(pos["entryPrice"] or 0),
                    unrealized_pnl=float(pos["unrealizedPnl"] or 0),
                )

        # 見つからなかった場合
        return Position(
            symbol=symbol,
            side=None,
            size=0.0,
            entry_price=0.0,
            unrealized_pnl=0.0,
        )

    async def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Order:
        """
        指値注文を発注.

        Args:
            symbol: ccxt形式のシンボル
            side: "buy" or "sell"
            amount: 数量
            price: 価格
        """
        response = await self._exchange.create_order(
            symbol=symbol,
            type="limit",
            side=side,
            amount=amount,
            price=price,
        )
        return Order(
            id=str(response["id"]),
            symbol=symbol,
            side=side,
            amount=amount,
            price=price,
            # status=response.get("status", "open"),
        )

    async def place_market_order(self, symbol: str, side: str, amount: float) -> Order:
        """
        成行注文を発注.

        Args:
            symbol: ccxt形式のシンボル
            side: "buy" or "sell"
            amount: 数量
        """
        response = await self._exchange.create_order(
            symbol=symbol,
            type="market",
            side=side,
            amount=amount,
        )
        return Order(
            id=str(response["id"]),
            symbol=symbol,
            side=side,
            amount=amount,
            price=None,
            # status=response.get("status", "open"),
        )

    async def cancel_order(self, order_id: str, symbol: str) -> None:
        """
        注文をキャンセル.

        Args:
            order_id: 注文ID
            symbol: ccxt形式のシンボル
        """
        await self._exchange.cancel_order(order_id, symbol)

    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> list[OHLCV]:
        """
        OHLCVデータを取得.

        Args:
            symbol: ccxt形式のシンボル
            timeframe: ローソク足の時間枠（"1m", "5m", "1h"など）
            limit: 取得する本数
        """
        response = await self._exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        return [
            OHLCV(
                timestamp=int(candle[0]),
                open=float(candle[1]),
                high=float(candle[2]),
                low=float(candle[3]),
                close=float(candle[4]),
                volume=float(candle[5]),
            )
            for candle in response
        ]

    async def get_open_orders(self, symbol: str) -> list[Order]:
        """
        未約定の注文一覧を取得.

        Args:
            symbol: ccxt形式のシンボル
        """
        response = await self._exchange.fetch_open_orders(symbol)
        return [
            Order(
                id=str(order["id"]),
                symbol=order["symbol"],
                side=order["side"],
                amount=float(order["amount"]),
                price=float(order["price"]) if order["price"] else None,
                # status=order.get("status", "open"),
            )
            for order in response
        ]

    async def close(self) -> None:
        """クライアントのリソースをクリーンアップ."""
        await self._exchange.close()
