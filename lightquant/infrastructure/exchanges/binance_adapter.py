"""
Binance交易所适配器
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import ccxt
import ccxt.async_support as ccxt_async

from ...domain.models.account import Balance
from ...domain.models.market_data import Candle, OrderBook, OrderBookEntry, Ticker
from ...domain.models.order import Order, OrderSide, OrderStatus, OrderType
from .exchange_adapter import ExchangeAdapter


class BinanceAdapter(ExchangeAdapter):
    """
    币安交易所适配器

    基于CCXT库实现
    """

    def __init__(self, api_key: str = "", api_secret: str = "", passphrase: str = ""):
        super().__init__(api_key, api_secret, passphrase)
        self._exchange = ccxt_async.binance(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "options": {
                    "defaultType": "spot",  # 默认为现货交易
                },
            }
        )

    def _get_exchange_id(self) -> str:
        """获取交易所ID"""
        return "binance"

    async def fetch_ticker(self, symbol: str) -> Optional[Ticker]:
        """获取最新行情"""
        try:
            ticker_data = await self._exchange.fetch_ticker(symbol)
            return self._convert_to_ticker(ticker_data)
        except Exception as e:
            print(f"获取{symbol}行情失败: {e}")
            return None

    async def fetch_tickers(
        self, symbols: Optional[List[str]] = None
    ) -> Dict[str, Ticker]:
        """获取多个交易对的行情"""
        result = {}
        try:
            tickers_data = await self._exchange.fetch_tickers(symbols)
            for symbol, ticker_data in tickers_data.items():
                result[symbol] = self._convert_to_ticker(ticker_data)
            return result
        except Exception as e:
            print(f"获取行情列表失败: {e}")
            return result

    async def fetch_order_book(
        self, symbol: str, limit: int = 20
    ) -> Optional[OrderBook]:
        """获取订单簿"""
        try:
            order_book_data = await self._exchange.fetch_order_book(symbol, limit)
            return self._convert_to_order_book(order_book_data, symbol)
        except Exception as e:
            print(f"获取{symbol}订单簿失败: {e}")
            return None

    async def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Candle]:
        """获取K线数据"""
        result = []
        try:
            since_timestamp = int(since.timestamp() * 1000) if since else None
            candles_data = await self._exchange.fetch_ohlcv(
                symbol, timeframe, since_timestamp, limit
            )
            for candle_data in candles_data:
                result.append(self._convert_to_candle(candle_data, symbol, timeframe))
            return result
        except Exception as e:
            print(f"获取{symbol} {timeframe}K线失败: {e}")
            return result

    async def fetch_balance(self) -> Dict[str, Balance]:
        """获取账户余额"""
        result = {}
        try:
            balance_data = await self._exchange.fetch_balance()
            for currency, data in balance_data["total"].items():
                if data > 0:
                    result[currency] = Balance(
                        currency=currency,
                        free=balance_data["free"].get(currency, 0),
                        used=balance_data["used"].get(currency, 0),
                        total=data,
                    )
            return result
        except Exception as e:
            print(f"获取账户余额失败: {e}")
            return result

    async def create_order(
        self, order: Order
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """创建订单"""
        try:
            order_type = self.map_order_type(order.type)
            side = self.map_order_side(order.side)

            params = {}
            if order.client_order_id:
                params["clientOrderId"] = order.client_order_id

            # 创建订单
            response = await self._exchange.create_order(
                symbol=order.symbol,
                type=order_type,
                side=side,
                amount=order.amount,
                price=order.price if order.price else None,
                params=params,
            )

            return True, response["id"], None
        except Exception as e:
            error_msg = str(e)
            print(f"创建订单失败: {error_msg}")
            return False, None, error_msg

    async def cancel_order(self, order: Order) -> Tuple[bool, Optional[str]]:
        """取消订单"""
        try:
            if not order.exchange_order_id:
                return False, "缺少交易所订单ID"

            await self._exchange.cancel_order(order.exchange_order_id, order.symbol)
            return True, None
        except Exception as e:
            error_msg = str(e)
            print(f"取消订单失败: {error_msg}")
            return False, error_msg

    async def fetch_order(
        self, order: Order
    ) -> Tuple[
        bool, Optional[OrderStatus], Optional[float], Optional[float], Optional[str]
    ]:
        """获取订单状态"""
        try:
            if not order.exchange_order_id:
                return False, None, None, None, "缺少交易所订单ID"

            # 获取订单信息
            order_data = await self._exchange.fetch_order(
                order.exchange_order_id, order.symbol
            )

            # 转换订单状态
            status = self.map_order_status(order_data["status"])

            # 获取已成交数量和平均成交价格
            filled = order_data["filled"]
            avg_price = order_data["price"]
            if filled > 0 and "average" in order_data and order_data["average"]:
                avg_price = order_data["average"]

            return True, status, filled, avg_price, None
        except Exception as e:
            error_msg = str(e)
            print(f"获取订单状态失败: {error_msg}")
            return False, None, None, None, error_msg

    async def fetch_open_orders(
        self, symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取未完成订单"""
        try:
            orders_data = await self._exchange.fetch_open_orders(symbol)
            return orders_data
        except Exception as e:
            print(f"获取未完成订单失败: {e}")
            return []

    async def fetch_closed_orders(
        self,
        symbol: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取已完成订单"""
        try:
            since_timestamp = int(since.timestamp() * 1000) if since else None
            orders_data = await self._exchange.fetch_closed_orders(
                symbol, since_timestamp, limit
            )
            return orders_data
        except Exception as e:
            print(f"获取已完成订单失败: {e}")
            return []

    def map_order_type(self, order_type: OrderType) -> str:
        """映射订单类型"""
        mapping = {
            OrderType.MARKET: "market",
            OrderType.LIMIT: "limit",
            OrderType.STOP_LOSS: "stop_loss",
            OrderType.STOP_LOSS_LIMIT: "stop_loss_limit",
            OrderType.TAKE_PROFIT: "take_profit",
            OrderType.TAKE_PROFIT_LIMIT: "take_profit_limit",
        }
        return mapping.get(order_type, "limit")

    def map_order_side(self, order_side: OrderSide) -> str:
        """映射订单方向"""
        mapping = {
            OrderSide.BUY: "buy",
            OrderSide.SELL: "sell",
        }
        return mapping.get(order_side, "buy")

    def map_order_status(self, status: str) -> OrderStatus:
        """映射订单状态"""
        mapping = {
            "open": OrderStatus.OPEN,
            "closed": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELED,
            "expired": OrderStatus.EXPIRED,
            "rejected": OrderStatus.REJECTED,
        }
        return mapping.get(status, OrderStatus.UNKNOWN)

    def _convert_to_ticker(self, ticker_data: Dict[str, Any]) -> Ticker:
        """将CCXT行情数据转换为Ticker对象"""
        return Ticker(
            symbol=ticker_data["symbol"],
            timestamp=datetime.fromtimestamp(ticker_data["timestamp"] / 1000),
            bid=ticker_data["bid"],
            ask=ticker_data["ask"],
            last=ticker_data["last"],
            volume=ticker_data["volume"],
            exchange=self.exchange_id,
        )

    def _convert_to_order_book(
        self, order_book_data: Dict[str, Any], symbol: str
    ) -> OrderBook:
        """将CCXT订单簿数据转换为OrderBook对象"""
        bids = [
            OrderBookEntry(price=price, amount=amount)
            for price, amount in order_book_data["bids"]
        ]
        asks = [
            OrderBookEntry(price=price, amount=amount)
            for price, amount in order_book_data["asks"]
        ]

        return OrderBook(
            symbol=symbol,
            timestamp=(
                datetime.fromtimestamp(order_book_data["timestamp"] / 1000)
                if order_book_data.get("timestamp")
                else datetime.now()
            ),
            bids=bids,
            asks=asks,
            exchange=self.exchange_id,
        )

    def _convert_to_candle(
        self, candle_data: List[Any], symbol: str, timeframe: str
    ) -> Candle:
        """将CCXT K线数据转换为Candle对象"""
        timestamp, open_price, high, low, close, volume = candle_data

        return Candle(
            symbol=symbol,
            timestamp=datetime.fromtimestamp(timestamp / 1000),
            timeframe=timeframe,
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=volume,
            exchange=self.exchange_id,
        )
