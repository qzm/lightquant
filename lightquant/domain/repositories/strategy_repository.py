"""
策略仓库接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..models.strategy import Strategy, StrategyStatus


class StrategyRepository(ABC):
    """策略仓库接口"""

    @abstractmethod
    def save(self, strategy: Strategy) -> None:
        """
        保存策略

        Args:
            strategy: 策略对象
        """
        pass

    @abstractmethod
    def find_by_id(self, strategy_id: str) -> Optional[Strategy]:
        """
        根据ID查找策略

        Args:
            strategy_id: 策略ID

        Returns:
            策略对象，如果不存在则返回None
        """
        pass

    @abstractmethod
    def find_all(self) -> List[Strategy]:
        """
        查找所有策略

        Returns:
            策略列表
        """
        pass

    @abstractmethod
    def find_by_status(self, status: StrategyStatus) -> List[Strategy]:
        """
        根据状态查找策略

        Args:
            status: 策略状态

        Returns:
            策略列表
        """
        pass

    @abstractmethod
    def find_by_exchange_id(self, exchange_id: str) -> List[Strategy]:
        """
        根据交易所ID查找策略

        Args:
            exchange_id: 交易所ID

        Returns:
            策略列表
        """
        pass

    @abstractmethod
    def find_by_symbol(self, symbol: str) -> List[Strategy]:
        """
        根据交易对查找策略

        Args:
            symbol: 交易对，如 "BTC/USDT"

        Returns:
            策略列表
        """
        pass

    @abstractmethod
    def delete(self, strategy_id: str) -> bool:
        """
        删除策略

        Args:
            strategy_id: 策略ID

        Returns:
            是否成功删除
        """
        pass
