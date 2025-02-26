"""
策略服务，处理策略相关的领域逻辑
"""

from typing import List, Dict, Optional, Any

from ..models.strategy import Strategy, StrategyConfig, StrategyStatus
from ..repositories.strategy_repository import StrategyRepository
from ..repositories.order_repository import OrderRepository


class StrategyService:
    """策略服务，处理策略相关的领域逻辑"""
    
    def __init__(
        self,
        strategy_repository: StrategyRepository,
        order_repository: OrderRepository
    ):
        self._strategy_repository = strategy_repository
        self._order_repository = order_repository
    
    def create_strategy(self, config: StrategyConfig) -> Strategy:
        """
        创建策略
        
        Args:
            config: 策略配置
            
        Returns:
            创建的策略对象
        """
        strategy = Strategy(config)
        self._strategy_repository.save(strategy)
        return strategy
    
    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """
        获取策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            策略对象，如果不存在则返回None
        """
        return self._strategy_repository.find_by_id(strategy_id)
    
    def get_strategies(self) -> List[Strategy]:
        """
        获取所有策略
        
        Returns:
            策略列表
        """
        return self._strategy_repository.find_all()
    
    def get_strategies_by_status(self, status: StrategyStatus) -> List[Strategy]:
        """
        获取指定状态的策略
        
        Args:
            status: 策略状态
            
        Returns:
            策略列表
        """
        return self._strategy_repository.find_by_status(status)
    
    def get_strategies_by_exchange(self, exchange_id: str) -> List[Strategy]:
        """
        获取指定交易所的策略
        
        Args:
            exchange_id: 交易所ID
            
        Returns:
            策略列表
        """
        return self._strategy_repository.find_by_exchange_id(exchange_id)
    
    def get_strategies_by_symbol(self, symbol: str) -> List[Strategy]:
        """
        获取指定交易对的策略
        
        Args:
            symbol: 交易对，如 "BTC/USDT"
            
        Returns:
            策略列表
        """
        return self._strategy_repository.find_by_symbol(symbol)
    
    def start_strategy(self, strategy_id: str) -> bool:
        """
        启动策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            是否成功启动
        """
        strategy = self._strategy_repository.find_by_id(strategy_id)
        if not strategy:
            return False
        
        strategy.start()
        self._strategy_repository.save(strategy)
        return True
    
    def pause_strategy(self, strategy_id: str) -> bool:
        """
        暂停策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            是否成功暂停
        """
        strategy = self._strategy_repository.find_by_id(strategy_id)
        if not strategy or strategy.status != StrategyStatus.RUNNING:
            return False
        
        strategy.pause()
        self._strategy_repository.save(strategy)
        return True
    
    def resume_strategy(self, strategy_id: str) -> bool:
        """
        恢复策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            是否成功恢复
        """
        strategy = self._strategy_repository.find_by_id(strategy_id)
        if not strategy or strategy.status != StrategyStatus.PAUSED:
            return False
        
        strategy.resume()
        self._strategy_repository.save(strategy)
        return True
    
    def stop_strategy(self, strategy_id: str) -> bool:
        """
        停止策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            是否成功停止
        """
        strategy = self._strategy_repository.find_by_id(strategy_id)
        if not strategy or strategy.status == StrategyStatus.STOPPED:
            return False
        
        strategy.stop()
        self._strategy_repository.save(strategy)
        return True
    
    def update_strategy_config(self, strategy_id: str, config: StrategyConfig) -> bool:
        """
        更新策略配置
        
        Args:
            strategy_id: 策略ID
            config: 新的策略配置
            
        Returns:
            是否成功更新
        """
        strategy = self._strategy_repository.find_by_id(strategy_id)
        if not strategy:
            return False
        
        strategy.update_config(config)
        self._strategy_repository.save(strategy)
        return True
    
    def update_strategy_performance(self, strategy_id: str, metrics: Dict[str, Any]) -> bool:
        """
        更新策略性能指标
        
        Args:
            strategy_id: 策略ID
            metrics: 性能指标
            
        Returns:
            是否成功更新
        """
        strategy = self._strategy_repository.find_by_id(strategy_id)
        if not strategy:
            return False
        
        strategy.update_performance_metrics(metrics)
        self._strategy_repository.save(strategy)
        return True
    
    def add_order_to_strategy(self, strategy_id: str, order_id: str) -> bool:
        """
        将订单添加到策略
        
        Args:
            strategy_id: 策略ID
            order_id: 订单ID
            
        Returns:
            是否成功添加
        """
        strategy = self._strategy_repository.find_by_id(strategy_id)
        if not strategy:
            return False
        
        order = self._order_repository.find_by_id(order_id)
        if not order:
            return False
        
        strategy.add_order(order_id)
        self._strategy_repository.save(strategy)
        return True
    
    def remove_order_from_strategy(self, strategy_id: str, order_id: str) -> bool:
        """
        从策略中移除订单
        
        Args:
            strategy_id: 策略ID
            order_id: 订单ID
            
        Returns:
            是否成功移除
        """
        strategy = self._strategy_repository.find_by_id(strategy_id)
        if not strategy:
            return False
        
        strategy.remove_order(order_id)
        self._strategy_repository.save(strategy)
        return True
    
    def get_strategy_orders(self, strategy_id: str) -> List[str]:
        """
        获取策略的所有订单ID
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            订单ID列表
        """
        strategy = self._strategy_repository.find_by_id(strategy_id)
        if not strategy:
            return []
        
        return list(strategy.order_ids) 