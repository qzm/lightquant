"""
策略相关的领域事件
"""

from typing import Any, Dict

from .base import DomainEvent


class StrategyStarted(DomainEvent):
    """策略启动事件"""

    def __init__(self, strategy):
        super().__init__()
        self._strategy = strategy

    @property
    def strategy(self):
        return self._strategy

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "strategy_id": self._strategy.id,
                "strategy_name": self._strategy.config.name,
                "symbols": self._strategy.config.symbols,
                "exchange_ids": self._strategy.config.exchange_ids,
            }
        )
        return data


class StrategyPaused(DomainEvent):
    """策略暂停事件"""

    def __init__(self, strategy):
        super().__init__()
        self._strategy = strategy

    @property
    def strategy(self):
        return self._strategy

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "strategy_id": self._strategy.id,
                "strategy_name": self._strategy.config.name,
            }
        )
        return data


class StrategyResumed(DomainEvent):
    """策略恢复事件"""

    def __init__(self, strategy):
        super().__init__()
        self._strategy = strategy

    @property
    def strategy(self):
        return self._strategy

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "strategy_id": self._strategy.id,
                "strategy_name": self._strategy.config.name,
            }
        )
        return data


class StrategyStopped(DomainEvent):
    """策略停止事件"""

    def __init__(self, strategy):
        super().__init__()
        self._strategy = strategy

    @property
    def strategy(self):
        return self._strategy

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "strategy_id": self._strategy.id,
                "strategy_name": self._strategy.config.name,
                "run_duration": (
                    (
                        self._strategy.stop_time - self._strategy.start_time
                    ).total_seconds()
                    if self._strategy.start_time and self._strategy.stop_time
                    else None
                ),
            }
        )
        return data


class StrategyError(DomainEvent):
    """策略错误事件"""

    def __init__(self, strategy, error_message):
        super().__init__()
        self._strategy = strategy
        self._error_message = error_message

    @property
    def strategy(self):
        return self._strategy

    @property
    def error_message(self) -> str:
        return self._error_message

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "strategy_id": self._strategy.id,
                "strategy_name": self._strategy.config.name,
                "error_message": self._error_message,
            }
        )
        return data


class StrategyConfigUpdated(DomainEvent):
    """策略配置更新事件"""

    def __init__(self, strategy):
        super().__init__()
        self._strategy = strategy

    @property
    def strategy(self):
        return self._strategy

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "strategy_id": self._strategy.id,
                "strategy_name": self._strategy.config.name,
                "symbols": self._strategy.config.symbols,
                "exchange_ids": self._strategy.config.exchange_ids,
                "timeframes": self._strategy.config.timeframes,
            }
        )
        return data
