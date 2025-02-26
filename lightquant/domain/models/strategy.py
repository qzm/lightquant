"""
策略模型，包括策略配置和状态
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set

from .base import AggregateRoot, ValueObject


class StrategyStatus(Enum):
    """策略状态枚举"""
    CREATED = "created"  # 已创建
    RUNNING = "running"  # 运行中
    PAUSED = "paused"    # 已暂停
    STOPPED = "stopped"  # 已停止
    ERROR = "error"      # 错误状态


@dataclass
class StrategyConfig(ValueObject):
    """策略配置值对象"""
    name: str  # 策略名称
    symbols: List[str]  # 交易对列表
    exchange_ids: List[str]  # 交易所ID列表
    params: Dict[str, Any] = field(default_factory=dict)  # 策略参数
    timeframes: List[str] = field(default_factory=lambda: ["1m"])  # 时间周期列表
    
    def __post_init__(self):
        # 确保列表类型的字段不为None
        if self.symbols is None:
            self.symbols = []
        if self.exchange_ids is None:
            self.exchange_ids = []
        if self.timeframes is None:
            self.timeframes = ["1m"]
        if self.params is None:
            self.params = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """将策略配置转换为字典"""
        return {
            "name": self.name,
            "symbols": self.symbols,
            "exchange_ids": self.exchange_ids,
            "timeframes": self.timeframes,
            "params": self.params,
        }


class Strategy(AggregateRoot):
    """策略聚合根"""
    
    def __init__(
        self,
        config: StrategyConfig,
        entity_id: Optional[str] = None
    ):
        super().__init__(entity_id)
        self._config = config
        self._status = StrategyStatus.CREATED
        self._start_time: Optional[datetime] = None
        self._stop_time: Optional[datetime] = None
        self._last_run_time: Optional[datetime] = None
        self._error_message: Optional[str] = None
        self._performance_metrics: Dict[str, Any] = {}
        self._order_ids: Set[str] = set()
    
    @property
    def config(self) -> StrategyConfig:
        return self._config
    
    @property
    def status(self) -> StrategyStatus:
        return self._status
    
    @property
    def start_time(self) -> Optional[datetime]:
        return self._start_time
    
    @property
    def stop_time(self) -> Optional[datetime]:
        return self._stop_time
    
    @property
    def last_run_time(self) -> Optional[datetime]:
        return self._last_run_time
    
    @property
    def error_message(self) -> Optional[str]:
        return self._error_message
    
    @property
    def performance_metrics(self) -> Dict[str, Any]:
        return self._performance_metrics
    
    @property
    def order_ids(self) -> Set[str]:
        return self._order_ids
    
    def start(self) -> None:
        """启动策略"""
        if self._status == StrategyStatus.RUNNING:
            return
        
        self._status = StrategyStatus.RUNNING
        self._start_time = datetime.utcnow()
        self._error_message = None
        self.update()
        
        # 添加领域事件
        from ..events.strategy_events import StrategyStarted
        self.add_domain_event(StrategyStarted(self))
    
    def pause(self) -> None:
        """暂停策略"""
        if self._status != StrategyStatus.RUNNING:
            return
        
        self._status = StrategyStatus.PAUSED
        self.update()
        
        # 添加领域事件
        from ..events.strategy_events import StrategyPaused
        self.add_domain_event(StrategyPaused(self))
    
    def resume(self) -> None:
        """恢复策略"""
        if self._status != StrategyStatus.PAUSED:
            return
        
        self._status = StrategyStatus.RUNNING
        self.update()
        
        # 添加领域事件
        from ..events.strategy_events import StrategyResumed
        self.add_domain_event(StrategyResumed(self))
    
    def stop(self) -> None:
        """停止策略"""
        if self._status == StrategyStatus.STOPPED:
            return
        
        self._status = StrategyStatus.STOPPED
        self._stop_time = datetime.utcnow()
        self.update()
        
        # 添加领域事件
        from ..events.strategy_events import StrategyStopped
        self.add_domain_event(StrategyStopped(self))
    
    def set_error(self, error_message: str) -> None:
        """设置策略错误状态"""
        self._status = StrategyStatus.ERROR
        self._error_message = error_message
        self.update()
        
        # 添加领域事件
        from ..events.strategy_events import StrategyError
        self.add_domain_event(StrategyError(self, error_message))
    
    def update_config(self, config: StrategyConfig) -> None:
        """更新策略配置"""
        self._config = config
        self.update()
        
        # 添加领域事件
        from ..events.strategy_events import StrategyConfigUpdated
        self.add_domain_event(StrategyConfigUpdated(self))
    
    def update_performance_metrics(self, metrics: Dict[str, Any]) -> None:
        """更新性能指标"""
        self._performance_metrics.update(metrics)
        self._last_run_time = datetime.utcnow()
        self.update()
    
    def add_order(self, order_id: str) -> None:
        """添加订单ID"""
        self._order_ids.add(order_id)
        self.update()
    
    def remove_order(self, order_id: str) -> None:
        """移除订单ID"""
        if order_id in self._order_ids:
            self._order_ids.remove(order_id)
            self.update()
    
    def to_dict(self) -> Dict[str, Any]:
        """将策略转换为字典"""
        return {
            "id": self.id,
            "config": self._config.to_dict(),
            "status": self._status.value,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "stop_time": self._stop_time.isoformat() if self._stop_time else None,
            "last_run_time": self._last_run_time.isoformat() if self._last_run_time else None,
            "error_message": self._error_message,
            "performance_metrics": self._performance_metrics,
            "order_ids": list(self._order_ids),
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
        } 