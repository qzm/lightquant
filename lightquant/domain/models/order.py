"""
订单模型，包括订单实体和相关值对象
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Optional, Dict, Any
import uuid

from .base import AggregateRoot, ValueObject


class OrderType(Enum):
    """订单类型枚举"""
    MARKET = "market"  # 市价单
    LIMIT = "limit"    # 限价单
    STOP = "stop"      # 止损单
    STOP_LIMIT = "stop_limit"  # 止损限价单
    TRAILING_STOP = "trailing_stop"  # 追踪止损单


class OrderStatus(Enum):
    """订单状态枚举"""
    PENDING = "pending"        # 等待中
    OPEN = "open"              # 已开放
    FILLED = "filled"          # 已成交
    PARTIALLY_FILLED = "partially_filled"  # 部分成交
    CANCELED = "canceled"      # 已取消
    REJECTED = "rejected"      # 已拒绝
    EXPIRED = "expired"        # 已过期


class OrderSide(Enum):
    """订单方向枚举"""
    BUY = "buy"    # 买入
    SELL = "sell"  # 卖出


@dataclass
class OrderParams(ValueObject):
    """订单参数值对象"""
    symbol: str                  # 交易对，如 "BTC/USDT"
    order_type: OrderType        # 订单类型
    side: OrderSide              # 买入或卖出
    amount: float                # 数量
    price: Optional[float] = None  # 价格，市价单可为None
    stop_price: Optional[float] = None  # 止损价格，仅止损单和止损限价单需要
    leverage: Optional[float] = None  # 杠杆倍数，仅杠杆交易需要
    params: Optional[Dict[str, Any]] = None  # 交易所特定参数
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}
        
        # 验证订单参数
        if self.order_type != OrderType.MARKET and self.price is None:
            raise ValueError(f"Price must be specified for {self.order_type.value} orders")
        
        if self.order_type in (OrderType.STOP, OrderType.STOP_LIMIT) and self.stop_price is None:
            raise ValueError(f"Stop price must be specified for {self.order_type.value} orders")


class Order(AggregateRoot):
    """订单聚合根"""
    
    def __init__(
        self,
        params: OrderParams,
        strategy_id: str,
        exchange_id: str,
        entity_id: Optional[str] = None
    ):
        super().__init__(entity_id)
        self._params = params
        self._strategy_id = strategy_id
        self._exchange_id = exchange_id
        self._status = OrderStatus.PENDING
        self._filled_amount = 0.0
        self._remaining_amount = params.amount
        self._average_price = None
        self._exchange_order_id: Optional[str] = None
        self._closed_at: Optional[datetime] = None
        self._trades = []
        
    @property
    def params(self) -> OrderParams:
        return self._params
    
    @property
    def strategy_id(self) -> str:
        return self._strategy_id
    
    @property
    def exchange_id(self) -> str:
        return self._exchange_id
    
    @property
    def status(self) -> OrderStatus:
        return self._status
    
    @property
    def filled_amount(self) -> float:
        return self._filled_amount
    
    @property
    def average_price(self) -> Optional[float]:
        return self._average_price
    
    @property
    def exchange_order_id(self) -> Optional[str]:
        return self._exchange_order_id
    
    @property
    def closed_at(self) -> Optional[datetime]:
        return self._closed_at
    
    @property
    def is_closed(self) -> bool:
        return self._status in (
            OrderStatus.FILLED,
            OrderStatus.CANCELED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED
        )
    
    @property
    def remaining_amount(self) -> float:
        return self._remaining_amount
    
    def submit(self, exchange_order_id: str) -> None:
        """提交订单到交易所后调用"""
        if self._status != OrderStatus.PENDING:
            raise ValueError(f"Cannot submit order with status {self._status.value}")
        
        self._exchange_order_id = exchange_order_id
        self._status = OrderStatus.OPEN
        self.update()
        
        # 添加领域事件
        from ..events.order_events import OrderSubmitted
        self.add_domain_event(OrderSubmitted(self))
    
    def fill(self, amount: float, price: float, trade_id: str) -> None:
        """处理订单成交"""
        if self.is_closed:
            raise ValueError(f"Cannot fill a closed order with status {self._status.value}")
        
        if amount <= 0:
            raise ValueError("Fill amount must be positive")
        
        if amount > self.remaining_amount:
            raise ValueError(f"Fill amount {amount} exceeds remaining amount {self.remaining_amount}")
        
        # 更新成交信息
        self._filled_amount += amount
        self._remaining_amount -= amount
        
        # 计算新的平均价格
        if self._average_price is None:
            self._average_price = price
        else:
            self._average_price = (
                (self._average_price * (self._filled_amount - amount) + price * amount)
                / self._filled_amount
            )
        
        # 添加成交记录
        from .trade import Trade
        trade = Trade(
            order_id=self.id,
            trade_id=trade_id,
            amount=amount,
            price=price,
            side=self._params.side,
            symbol=self._params.symbol,
            exchange_id=self._exchange_id
        )
        self._trades.append(trade)
        
        # 更新订单状态
        if self._filled_amount >= self._params.amount:
            self._status = OrderStatus.FILLED
            self._closed_at = datetime.utcnow()
            
            # 添加领域事件
            from ..events.order_events import OrderFilled
            self.add_domain_event(OrderFilled(self))
        else:
            self._status = OrderStatus.PARTIALLY_FILLED
            
            # 添加领域事件
            from ..events.order_events import OrderPartiallyFilled
            self.add_domain_event(OrderPartiallyFilled(self, amount, price))
        
        self.update()
    
    def cancel(self) -> None:
        """取消订单"""
        if self.is_closed:
            raise ValueError(f"Cannot cancel a closed order with status {self._status.value}")
        
        self._status = OrderStatus.CANCELED
        self._closed_at = datetime.utcnow()
        self.update()
        
        # 添加领域事件
        from ..events.order_events import OrderCanceled
        self.add_domain_event(OrderCanceled(self))
    
    def reject(self, reason: str) -> None:
        """拒绝订单"""
        if self._status != OrderStatus.PENDING and self._status != OrderStatus.OPEN:
            raise ValueError(f"Cannot reject order with status {self._status.value}")
        
        self._status = OrderStatus.REJECTED
        self._closed_at = datetime.utcnow()
        self.update()
        
        # 添加领域事件
        from ..events.order_events import OrderRejected
        self.add_domain_event(OrderRejected(self, reason))
    
    def expire(self) -> None:
        """订单过期"""
        if self.is_closed:
            raise ValueError(f"Cannot expire a closed order with status {self._status.value}")
        
        self._status = OrderStatus.EXPIRED
        self._closed_at = datetime.utcnow()
        self.update()
        
        # 添加领域事件
        from ..events.order_events import OrderExpired
        self.add_domain_event(OrderExpired(self))
    
    def to_dict(self) -> Dict[str, Any]:
        """将订单转换为字典"""
        return {
            "id": self.id,
            "exchange_id": self._exchange_id,
            "exchange_order_id": self._exchange_order_id,
            "strategy_id": self._strategy_id,
            "symbol": self._params.symbol,
            "type": self._params.order_type.value,
            "side": self._params.side.value,
            "amount": self._params.amount,
            "price": self._params.price,
            "stop_price": self._params.stop_price,
            "leverage": self._params.leverage,
            "params": self._params.params,
            "status": self._status.value,
            "filled_amount": self._filled_amount,
            "remaining_amount": self._remaining_amount,
            "average_price": self._average_price,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "closed_at": self._closed_at.isoformat() if self._closed_at else None,
        } 