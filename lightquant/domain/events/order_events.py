"""
订单相关的领域事件
"""

from typing import Any, Dict

from .base import DomainEvent


class OrderSubmitted(DomainEvent):
    """订单已提交事件"""

    def __init__(self, order):
        super().__init__()
        self._order = order

    @property
    def order(self):
        return self._order

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "order_id": self._order.id,
                "exchange_id": self._order.exchange_id,
                "exchange_order_id": self._order.exchange_order_id,
                "strategy_id": self._order.strategy_id,
                "symbol": self._order.params.symbol,
                "order_type": self._order.params.order_type.value,
                "side": self._order.params.side.value,
                "amount": self._order.params.amount,
                "price": self._order.params.price,
            }
        )
        return data


class OrderPartiallyFilled(DomainEvent):
    """订单部分成交事件"""

    def __init__(self, order, filled_amount, price):
        super().__init__()
        self._order = order
        self._filled_amount = filled_amount
        self._price = price

    @property
    def order(self):
        return self._order

    @property
    def filled_amount(self) -> float:
        return self._filled_amount

    @property
    def price(self) -> float:
        return self._price

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "order_id": self._order.id,
                "exchange_id": self._order.exchange_id,
                "exchange_order_id": self._order.exchange_order_id,
                "strategy_id": self._order.strategy_id,
                "symbol": self._order.params.symbol,
                "side": self._order.params.side.value,
                "filled_amount": self._filled_amount,
                "price": self._price,
                "total_filled_amount": self._order.filled_amount,
                "remaining_amount": self._order.remaining_amount,
            }
        )
        return data


class OrderFilled(DomainEvent):
    """订单完全成交事件"""

    def __init__(self, order):
        super().__init__()
        self._order = order

    @property
    def order(self):
        return self._order

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "order_id": self._order.id,
                "exchange_id": self._order.exchange_id,
                "exchange_order_id": self._order.exchange_order_id,
                "strategy_id": self._order.strategy_id,
                "symbol": self._order.params.symbol,
                "order_type": self._order.params.order_type.value,
                "side": self._order.params.side.value,
                "amount": self._order.params.amount,
                "average_price": self._order.average_price,
            }
        )
        return data


class OrderCanceled(DomainEvent):
    """订单已取消事件"""

    def __init__(self, order):
        super().__init__()
        self._order = order

    @property
    def order(self):
        return self._order

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "order_id": self._order.id,
                "exchange_id": self._order.exchange_id,
                "exchange_order_id": self._order.exchange_order_id,
                "strategy_id": self._order.strategy_id,
                "symbol": self._order.params.symbol,
                "filled_amount": self._order.filled_amount,
                "remaining_amount": self._order.remaining_amount,
            }
        )
        return data


class OrderRejected(DomainEvent):
    """订单被拒绝事件"""

    def __init__(self, order, reason):
        super().__init__()
        self._order = order
        self._reason = reason

    @property
    def order(self):
        return self._order

    @property
    def reason(self) -> str:
        return self._reason

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "order_id": self._order.id,
                "exchange_id": self._order.exchange_id,
                "exchange_order_id": self._order.exchange_order_id,
                "strategy_id": self._order.strategy_id,
                "symbol": self._order.params.symbol,
                "reason": self._reason,
            }
        )
        return data


class OrderExpired(DomainEvent):
    """订单已过期事件"""

    def __init__(self, order):
        super().__init__()
        self._order = order

    @property
    def order(self):
        return self._order

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "order_id": self._order.id,
                "exchange_id": self._order.exchange_id,
                "exchange_order_id": self._order.exchange_order_id,
                "strategy_id": self._order.strategy_id,
                "symbol": self._order.params.symbol,
                "filled_amount": self._order.filled_amount,
                "remaining_amount": self._order.remaining_amount,
            }
        )
        return data
