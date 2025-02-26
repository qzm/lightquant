"""
策略基类，所有具体策略都应该继承这个类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from ..models.strategy import StrategyConfig
from ..models.market_data import Candle, Ticker, OrderBook
from ..models.order import Order, OrderType, OrderSide
from .strategy_context import StrategyContext
from .strategy_result import StrategyResult


class BaseStrategy(ABC):
    """
    策略基类，所有具体策略都应该继承这个类
    
    策略生命周期：
    1. 初始化（__init__）
    2. 设置上下文（set_context）
    3. 初始化策略（initialize）
    4. 处理市场数据（on_candle, on_ticker, on_orderbook）
    5. 处理订单更新（on_order_update）
    6. 清理资源（cleanup）
    """
    
    def __init__(self, config: StrategyConfig):
        """
        初始化策略
        
        Args:
            config: 策略配置
        """
        self.config = config
        self.context: Optional[StrategyContext] = None
        self.parameters: Dict[str, Any] = config.params
        self.is_initialized = False
    
    def set_context(self, context: StrategyContext) -> None:
        """
        设置策略上下文
        
        Args:
            context: 策略上下文
        """
        self.context = context
    
    @abstractmethod
    def initialize(self) -> None:
        """
        初始化策略，在策略启动时调用
        在这里可以进行指标初始化、数据加载等操作
        """
        pass
    
    @abstractmethod
    def on_candle(self, candle: Candle) -> StrategyResult:
        """
        处理K线数据
        
        Args:
            candle: K线数据
            
        Returns:
            策略执行结果
        """
        pass
    
    def on_ticker(self, ticker: Ticker) -> StrategyResult:
        """
        处理Ticker数据
        
        Args:
            ticker: Ticker数据
            
        Returns:
            策略执行结果
        """
        return StrategyResult()
    
    def on_orderbook(self, orderbook: OrderBook) -> StrategyResult:
        """
        处理订单簿数据
        
        Args:
            orderbook: 订单簿数据
            
        Returns:
            策略执行结果
        """
        return StrategyResult()
    
    def on_order_update(self, order: Order) -> None:
        """
        处理订单更新
        
        Args:
            order: 订单对象
        """
        pass
    
    def cleanup(self) -> None:
        """
        清理资源，在策略停止时调用
        """
        pass
    
    # 辅助方法
    def create_market_order(self, symbol: str, side: OrderSide, amount: float) -> Optional[Order]:
        """
        创建市价单
        
        Args:
            symbol: 交易对
            side: 订单方向
            amount: 数量
            
        Returns:
            创建的订单，如果创建失败则返回None
        """
        if not self.context:
            return None
        
        return self.context.create_order(
            symbol=symbol,
            order_type=OrderType.MARKET,
            side=side,
            amount=amount
        )
    
    def create_limit_order(self, symbol: str, side: OrderSide, amount: float, price: float) -> Optional[Order]:
        """
        创建限价单
        
        Args:
            symbol: 交易对
            side: 订单方向
            amount: 数量
            price: 价格
            
        Returns:
            创建的订单，如果创建失败则返回None
        """
        if not self.context:
            return None
        
        return self.context.create_order(
            symbol=symbol,
            order_type=OrderType.LIMIT,
            side=side,
            amount=amount,
            price=price
        )
    
    def cancel_order(self, order_id: str) -> bool:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否成功取消
        """
        if not self.context:
            return False
        
        return self.context.cancel_order(order_id)
    
    def get_parameters(self) -> Dict[str, Any]:
        """
        获取策略参数
        
        Returns:
            策略参数字典
        """
        return self.parameters 