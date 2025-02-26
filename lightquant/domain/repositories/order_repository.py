"""
订单仓库接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..models.order import Order


class OrderRepository(ABC):
    """订单仓库接口"""

    @abstractmethod
    def save(self, order: Order) -> None:
        """
        保存订单

        Args:
            order: 订单对象
        """
        pass

    @abstractmethod
    def find_by_id(self, order_id: str) -> Optional[Order]:
        """
        根据ID查找订单

        Args:
            order_id: 订单ID

        Returns:
            订单对象，如果不存在则返回None
        """
        pass

    @abstractmethod
    def find_by_exchange_order_id(
        self, exchange_id: str, exchange_order_id: str
    ) -> Optional[Order]:
        """
        根据交易所订单ID查找订单

        Args:
            exchange_id: 交易所ID
            exchange_order_id: 交易所订单ID

        Returns:
            订单对象，如果不存在则返回None
        """
        pass

    @abstractmethod
    def find_by_strategy_id(self, strategy_id: str) -> List[Order]:
        """
        查找策略的所有订单

        Args:
            strategy_id: 策略ID

        Returns:
            订单列表
        """
        pass

    @abstractmethod
    def find_open_by_strategy_id(self, strategy_id: str) -> List[Order]:
        """
        查找策略的未完成订单

        Args:
            strategy_id: 策略ID

        Returns:
            未完成订单列表
        """
        pass

    @abstractmethod
    def find_by_exchange_id(self, exchange_id: str) -> List[Order]:
        """
        查找交易所的所有订单

        Args:
            exchange_id: 交易所ID

        Returns:
            订单列表
        """
        pass

    @abstractmethod
    def find_open_by_exchange_id(self, exchange_id: str) -> List[Order]:
        """
        查找交易所的未完成订单

        Args:
            exchange_id: 交易所ID

        Returns:
            未完成订单列表
        """
        pass

    @abstractmethod
    def find_by_symbol(self, symbol: str) -> List[Order]:
        """
        查找交易对的所有订单

        Args:
            symbol: 交易对，如 "BTC/USDT"

        Returns:
            订单列表
        """
        pass

    @abstractmethod
    def delete(self, order_id: str) -> bool:
        """
        删除订单

        Args:
            order_id: 订单ID

        Returns:
            是否成功删除
        """
        pass
