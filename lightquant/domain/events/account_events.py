"""
账户相关的领域事件
"""

from typing import Any, Dict

from .base import DomainEvent


class BalanceUpdated(DomainEvent):
    """余额更新事件"""

    def __init__(self, account, balance):
        super().__init__()
        self._account = account
        self._balance = balance

    @property
    def account(self):
        return self._account

    @property
    def balance(self):
        return self._balance

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "account_id": self._account.id,
                "exchange_id": self._account.exchange_id,
                "currency": self._balance.currency,
                "free": self._balance.free,
                "used": self._balance.used,
                "total": self._balance.total,
            }
        )
        return data


class AccountUpdated(DomainEvent):
    """账户更新事件"""

    def __init__(self, account):
        super().__init__()
        self._account = account

    @property
    def account(self):
        return self._account

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "account_id": self._account.id,
                "exchange_id": self._account.exchange_id,
                "currencies": list(self._account.balances.keys()),
            }
        )
        return data
