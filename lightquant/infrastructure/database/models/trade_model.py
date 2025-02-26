"""
交易数据库模型
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import relationship

from ..database_manager import Base


class TradeModel(Base):
    """交易数据库模型"""

    __tablename__ = "trades"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    trade_id = Column(String(100), nullable=False, index=True)  # 交易所返回的成交ID
    exchange_id = Column(String(50), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(
        String(10), nullable=False
    )  # 使用字符串而不是枚举，因为这里直接存储OrderSideEnum的值
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)  # 成交金额 = 数量 * 价格
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    order = relationship("OrderModel", back_populates="trades")

    def __repr__(self) -> str:
        return (
            f"<Trade(id='{self.id}', "
            f"order_id='{self.order_id}', "
            f"symbol='{self.symbol}', "
            f"side='{self.side}', "
            f"amount={self.amount}, "
            f"price={self.price})>"
        )
