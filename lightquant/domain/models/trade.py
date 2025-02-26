"""
交易模型，表示订单的成交记录
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

from .base import Entity
from .order import OrderSide


class Trade(Entity):
    """交易实体，表示订单的成交记录"""

    def __init__(
        self,
        order_id: str,
        trade_id: str,
        amount: float,
        price: float,
        side: OrderSide,
        symbol: str,
        exchange_id: str,
        entity_id: str = None,
    ):
        super().__init__(entity_id)
        self._order_id = order_id
        self._trade_id = trade_id  # 交易所返回的成交ID
        self._amount = amount
        self._price = price
        self._side = side
        self._symbol = symbol
        self._exchange_id = exchange_id
        self._timestamp = datetime.utcnow()

    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def trade_id(self) -> str:
        return self._trade_id

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def price(self) -> float:
        return self._price

    @property
    def side(self) -> OrderSide:
        return self._side

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def exchange_id(self) -> str:
        return self._exchange_id

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def cost(self) -> float:
        """交易总成本/价值"""
        return self._amount * self._price

    def to_dict(self) -> Dict[str, Any]:
        """将交易转换为字典"""
        return {
            "id": self.id,
            "order_id": self._order_id,
            "trade_id": self._trade_id,
            "exchange_id": self._exchange_id,
            "symbol": self._symbol,
            "side": self._side.value,
            "amount": self._amount,
            "price": self._price,
            "cost": self.cost,
            "timestamp": self._timestamp.isoformat(),
        }
