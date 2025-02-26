"""
策略仓库SQL实现
"""

import json
from typing import List, Optional, Dict, Any, Set

from sqlalchemy.orm import Session

from ....domain.models.strategy import Strategy, StrategyConfig, StrategyStatus
from ....domain.repositories.strategy_repository import StrategyRepository
from ..models.strategy_model import StrategyModel, StrategyStatusEnum
from ..database_manager import DatabaseManager


class SQLStrategyRepository(StrategyRepository):
    """策略仓库SQL实现"""

    def __init__(self, db_manager: DatabaseManager):
        self._db_manager = db_manager

    def save(self, strategy: Strategy) -> None:
        """保存策略"""
        with self._db_manager.session() as session:
            # 检查策略是否已存在
            strategy_model = (
                session.query(StrategyModel)
                .filter(StrategyModel.id == strategy.id)
                .first()
            )

            if strategy_model:
                # 更新现有策略
                strategy_model.name = strategy.config.name
                strategy_model.status = self._map_strategy_status(strategy.status)
                strategy_model.config = json.dumps(strategy.config.params)
                strategy_model.symbols = json.dumps(strategy.config.symbols)
                strategy_model.exchange_ids = json.dumps(strategy.config.exchange_ids)
                strategy_model.timeframes = json.dumps(strategy.config.timeframes)
                strategy_model.performance_metrics = json.dumps(
                    strategy.performance_metrics
                )
                strategy_model.error_message = strategy.error_message
                strategy_model.updated_at = strategy.updated_at
                strategy_model.start_time = strategy.start_time
                strategy_model.stop_time = strategy.stop_time
                strategy_model.last_run_time = strategy.last_run_time
            else:
                # 创建新策略
                strategy_model = StrategyModel(
                    id=strategy.id,
                    name=strategy.config.name,
                    status=self._map_strategy_status(strategy.status),
                    config=json.dumps(strategy.config.params),
                    symbols=json.dumps(strategy.config.symbols),
                    exchange_ids=json.dumps(strategy.config.exchange_ids),
                    timeframes=json.dumps(strategy.config.timeframes),
                    performance_metrics=json.dumps(strategy.performance_metrics),
                    error_message=strategy.error_message,
                    created_at=strategy.created_at,
                    updated_at=strategy.updated_at,
                    start_time=strategy.start_time,
                    stop_time=strategy.stop_time,
                    last_run_time=strategy.last_run_time,
                )
                session.add(strategy_model)

    def find_by_id(self, strategy_id: str) -> Optional[Strategy]:
        """根据ID查找策略"""
        with self._db_manager.session() as session:
            strategy_model = (
                session.query(StrategyModel)
                .filter(StrategyModel.id == strategy_id)
                .first()
            )
            if not strategy_model:
                return None
            return self._to_domain_entity(strategy_model, session)

    def find_all(self) -> List[Strategy]:
        """查找所有策略"""
        with self._db_manager.session() as session:
            strategy_models = session.query(StrategyModel).all()
            return [self._to_domain_entity(model, session) for model in strategy_models]

    def find_by_status(self, status: StrategyStatus) -> List[Strategy]:
        """根据状态查找策略"""
        with self._db_manager.session() as session:
            strategy_models = (
                session.query(StrategyModel)
                .filter(StrategyModel.status == self._map_strategy_status(status))
                .all()
            )
            return [self._to_domain_entity(model, session) for model in strategy_models]

    def find_by_exchange_id(self, exchange_id: str) -> List[Strategy]:
        """根据交易所ID查找策略"""
        with self._db_manager.session() as session:
            # 这里需要查询JSON字段，不同数据库实现可能不同
            # 这里使用简单的模糊匹配，实际使用时可能需要更精确的查询
            strategy_models = (
                session.query(StrategyModel)
                .filter(StrategyModel.exchange_ids.like(f'%"{exchange_id}"%'))
                .all()
            )

            # 过滤结果，确保exchange_id在exchange_ids列表中
            result = []
            for model in strategy_models:
                exchange_ids = json.loads(model.exchange_ids)
                if exchange_id in exchange_ids:
                    result.append(self._to_domain_entity(model, session))

            return result

    def find_by_symbol(self, symbol: str) -> List[Strategy]:
        """根据交易对查找策略"""
        with self._db_manager.session() as session:
            # 这里需要查询JSON字段，不同数据库实现可能不同
            # 这里使用简单的模糊匹配，实际使用时可能需要更精确的查询
            strategy_models = (
                session.query(StrategyModel)
                .filter(StrategyModel.symbols.like(f'%"{symbol}"%'))
                .all()
            )

            # 过滤结果，确保symbol在symbols列表中
            result = []
            for model in strategy_models:
                symbols = json.loads(model.symbols)
                if symbol in symbols:
                    result.append(self._to_domain_entity(model, session))

            return result

    def delete(self, strategy_id: str) -> bool:
        """删除策略"""
        with self._db_manager.session() as session:
            strategy_model = (
                session.query(StrategyModel)
                .filter(StrategyModel.id == strategy_id)
                .first()
            )
            if not strategy_model:
                return False
            session.delete(strategy_model)
            return True

    def _to_domain_entity(self, model: StrategyModel, session: Session) -> Strategy:
        """将数据库模型转换为领域实体"""
        # 创建策略配置
        config = StrategyConfig(
            name=model.name,
            symbols=json.loads(model.symbols),
            exchange_ids=json.loads(model.exchange_ids),
            timeframes=json.loads(model.timeframes),
            params=json.loads(model.config) if model.config else {},
        )

        # 创建策略实体
        strategy = Strategy(config=config, entity_id=model.id)

        # 设置策略属性
        strategy._status = self._map_to_strategy_status(model.status)
        strategy._performance_metrics = (
            json.loads(model.performance_metrics) if model.performance_metrics else {}
        )
        strategy._error_message = model.error_message
        strategy._created_at = model.created_at
        strategy._updated_at = model.updated_at
        strategy._start_time = model.start_time
        strategy._stop_time = model.stop_time
        strategy._last_run_time = model.last_run_time

        # 获取策略关联的订单ID
        order_ids = set()
        for order in model.orders:
            order_ids.add(order.id)
        strategy._order_ids = order_ids

        return strategy

    def _map_strategy_status(self, status: StrategyStatus) -> StrategyStatusEnum:
        """将领域枚举映射为数据库枚举"""
        mapping = {
            StrategyStatus.CREATED: StrategyStatusEnum.CREATED,
            StrategyStatus.RUNNING: StrategyStatusEnum.RUNNING,
            StrategyStatus.PAUSED: StrategyStatusEnum.PAUSED,
            StrategyStatus.STOPPED: StrategyStatusEnum.STOPPED,
            StrategyStatus.ERROR: StrategyStatusEnum.ERROR,
        }
        return mapping.get(status, StrategyStatusEnum.CREATED)

    def _map_to_strategy_status(self, status: StrategyStatusEnum) -> StrategyStatus:
        """将数据库枚举映射为领域枚举"""
        mapping = {
            StrategyStatusEnum.CREATED: StrategyStatus.CREATED,
            StrategyStatusEnum.RUNNING: StrategyStatus.RUNNING,
            StrategyStatusEnum.PAUSED: StrategyStatus.PAUSED,
            StrategyStatusEnum.STOPPED: StrategyStatus.STOPPED,
            StrategyStatusEnum.ERROR: StrategyStatus.ERROR,
        }
        return mapping.get(status, StrategyStatus.CREATED)
