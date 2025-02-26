"""
市场数据数据库模型
"""

from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import JSONB

from ..database_manager import Base


class TickerModel(Base):
    """行情数据库模型"""
    
    __tablename__ = "tickers"
    
    id = Column(String(36), primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    exchange_id = Column(String(50), nullable=False, index=True)
    bid = Column(Float, nullable=False)
    ask = Column(Float, nullable=False)
    last = Column(Float, nullable=False)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    quote_volume = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 创建复合索引
    __table_args__ = (
        Index('ix_tickers_symbol_exchange_timestamp', 'symbol', 'exchange_id', 'timestamp'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<Ticker(id='{self.id}', "
            f"symbol='{self.symbol}', "
            f"exchange_id='{self.exchange_id}', "
            f"last={self.last}, "
            f"timestamp='{self.timestamp}')>"
        )


class CandleModel(Base):
    """K线数据库模型"""
    
    __tablename__ = "candles"
    
    id = Column(String(36), primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    exchange_id = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    quote_volume = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 创建复合索引
    __table_args__ = (
        Index('ix_candles_symbol_exchange_timeframe_timestamp', 'symbol', 'exchange_id', 'timeframe', 'timestamp'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<Candle(id='{self.id}', "
            f"symbol='{self.symbol}', "
            f"exchange_id='{self.exchange_id}', "
            f"timeframe='{self.timeframe}', "
            f"timestamp='{self.timestamp}')>"
        )


class OrderBookModel(Base):
    """订单簿数据库模型"""
    
    __tablename__ = "order_books"
    
    id = Column(String(36), primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    exchange_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    bids = Column(Text, nullable=False)  # JSON格式的买单列表
    asks = Column(Text, nullable=False)  # JSON格式的卖单列表
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 创建复合索引
    __table_args__ = (
        Index('ix_order_books_symbol_exchange_timestamp', 'symbol', 'exchange_id', 'timestamp'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<OrderBook(id='{self.id}', "
            f"symbol='{self.symbol}', "
            f"exchange_id='{self.exchange_id}', "
            f"timestamp='{self.timestamp}')>"
        ) 