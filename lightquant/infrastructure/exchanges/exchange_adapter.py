"""
交易所适配器基类
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ...domain.models.account import Balance
from ...domain.models.market_data import Candle, OrderBook, OrderBookEntry, Ticker
from ...domain.models.order import Order, OrderParams, OrderSide, OrderStatus, OrderType


class ExchangeAdapter(ABC):
    """
    交易所适配器基类

    负责与交易所API交互，提供统一的接口
    """

    def __init__(self, api_key: str = "", api_secret: str = "", passphrase: str = ""):
        self._api_key = api_key
        self._api_secret = api_secret
        self._passphrase = passphrase
        self._exchange_id = self._get_exchange_id()

    @property
    def exchange_id(self) -> str:
        """获取交易所ID"""
        return self._exchange_id

    @abstractmethod
    def _get_exchange_id(self) -> str:
        """获取交易所ID"""
        pass

    @abstractmethod
    async def fetch_ticker(self, symbol: str) -> Optional[Ticker]:
        """
        获取最新行情

        Args:
            symbol: 交易对，如 "BTC/USDT"

        Returns:
            行情对象，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def fetch_tickers(
        self, symbols: Optional[List[str]] = None
    ) -> Dict[str, Ticker]:
        """
        获取多个交易对的行情

        Args:
            symbols: 交易对列表，如果为None则获取所有交易对

        Returns:
            行情字典，键为交易对，值为行情对象
        """
        pass

    @abstractmethod
    async def fetch_order_book(
        self, symbol: str, limit: int = 20
    ) -> Optional[OrderBook]:
        """
        获取订单簿

        Args:
            symbol: 交易对，如 "BTC/USDT"
            limit: 获取的深度级别

        Returns:
            订单簿对象，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Candle]:
        """
        获取K线数据

        Args:
            symbol: 交易对，如 "BTC/USDT"
            timeframe: 时间周期，如 "1m", "5m", "1h", "1d"
            since: 开始时间，如果为None则获取最新的K线
            limit: 获取的K线数量

        Returns:
            K线列表
        """
        pass

    @abstractmethod
    async def fetch_balance(self) -> Dict[str, Balance]:
        """
        获取账户余额

        Returns:
            余额字典，键为货币，值为余额对象
        """
        pass

    @abstractmethod
    async def create_order(
        self, order: Order
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        创建订单

        Args:
            order: 订单对象

        Returns:
            (是否成功, 交易所订单ID, 错误信息)
        """
        pass

    @abstractmethod
    async def cancel_order(self, order: Order) -> Tuple[bool, Optional[str]]:
        """
        取消订单

        Args:
            order: 订单对象

        Returns:
            (是否成功, 错误信息)
        """
        pass

    @abstractmethod
    async def fetch_order(
        self, order: Order
    ) -> Tuple[
        bool, Optional[OrderStatus], Optional[float], Optional[float], Optional[str]
    ]:
        """
        获取订单状态

        Args:
            order: 订单对象

        Returns:
            (是否成功, 订单状态, 已成交数量, 平均成交价格, 错误信息)
        """
        pass

    @abstractmethod
    async def fetch_open_orders(
        self, symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取未完成订单

        Args:
            symbol: 交易对，如果为None则获取所有交易对的未完成订单

        Returns:
            未完成订单列表
        """
        pass

    @abstractmethod
    async def fetch_closed_orders(
        self,
        symbol: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取已完成订单

        Args:
            symbol: 交易对，如果为None则获取所有交易对的已完成订单
            since: 开始时间，如果为None则获取最新的已完成订单
            limit: 获取的订单数量

        Returns:
            已完成订单列表
        """
        pass

    @abstractmethod
    def map_order_type(self, order_type: OrderType) -> str:
        """
        映射订单类型

        Args:
            order_type: 订单类型

        Returns:
            交易所的订单类型
        """
        pass

    @abstractmethod
    def map_order_side(self, order_side: OrderSide) -> str:
        """
        映射订单方向

        Args:
            order_side: 订单方向

        Returns:
            交易所的订单方向
        """
        pass

    @abstractmethod
    def map_order_status(self, status: str) -> OrderStatus:
        """
        映射订单状态

        Args:
            status: 交易所的订单状态

        Returns:
            订单状态
        """
        pass
