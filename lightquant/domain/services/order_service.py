"""
订单服务，处理订单相关的领域逻辑
"""

from typing import Any, Dict, List, Optional

from ..models.account import Account
from ..models.order import Order, OrderParams, OrderSide, OrderStatus, OrderType
from ..repositories.account_repository import AccountRepository
from ..repositories.order_repository import OrderRepository


class OrderService:
    """订单服务，处理订单相关的领域逻辑"""

    def __init__(
        self, order_repository: OrderRepository, account_repository: AccountRepository
    ):
        self._order_repository = order_repository
        self._account_repository = account_repository

    def create_order(
        self, params: OrderParams, strategy_id: str, exchange_id: str
    ) -> Order:
        """
        创建订单

        Args:
            params: 订单参数
            strategy_id: 策略ID
            exchange_id: 交易所ID

        Returns:
            创建的订单对象
        """
        # 创建订单对象
        order = Order(params, strategy_id, exchange_id)

        # 保存订单
        self._order_repository.save(order)

        return order

    def validate_order(self, order: Order) -> bool:
        """
        验证订单是否有效

        Args:
            order: 订单对象

        Returns:
            订单是否有效
        """
        # 检查账户余额是否足够
        account = self._account_repository.find_by_exchange_id(order.exchange_id)
        if not account:
            return False

        # 买入订单检查计价货币余额
        if order.params.side == OrderSide.BUY:
            # 从交易对中提取计价货币，如BTC/USDT中的USDT
            quote_currency = order.params.symbol.split("/")[1]

            # 计算所需金额
            required_amount = order.params.amount * (order.params.price or 0)

            # 检查余额是否足够
            return account.has_sufficient_balance(quote_currency, required_amount)

        # 卖出订单检查基础货币余额
        elif order.params.side == OrderSide.SELL:
            # 从交易对中提取基础货币，如BTC/USDT中的BTC
            base_currency = order.params.symbol.split("/")[0]

            # 检查余额是否足够
            return account.has_sufficient_balance(base_currency, order.params.amount)

        return False

    def get_order(self, order_id: str) -> Optional[Order]:
        """
        获取订单

        Args:
            order_id: 订单ID

        Returns:
            订单对象，如果不存在则返回None
        """
        return self._order_repository.find_by_id(order_id)

    def get_orders_by_strategy(self, strategy_id: str) -> List[Order]:
        """
        获取策略的所有订单

        Args:
            strategy_id: 策略ID

        Returns:
            订单列表
        """
        return self._order_repository.find_by_strategy_id(strategy_id)

    def get_open_orders_by_strategy(self, strategy_id: str) -> List[Order]:
        """
        获取策略的未完成订单

        Args:
            strategy_id: 策略ID

        Returns:
            未完成订单列表
        """
        return self._order_repository.find_open_by_strategy_id(strategy_id)

    def get_orders_by_exchange(self, exchange_id: str) -> List[Order]:
        """
        获取交易所的所有订单

        Args:
            exchange_id: 交易所ID

        Returns:
            订单列表
        """
        return self._order_repository.find_by_exchange_id(exchange_id)

    def get_open_orders_by_exchange(self, exchange_id: str) -> List[Order]:
        """
        获取交易所的未完成订单

        Args:
            exchange_id: 交易所ID

        Returns:
            未完成订单列表
        """
        return self._order_repository.find_open_by_exchange_id(exchange_id)

    def cancel_order(self, order_id: str) -> bool:
        """
        取消订单

        Args:
            order_id: 订单ID

        Returns:
            是否成功取消
        """
        order = self._order_repository.find_by_id(order_id)
        if not order or order.is_closed:
            return False

        order.cancel()
        self._order_repository.save(order)

        return True

    def cancel_all_orders_by_strategy(self, strategy_id: str) -> int:
        """
        取消策略的所有未完成订单

        Args:
            strategy_id: 策略ID

        Returns:
            成功取消的订单数量
        """
        orders = self._order_repository.find_open_by_strategy_id(strategy_id)
        canceled_count = 0

        for order in orders:
            order.cancel()
            self._order_repository.save(order)
            canceled_count += 1

        return canceled_count

    def cancel_all_orders_by_exchange(self, exchange_id: str) -> int:
        """
        取消交易所的所有未完成订单

        Args:
            exchange_id: 交易所ID

        Returns:
            成功取消的订单数量
        """
        orders = self._order_repository.find_open_by_exchange_id(exchange_id)
        canceled_count = 0

        for order in orders:
            order.cancel()
            self._order_repository.save(order)
            canceled_count += 1

        return canceled_count
