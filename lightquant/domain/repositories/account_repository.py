"""
账户仓库接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..models.account import Account


class AccountRepository(ABC):
    """账户仓库接口"""

    @abstractmethod
    def save(self, account: Account) -> None:
        """
        保存账户

        Args:
            account: 账户对象
        """
        pass

    @abstractmethod
    def find_by_id(self, account_id: str) -> Optional[Account]:
        """
        根据ID查找账户

        Args:
            account_id: 账户ID

        Returns:
            账户对象，如果不存在则返回None
        """
        pass

    @abstractmethod
    def find_by_exchange_id(self, exchange_id: str) -> Optional[Account]:
        """
        根据交易所ID查找账户

        Args:
            exchange_id: 交易所ID

        Returns:
            账户对象，如果不存在则返回None
        """
        pass

    @abstractmethod
    def find_all(self) -> List[Account]:
        """
        查找所有账户

        Returns:
            账户列表
        """
        pass

    @abstractmethod
    def delete(self, account_id: str) -> bool:
        """
        删除账户

        Args:
            account_id: 账户ID

        Returns:
            是否成功删除
        """
        pass
