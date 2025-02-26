"""
账户数据库模型
"""

from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from ..database_manager import Base


class AccountModel(Base):
    """账户数据库模型"""

    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True)
    exchange_id = Column(String(50), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 关联关系
    balances = relationship(
        "BalanceModel", back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Account(id='{self.id}', exchange_id='{self.exchange_id}')>"


class BalanceModel(Base):
    """余额数据库模型"""

    __tablename__ = "balances"

    id = Column(String(36), primary_key=True)
    account_id = Column(
        String(36), ForeignKey("accounts.id"), nullable=False, index=True
    )
    currency = Column(String(20), nullable=False, index=True)
    free = Column(Float, nullable=False, default=0.0)
    used = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    account = relationship("AccountModel", back_populates="balances")

    def __repr__(self) -> str:
        return (
            f"<Balance(id='{self.id}', "
            f"account_id='{self.account_id}', "
            f"currency='{self.currency}', "
            f"free={self.free}, "
            f"used={self.used}, "
            f"total={self.total})>"
        )
