"""
市场数据仓库接口
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional

from ..models.market_data import Ticker, Candle, OrderBook


class MarketDataRepository(ABC):
    """市场数据仓库接口"""
    
    @abstractmethod
    def get_ticker(self, symbol: str, exchange_id: str) -> Optional[Ticker]:
        """
        获取最新行情
        
        Args:
            symbol: 交易对，如 "BTC/USDT"
            exchange_id: 交易所ID
            
        Returns:
            行情对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_tickers(self, exchange_id: str) -> Dict[str, Ticker]:
        """
        获取交易所的所有行情
        
        Args:
            exchange_id: 交易所ID
            
        Returns:
            行情字典，键为交易对，值为行情对象
        """
        pass
    
    @abstractmethod
    def save_ticker(self, ticker: Ticker) -> None:
        """
        保存行情
        
        Args:
            ticker: 行情对象
        """
        pass
    
    @abstractmethod
    def get_candles(
        self,
        symbol: str,
        exchange_id: str,
        timeframe: str,
        since: Optional[datetime] = None,
        limit: int = 100
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
        pass
    
    @abstractmethod
    def save_candles(self, candles: List[Candle]) -> None:
        """
        保存K线数据
        
        Args:
            candles: K线列表
        """
        pass
    
    @abstractmethod
    def get_order_book(
        self,
        symbol: str,
        exchange_id: str,
        limit: int = 20
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
        pass
    
    @abstractmethod
    def save_order_book(self, order_book: OrderBook) -> None:
        """
        保存订单簿
        
        Args:
            order_book: 订单簿对象
        """
        pass 