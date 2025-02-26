"""
策略数据库模型
"""

import enum
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Enum, Text, Table, ForeignKey
from sqlalchemy.orm import relationship

from ..database_manager import Base


class StrategyStatusEnum(enum.Enum):
    """策略状态枚举"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


# 策略与订单的多对多关系表
strategy_orders = Table(
    'strategy_orders',
    Base.metadata,
    Column('strategy_id', String(36), ForeignKey('strategies.id'), primary_key=True),
    Column('order_id', String(36), ForeignKey('orders.id'), primary_key=True)
)


class StrategyModel(Base):
    """策略数据库模型"""
    
    __tablename__ = "strategies"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    status = Column(Enum(StrategyStatusEnum), nullable=False, default=StrategyStatusEnum.CREATED, index=True)
    config = Column(Text, nullable=False)  # JSON格式的策略配置
    symbols = Column(Text, nullable=False)  # JSON格式的交易对列表
    exchange_ids = Column(Text, nullable=False)  # JSON格式的交易所ID列表
    timeframes = Column(Text, nullable=False)  # JSON格式的时间周期列表
    performance_metrics = Column(Text, nullable=True)  # JSON格式的性能指标
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    start_time = Column(DateTime, nullable=True)
    stop_time = Column(DateTime, nullable=True)
    last_run_time = Column(DateTime, nullable=True)
    
    # 关联关系
    orders = relationship("OrderModel", secondary=strategy_orders, backref="strategies")
    
    def __repr__(self) -> str:
        return (
            f"<Strategy(id='{self.id}', "
            f"name='{self.name}', "
            f"status='{self.status.value}')>"
        ) 