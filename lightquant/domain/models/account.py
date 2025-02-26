"""
账户模型，包括账户和余额
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

from .base import AggregateRoot, ValueObject


@dataclass
class Balance:
    """资产余额数据类"""
    asset: str  # 资产名称，如 "BTC", "USDT"
    free: float  # 可用余额
    locked: float = 0.0  # 锁定余额（如挂单冻结）
    
    @property
    def total(self) -> float:
        """总余额 = 可用余额 + 锁定余额"""
        return self.free + self.locked


class Account(AggregateRoot):
    """账户聚合根"""
    
    def __init__(self, exchange_id: str, name: Optional[str] = None):
        super().__init__(str(uuid.uuid4()))
        self.exchange_id = exchange_id
        self.name = name or exchange_id
        self.balances: Dict[str, Balance] = {}
    
    def update_balance(self, asset: str, free: float, locked: float = 0.0) -> None:
        """更新资产余额"""
        self.balances[asset] = Balance(asset=asset, free=free, locked=locked)
        self.update()
        
        # 添加领域事件
        from ..events.account_events import BalanceUpdated
        self.add_domain_event(BalanceUpdated(self, self.balances[asset]))
    
    def get_balance(self, asset: str) -> Optional[Balance]:
        """获取指定资产的余额"""
        return self.balances.get(asset)
    
    def has_sufficient_balance(self, asset: str, amount: float) -> bool:
        """检查是否有足够的可用余额"""
        balance = self.get_balance(asset)
        if not balance:
            return False
        return balance.free >= amount
    
    def lock_balance(self, asset: str, amount: float) -> bool:
        """锁定余额（如挂单时）"""
        balance = self.get_balance(asset)
        if not balance or balance.free < amount:
            return False
        
        new_free = balance.free - amount
        new_locked = balance.locked + amount
        self.update_balance(asset, new_free, new_locked)
        return True
    
    def unlock_balance(self, asset: str, amount: float) -> bool:
        """解锁余额（如取消挂单时）"""
        balance = self.get_balance(asset)
        if not balance or balance.locked < amount:
            return False
        
        new_free = balance.free + amount
        new_locked = balance.locked - amount
        self.update_balance(asset, new_free, new_locked)
        return True
    
    def deduct_balance(self, asset: str, amount: float, from_locked: bool = False) -> bool:
        """扣除余额（如成交时）"""
        balance = self.get_balance(asset)
        if not balance:
            return False
        
        if from_locked:
            if balance.locked < amount:
                return False
            new_locked = balance.locked - amount
            self.update_balance(asset, balance.free, new_locked)
        else:
            if balance.free < amount:
                return False
            new_free = balance.free - amount
            self.update_balance(asset, new_free, balance.locked)
        
        return True
    
    def add_balance(self, asset: str, amount: float) -> None:
        """增加余额（如成交时）"""
        balance = self.get_balance(asset)
        if balance:
            new_free = balance.free + amount
            self.update_balance(asset, new_free, balance.locked)
        else:
            self.update_balance(asset, amount, 0.0)
    
    def get_equity(self, quote_asset: str = "USDT", prices: Dict[str, float] = None) -> float:
        """
        计算账户权益（以指定计价货币表示）
        
        Args:
            quote_asset: 计价货币，默认为USDT
            prices: 资产价格字典，格式为 {symbol: price}，如 {"BTC/USDT": 50000.0}
            
        Returns:
            float: 账户总权益
        """
        if not prices:
            return 0.0
            
        equity = 0.0
        
        # 添加计价货币本身的余额
        quote_balance = self.get_balance(quote_asset)
        if quote_balance:
            equity += quote_balance.total
            
        # 计算其他资产的价值
        for asset, balance in self.balances.items():
            if asset == quote_asset:
                continue
                
            symbol = f"{asset}/{quote_asset}"
            if symbol in prices:
                equity += balance.total * prices[symbol]
                
        return equity
    
    def to_dict(self) -> Dict:
        """将账户转换为字典"""
        return {
            "id": self.id,
            "exchange_id": self.exchange_id,
            "name": self.name,
            "balances": {
                asset: {
                    "asset": balance.asset,
                    "free": balance.free,
                    "locked": balance.locked,
                    "total": balance.total
                }
                for asset, balance in self.balances.items()
            },
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat()
        } 