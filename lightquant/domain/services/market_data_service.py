"""
市场数据服务，处理市场数据相关的领域逻辑
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.market_data import Candle, OrderBook, Ticker
from ..repositories.market_data_repository import MarketDataRepository


class MarketDataService:
    """市场数据服务，处理市场数据相关的领域逻辑"""

    def __init__(self, market_data_repository: MarketDataRepository):
        self._market_data_repository = market_data_repository

    def get_ticker(self, symbol: str, exchange_id: str) -> Optional[Ticker]:
        """
        获取最新行情

        Args:
            symbol: 交易对，如 "BTC/USDT"
            exchange_id: 交易所ID

        Returns:
            行情对象，如果不存在则返回None
        """
        return self._market_data_repository.get_ticker(symbol, exchange_id)

    def get_tickers(self, exchange_id: str) -> Dict[str, Ticker]:
        """
        获取交易所的所有行情

        Args:
            exchange_id: 交易所ID

        Returns:
            行情字典，键为交易对，值为行情对象
        """
        return self._market_data_repository.get_tickers(exchange_id)

    def get_candles(
        self,
        symbol: str,
        exchange_id: str,
        timeframe: str,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Candle]:
        """
        获取K线数据

        Args:
            symbol: 交易对，如 "BTC/USDT"
            exchange_id: 交易所ID
            timeframe: 时间周期，如 "1m", "5m", "1h", "1d"
            since: 开始时间，如果为None则获取最新的K线
            limit: 获取的K线数量

        Returns:
            K线列表
        """
        return self._market_data_repository.get_candles(
            symbol, exchange_id, timeframe, since, limit
        )

    def get_order_book(
        self, symbol: str, exchange_id: str, limit: int = 20
    ) -> Optional[OrderBook]:
        """
        获取订单簿

        Args:
            symbol: 交易对，如 "BTC/USDT"
            exchange_id: 交易所ID
            limit: 获取的深度级别

        Returns:
            订单簿对象，如果不存在则返回None
        """
        return self._market_data_repository.get_order_book(symbol, exchange_id, limit)

    def calculate_vwap(
        self, symbol: str, exchange_id: str, timeframe: str, periods: int = 20
    ) -> Optional[float]:
        """
        计算成交量加权平均价格(VWAP)

        Args:
            symbol: 交易对，如 "BTC/USDT"
            exchange_id: 交易所ID
            timeframe: 时间周期，如 "1m", "5m", "1h", "1d"
            periods: 计算周期数

        Returns:
            VWAP值，如果数据不足则返回None
        """
        candles = self.get_candles(symbol, exchange_id, timeframe, limit=periods)

        if len(candles) < periods:
            return None

        total_volume = 0
        total_volume_price = 0

        for candle in candles:
            volume = candle.volume
            typical_price = (candle.high + candle.low + candle.close) / 3

            total_volume += volume
            total_volume_price += volume * typical_price

        if total_volume == 0:
            return None

        return total_volume_price / total_volume

    def calculate_moving_average(
        self,
        symbol: str,
        exchange_id: str,
        timeframe: str,
        periods: int = 20,
        price_type: str = "close",
    ) -> Optional[float]:
        """
        计算移动平均线

        Args:
            symbol: 交易对，如 "BTC/USDT"
            exchange_id: 交易所ID
            timeframe: 时间周期，如 "1m", "5m", "1h", "1d"
            periods: 计算周期数
            price_type: 价格类型，可选 "open", "high", "low", "close"

        Returns:
            移动平均线值，如果数据不足则返回None
        """
        candles = self.get_candles(symbol, exchange_id, timeframe, limit=periods)

        if len(candles) < periods:
            return None

        prices = []
        for candle in candles:
            if price_type == "open":
                prices.append(candle.open)
            elif price_type == "high":
                prices.append(candle.high)
            elif price_type == "low":
                prices.append(candle.low)
            else:  # default to close
                prices.append(candle.close)

        return sum(prices) / len(prices)

    def calculate_bollinger_bands(
        self,
        symbol: str,
        exchange_id: str,
        timeframe: str,
        periods: int = 20,
        deviation: float = 2.0,
        price_type: str = "close",
    ) -> Optional[Dict[str, float]]:
        """
        计算布林带

        Args:
            symbol: 交易对，如 "BTC/USDT"
            exchange_id: 交易所ID
            timeframe: 时间周期，如 "1m", "5m", "1h", "1d"
            periods: 计算周期数
            deviation: 标准差倍数
            price_type: 价格类型，可选 "open", "high", "low", "close"

        Returns:
            布林带值，包含中轨、上轨和下轨，如果数据不足则返回None
        """
        candles = self.get_candles(symbol, exchange_id, timeframe, limit=periods)

        if len(candles) < periods:
            return None

        prices = []
        for candle in candles:
            if price_type == "open":
                prices.append(candle.open)
            elif price_type == "high":
                prices.append(candle.high)
            elif price_type == "low":
                prices.append(candle.low)
            else:  # default to close
                prices.append(candle.close)

        # 计算中轨（简单移动平均线）
        middle = sum(prices) / len(prices)

        # 计算标准差
        variance = sum((price - middle) ** 2 for price in prices) / len(prices)
        std_dev = variance**0.5

        # 计算上轨和下轨
        upper = middle + deviation * std_dev
        lower = middle - deviation * std_dev

        return {
            "middle": middle,
            "upper": upper,
            "lower": lower,
        }
