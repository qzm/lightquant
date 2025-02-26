"""
风险控制规则模块，包含各种风险控制规则的实现。
这些规则用于管理交易风险，防止过度交易和资金损失。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, date
import logging

from ..models.order import Order
from ..models.account import Account


class RiskRule(ABC):
    """风险控制规则抽象基类"""
    
    def __init__(self, name: str, description: str = "", enabled: bool = True):
        self.name = name
        self.description = description
        self.enabled = enabled
        self.logger = logging.getLogger(f"risk_rule.{self.__class__.__name__}")
    
    @abstractmethod
    def check_order(self, order: Order, account: Account, context: Dict[str, Any]) -> bool:
        """
        检查订单是否符合风险控制规则
        
        Args:
            order: 要检查的订单
            account: 账户信息
            context: 上下文信息，包含市场数据等
            
        Returns:
            bool: 如果订单符合规则返回True，否则返回False
        """
        pass
    
    def enable(self) -> None:
        """启用规则"""
        self.enabled = True
        self.logger.info(f"Risk rule '{self.name}' enabled")
    
    def disable(self) -> None:
        """禁用规则"""
        self.enabled = False
        self.logger.info(f"Risk rule '{self.name}' disabled")
    
    def update_params(self, params: Dict[str, Any]) -> None:
        """
        更新规则参数
        
        Args:
            params: 参数字典
        """
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)
                self.logger.info(f"Updated parameter '{key}' to {value} for rule '{self.name}'")
            else:
                self.logger.warning(f"Parameter '{key}' does not exist for rule '{self.name}'")


class PositionSizeRule(RiskRule):
    """
    仓位大小规则
    
    控制单笔交易的仓位大小，可以基于最大金额、账户权益百分比或固定数量
    """
    
    def __init__(
        self,
        name: str = "Position Size Rule",
        description: str = "Controls the position size of trades",
        enabled: bool = True,
        max_position_value: Optional[float] = None,
        max_position_percentage: Optional[float] = None,
        max_position_amount: Optional[float] = None,
        quote_asset: str = "USDT"
    ):
        """
        初始化仓位大小规则
        
        Args:
            name: 规则名称
            description: 规则描述
            enabled: 是否启用
            max_position_value: 最大仓位价值（以计价货币计）
            max_position_percentage: 最大仓位百分比（占账户权益）
            max_position_amount: 最大仓位数量（以基础货币计）
            quote_asset: 计价货币，默认为USDT
        """
        super().__init__(name, description, enabled)
        self.max_position_value = max_position_value
        self.max_position_percentage = max_position_percentage
        self.max_position_amount = max_position_amount
        self.quote_asset = quote_asset
    
    def check_order(self, order: Order, account: Account, context: Dict[str, Any]) -> bool:
        """
        检查订单是否符合仓位大小规则
        
        Args:
            order: 要检查的订单
            account: 账户信息
            context: 上下文信息，包含市场数据等
            
        Returns:
            bool: 如果订单符合规则返回True，否则返回False
        """
        if not self.enabled:
            return True
        
        # 获取订单的基础货币和计价货币
        symbol = order.params.symbol
        base_asset, quote_asset = symbol.split('/')
        
        # 检查最大仓位数量
        if self.max_position_amount is not None and order.params.amount > self.max_position_amount:
            self.logger.warning(
                f"Order amount {order.params.amount} {base_asset} exceeds max position amount {self.max_position_amount}"
            )
            return False
        
        # 计算订单价值
        price = order.params.price
        if price is None and 'ticker' in context:
            # 如果是市价单，使用当前市场价格
            ticker = context['ticker']
            if symbol in ticker:
                price = ticker[symbol]['last']
        
        if price is None:
            self.logger.warning(f"Cannot determine price for order {order.id}")
            return True  # 无法确定价格时，默认通过
        
        order_value = order.params.amount * price
        
        # 检查最大仓位价值
        if self.max_position_value is not None and order_value > self.max_position_value:
            self.logger.warning(
                f"Order value {order_value} {quote_asset} exceeds max position value {self.max_position_value}"
            )
            return False
        
        # 检查最大仓位百分比
        if self.max_position_percentage is not None:
            # 计算账户权益
            prices = {}
            if 'ticker' in context:
                ticker = context['ticker']
                for symbol, data in ticker.items():
                    prices[symbol] = data['last']
            
            equity = account.get_equity(self.quote_asset, prices)
            if equity <= 0:
                self.logger.warning(f"Account equity is zero or negative: {equity}")
                return False
            
            position_percentage = (order_value / equity) * 100
            if position_percentage > self.max_position_percentage:
                self.logger.warning(
                    f"Order position percentage {position_percentage:.2f}% exceeds max {self.max_position_percentage}%"
                )
                return False
        
        return True


class MaxDrawdownRule(RiskRule):
    """
    最大回撤规则
    
    当账户回撤超过指定阈值时，停止新的交易
    """
    
    def __init__(
        self,
        name: str = "Max Drawdown Rule",
        description: str = "Stops trading when account drawdown exceeds threshold",
        enabled: bool = True,
        max_drawdown_percentage: float = 10.0,
        lookback_days: int = 30
    ):
        """
        初始化最大回撤规则
        
        Args:
            name: 规则名称
            description: 规则描述
            enabled: 是否启用
            max_drawdown_percentage: 最大回撤百分比
            lookback_days: 回顾天数
        """
        super().__init__(name, description, enabled)
        self.max_drawdown_percentage = max_drawdown_percentage
        self.lookback_days = lookback_days
    
    def check_order(self, order: Order, account: Account, context: Dict[str, Any]) -> bool:
        """
        检查订单是否符合最大回撤规则
        
        Args:
            order: 要检查的订单
            account: 账户信息
            context: 上下文信息，包含市场数据等
            
        Returns:
            bool: 如果订单符合规则返回True，否则返回False
        """
        if not self.enabled:
            return True
        
        # 检查上下文中是否有回撤信息
        if 'drawdown' not in context:
            self.logger.warning("Drawdown information not available in context")
            return True  # 无法确定回撤时，默认通过
        
        current_drawdown = context['drawdown']
        if current_drawdown > self.max_drawdown_percentage:
            self.logger.warning(
                f"Current drawdown {current_drawdown:.2f}% exceeds max drawdown {self.max_drawdown_percentage}%"
            )
            return False
        
        return True


class MaxTradesPerDayRule(RiskRule):
    """
    每日最大交易次数规则
    
    限制每日交易次数，防止过度交易
    """
    
    def __init__(
        self,
        name: str = "Max Trades Per Day Rule",
        description: str = "Limits the number of trades per day",
        enabled: bool = True,
        max_trades: int = 10
    ):
        """
        初始化每日最大交易次数规则
        
        Args:
            name: 规则名称
            description: 规则描述
            enabled: 是否启用
            max_trades: 每日最大交易次数
        """
        super().__init__(name, description, enabled)
        self.max_trades = max_trades
        self._trades_today: List[str] = []
        self._current_date = date.today()
    
    def check_order(self, order: Order, account: Account, context: Dict[str, Any]) -> bool:
        """
        检查订单是否符合每日最大交易次数规则
        
        Args:
            order: 要检查的订单
            account: 账户信息
            context: 上下文信息，包含市场数据等
            
        Returns:
            bool: 如果订单符合规则返回True，否则返回False
        """
        if not self.enabled:
            return True
        
        # 检查日期是否变更，如果变更则重置计数
        today = date.today()
        if today != self._current_date:
            self._trades_today = []
            self._current_date = today
        
        # 检查今日交易次数是否已达上限
        if len(self._trades_today) >= self.max_trades:
            self.logger.warning(
                f"Max trades per day ({self.max_trades}) reached for {today.isoformat()}"
            )
            return False
        
        # 记录本次交易
        self._trades_today.append(order.id)
        self.logger.info(f"Trade {len(self._trades_today)}/{self.max_trades} for today")
        
        return True 