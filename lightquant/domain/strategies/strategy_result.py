"""
策略结果，表示策略执行的结果
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..models.order import Order


@dataclass
class StrategyResult:
    """
    策略执行结果

    包含：
    1. 创建的订单列表
    2. 取消的订单ID列表
    3. 性能指标
    4. 日志消息
    5. 是否有错误
    6. 错误消息
    """

    orders: List[Order] = field(default_factory=list)  # 创建的订单列表
    canceled_order_ids: List[str] = field(default_factory=list)  # 取消的订单ID列表
    metrics: Dict[str, Any] = field(default_factory=dict)  # 性能指标
    logs: List[str] = field(default_factory=list)  # 日志消息
    has_error: bool = False  # 是否有错误
    error_message: Optional[str] = None  # 错误消息

    def add_order(self, order: Order) -> None:
        """
        添加订单

        Args:
            order: 订单对象
        """
        self.orders.append(order)

    def add_canceled_order_id(self, order_id: str) -> None:
        """
        添加取消的订单ID

        Args:
            order_id: 订单ID
        """
        self.canceled_order_ids.append(order_id)

    def add_metric(self, key: str, value: Any) -> None:
        """
        添加性能指标

        Args:
            key: 指标名称
            value: 指标值
        """
        self.metrics[key] = value

    def add_log(self, message: str) -> None:
        """
        添加日志消息

        Args:
            message: 日志消息
        """
        self.logs.append(message)

    def set_error(self, message: str) -> None:
        """
        设置错误

        Args:
            message: 错误消息
        """
        self.has_error = True
        self.error_message = message

    def merge(self, other: "StrategyResult") -> None:
        """
        合并另一个策略结果

        Args:
            other: 另一个策略结果
        """
        self.orders.extend(other.orders)
        self.canceled_order_ids.extend(other.canceled_order_ids)
        self.metrics.update(other.metrics)
        self.logs.extend(other.logs)

        if other.has_error:
            self.has_error = True
            if self.error_message:
                self.error_message += f"; {other.error_message}"
            else:
                self.error_message = other.error_message
