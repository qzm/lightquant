"""
市场数据模型，包括行情、K线和订单簿
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from .base import ValueObject


@dataclass
class Ticker(ValueObject):
    """行情数据值对象"""
    symbol: str  # 交易对，如 "BTC/USDT"
    bid: float  # 买一价
    ask: float  # 卖一价
    last: float  # 最新成交价
    high: float  # 24小时最高价
    low: float  # 24小时最低价
    volume: float  # 24小时成交量
    quote_volume: float  # 24小时成交额
    timestamp: datetime  # 时间戳
    exchange_id: str  # 交易所ID
    
    @property
    def mid_price(self) -> float:
        """中间价"""
        return (self.bid + self.ask) / 2
    
    @property
    def spread(self) -> float:
        """价差"""
        return self.ask - self.bid
    
    @property
    def spread_percentage(self) -> float:
        """价差百分比"""
        return (self.ask - self.bid) / self.bid * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """将行情转换为字典"""
        return {
            "symbol": self.symbol,
            "exchange_id": self.exchange_id,
            "bid": self.bid,
            "ask": self.ask,
            "last": self.last,
            "high": self.high,
            "low": self.low,
            "volume": self.volume,
            "quote_volume": self.quote_volume,
            "mid_price": self.mid_price,
            "spread": self.spread,
            "spread_percentage": self.spread_percentage,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Candle(ValueObject):
    """K线数据值对象"""
    symbol: str  # 交易对，如 "BTC/USDT"
    timestamp: datetime  # 开盘时间
    open: float  # 开盘价
    high: float  # 最高价
    low: float  # 最低价
    close: float  # 收盘价
    volume: float  # 成交量
    quote_volume: Optional[float] = None  # 成交额
    exchange_id: str = ""  # 交易所ID
    timeframe: str = "1m"  # 时间周期，如 "1m", "5m", "1h", "1d"
    
    @property
    def is_bullish(self) -> bool:
        """是否是上涨K线"""
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        """是否是下跌K线"""
        return self.close < self.open
    
    @property
    def is_doji(self) -> bool:
        """是否是十字星"""
        return abs(self.close - self.open) / self.open < 0.0001
    
    @property
    def range(self) -> float:
        """价格范围"""
        return self.high - self.low
    
    @property
    def body(self) -> float:
        """实体长度"""
        return abs(self.close - self.open)
    
    @property
    def upper_shadow(self) -> float:
        """上影线长度"""
        return self.high - max(self.open, self.close)
    
    @property
    def lower_shadow(self) -> float:
        """下影线长度"""
        return min(self.open, self.close) - self.low
    
    def to_dict(self) -> Dict[str, Any]:
        """将K线转换为字典"""
        return {
            "symbol": self.symbol,
            "exchange_id": self.exchange_id,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "quote_volume": self.quote_volume,
        }


@dataclass
class OrderBookEntry(ValueObject):
    """订单簿条目值对象"""
    price: float  # 价格
    amount: float  # 数量
    
    def to_dict(self) -> Dict[str, float]:
        """将订单簿条目转换为字典"""
        return {
            "price": self.price,
            "amount": self.amount,
        }


@dataclass
class OrderBook(ValueObject):
    """订单簿值对象"""
    symbol: str  # 交易对，如 "BTC/USDT"
    bids: List[OrderBookEntry] = field(default_factory=list)  # 买单列表
    asks: List[OrderBookEntry] = field(default_factory=list)  # 卖单列表
    timestamp: datetime = field(default_factory=datetime.utcnow)  # 时间戳
    exchange_id: str = ""  # 交易所ID
    
    @property
    def best_bid(self) -> Optional[OrderBookEntry]:
        """最优买价"""
        return self.bids[0] if self.bids else None
    
    @property
    def best_ask(self) -> Optional[OrderBookEntry]:
        """最优卖价"""
        return self.asks[0] if self.asks else None
    
    @property
    def mid_price(self) -> Optional[float]:
        """中间价"""
        if not self.best_bid or not self.best_ask:
            return None
        return (self.best_bid.price + self.best_ask.price) / 2
    
    @property
    def spread(self) -> Optional[float]:
        """价差"""
        if not self.best_bid or not self.best_ask:
            return None
        return self.best_ask.price - self.best_bid.price
    
    @property
    def spread_percentage(self) -> Optional[float]:
        """价差百分比"""
        if not self.best_bid or not self.best_ask:
            return None
        return (self.best_ask.price - self.best_bid.price) / self.best_bid.price * 100
    
    def get_price_at_volume(self, volume: float, side: str) -> Optional[float]:
        """获取指定成交量对应的价格"""
        if side.lower() not in ["buy", "sell"]:
            raise ValueError("Side must be 'buy' or 'sell'")
        
        entries = self.asks if side.lower() == "buy" else self.bids
        cumulative_volume = 0.0
        weighted_price = 0.0
        
        for entry in entries:
            available_volume = min(entry.amount, volume - cumulative_volume)
            weighted_price += entry.price * available_volume
            cumulative_volume += available_volume
            
            if cumulative_volume >= volume:
                return weighted_price / volume
        
        return None  # 订单簿深度不足
    
    def to_dict(self) -> Dict[str, Any]:
        """将订单簿转换为字典"""
        return {
            "symbol": self.symbol,
            "exchange_id": self.exchange_id,
            "bids": [bid.to_dict() for bid in self.bids],
            "asks": [ask.to_dict() for ask in self.asks],
            "timestamp": self.timestamp.isoformat(),
        } 