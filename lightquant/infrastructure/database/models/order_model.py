"""
订单数据库模型
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from ..database_manager import Base


class OrderTypeEnum(enum.Enum):
    """订单类型枚举"""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderStatusEnum(enum.Enum):
    """订单状态枚举"""

    CREATED = "created"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderSideEnum(enum.Enum):
    """订单方向枚举"""

    BUY = "buy"
    SELL = "sell"


class OrderModel(Base):
    """订单数据库模型"""

    __tablename__ = "orders"

    id = Column(String(36), primary_key=True)
    strategy_id = Column(String(36), nullable=False, index=True)
    exchange_id = Column(String(50), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    order_type = Column(Enum(OrderTypeEnum), nullable=False)
    side = Column(Enum(OrderSideEnum), nullable=False)
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    filled_amount = Column(Float, default=0.0)
    average_price = Column(Float, nullable=True)
    status = Column(
        Enum(OrderStatusEnum),
        nullable=False,
        default=OrderStatusEnum.CREATED,
        index=True,
    )
    exchange_order_id = Column(String(100), nullable=True, index=True)
    client_order_id = Column(String(100), nullable=True, index=True)
    params = Column(Text, nullable=True)  # JSON格式的额外参数
    error_message = Column(Text, nullable=True)
    is_closed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # 关联关系
    trades = relationship(
        "TradeModel", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Order(id='{self.id}', "
            f"symbol='{self.symbol}', "
            f"type='{self.order_type.value}', "
            f"side='{self.side.value}', "
            f"status='{self.status.value}')>"
        )
