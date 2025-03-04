"""
策略引擎，负责策略的加载、运行和管理
"""

import importlib
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from ..models.market_data import Candle, OrderBook, Ticker
from ..models.order import Order
from ..models.strategy import Strategy, StrategyConfig, StrategyStatus
from ..repositories.account_repository import AccountRepository
from ..risk_management import RiskManager
from ..services.market_data_service import MarketDataService
from ..services.order_service import OrderService
from ..services.strategy_service import StrategyService
from .base_strategy import BaseStrategy
from .strategy_context import StrategyContext
from .strategy_result import StrategyResult

logger = logging.getLogger(__name__)


class StrategyEngine:
    """
    策略引擎，负责策略的加载、运行和管理

    策略引擎功能：
    1. 加载策略：从配置加载策略类
    2. 初始化策略：创建策略实例并初始化
    3. 运行策略：处理市场数据并执行策略逻辑
    4. 管理策略：启动、暂停、恢复、停止策略
    5. 处理订单更新：将订单更新传递给策略
    6. 风险管理：在执行订单前进行风险检查
    """

    def __init__(
        self,
        strategy_service: StrategyService,
        order_service: OrderService,
        market_data_service: MarketDataService,
        account_repository: AccountRepository,
    ):
        """
        初始化策略引擎

        Args:
            strategy_service: 策略服务
            order_service: 订单服务
            market_data_service: 市场数据服务
            account_repository: 账户仓库
        """
        self.strategy_service = strategy_service
        self.order_service = order_service
        self.market_data_service = market_data_service
        self.account_repository = account_repository

        # 策略实例映射表：策略ID -> 策略实例
        self.strategy_instances: Dict[str, BaseStrategy] = {}

        # 策略上下文映射表：策略ID -> 策略上下文
        self.strategy_contexts: Dict[str, StrategyContext] = {}

        # 策略类映射表：策略类名 -> 策略类
        self.strategy_classes: Dict[str, Type[BaseStrategy]] = {}

        # 风险管理器映射表：策略ID -> 风险管理器
        self.risk_managers: Dict[str, RiskManager] = {}

        # 是否正在运行
        self.is_running = False

    def register_strategy_class(self, strategy_class: Type[BaseStrategy]) -> None:
        """
        注册策略类

        Args:
            strategy_class: 策略类
        """
        class_name = strategy_class.__name__
        self.strategy_classes[class_name] = strategy_class
        logger.info(f"注册策略类: {class_name}")

    def load_strategy_class(
        self, module_path: str, class_name: str
    ) -> Optional[Type[BaseStrategy]]:
        """
        从模块加载策略类

        Args:
            module_path: 模块路径
            class_name: 类名

        Returns:
            策略类，如果加载失败则返回None
        """
        try:
            module = importlib.import_module(module_path)
            strategy_class = getattr(module, class_name)

            # 检查是否是BaseStrategy的子类
            if not issubclass(strategy_class, BaseStrategy):
                logger.error(f"类 {class_name} 不是BaseStrategy的子类")
                return None

            self.register_strategy_class(strategy_class)
            return strategy_class

        except (ImportError, AttributeError) as e:
            logger.error(f"加载策略类失败: {e}")
            return None

    def create_strategy(
        self, strategy_class: Type[BaseStrategy], config: StrategyConfig
    ) -> Optional[str]:
        """
        创建策略

        Args:
            strategy_class: 策略类
            config: 策略配置

        Returns:
            策略ID，如果创建失败则返回None
        """
        try:
            # 创建领域模型
            strategy = self.strategy_service.create_strategy(config)

            # 创建策略实例
            strategy_instance = strategy_class(config)

            # 获取账户
            account = None
            if config.exchange_ids:
                account = self.account_repository.find_by_exchange_id(
                    config.exchange_ids[0]
                )

            if not account:
                logger.error(f"找不到交易所账户: {config.exchange_ids}")
                return None

            # 创建风险管理器
            risk_manager = RiskManager()
            self.risk_managers[strategy.id] = risk_manager

            # 创建策略上下文
            context = StrategyContext(
                strategy_id=strategy.id,
                order_service=self.order_service,
                market_data_service=self.market_data_service,
                account=account,
                risk_manager=risk_manager,
            )

            # 设置上下文
            strategy_instance.set_context(context)

            # 保存策略实例和上下文
            self.strategy_instances[strategy.id] = strategy_instance
            self.strategy_contexts[strategy.id] = context

            logger.info(f"创建策略: {strategy.id}, 名称: {config.name}")
            return strategy.id

        except Exception as e:
            logger.error(f"创建策略失败: {e}")
            return None

    def initialize_strategy(self, strategy_id: str) -> bool:
        """
        初始化策略

        Args:
            strategy_id: 策略ID

        Returns:
            是否成功初始化
        """
        if strategy_id not in self.strategy_instances:
            logger.error(f"找不到策略实例: {strategy_id}")
            return False

        try:
            strategy_instance = self.strategy_instances[strategy_id]
            strategy_instance.initialize()
            strategy_instance.is_initialized = True

            logger.info(f"初始化策略: {strategy_id}")
            return True

        except Exception as e:
            logger.error(f"初始化策略失败: {strategy_id}, 错误: {e}")

            # 设置策略错误状态
            self.strategy_service.update_strategy_status(
                strategy_id=strategy_id,
                status=StrategyStatus.ERROR,
                error_message=str(e),
            )

            return False

    def start_strategy(self, strategy_id: str) -> bool:
        """
        启动策略

        Args:
            strategy_id: 策略ID

        Returns:
            是否成功启动
        """
        if strategy_id not in self.strategy_instances:
            logger.error(f"找不到策略实例: {strategy_id}")
            return False

        # 获取策略领域模型
        strategy = self.strategy_service.get_strategy(strategy_id)
        if not strategy:
            logger.error(f"找不到策略: {strategy_id}")
            return False

        # 初始化策略
        if not self.strategy_instances[strategy_id].is_initialized:
            if not self.initialize_strategy(strategy_id):
                return False

        # 启动策略
        result = self.strategy_service.start_strategy(strategy_id)
        if result:
            logger.info(f"启动策略: {strategy_id}")

        return result

    def pause_strategy(self, strategy_id: str) -> bool:
        """
        暂停策略

        Args:
            strategy_id: 策略ID

        Returns:
            是否成功暂停
        """
        result = self.strategy_service.pause_strategy(strategy_id)
        if result:
            logger.info(f"暂停策略: {strategy_id}")

        return result

    def resume_strategy(self, strategy_id: str) -> bool:
        """
        恢复策略

        Args:
            strategy_id: 策略ID

        Returns:
            是否成功恢复
        """
        result = self.strategy_service.resume_strategy(strategy_id)
        if result:
            logger.info(f"恢复策略: {strategy_id}")

        return result

    def stop_strategy(self, strategy_id: str) -> bool:
        """
        停止策略

        Args:
            strategy_id: 策略ID

        Returns:
            是否成功停止
        """
        if strategy_id not in self.strategy_instances:
            logger.error(f"找不到策略实例: {strategy_id}")
            return False

        try:
            # 清理资源
            self.strategy_instances[strategy_id].cleanup()

            # 停止策略
            result = self.strategy_service.stop_strategy(strategy_id)
            if result:
                logger.info(f"停止策略: {strategy_id}")

            return result

        except Exception as e:
            logger.error(f"停止策略失败: {strategy_id}, 错误: {e}")
            return False

    def process_candle(self, candle: Candle) -> None:
        """
        处理K线数据

        Args:
            candle: K线数据
        """
        if not self.is_running:
            return

        # 遍历所有策略
        for strategy_id, strategy in self.strategy_instances.items():
            # 检查策略是否已暂停
            strategy_status = self.strategy_service.get_strategy_status(strategy_id)
            if strategy_status != StrategyStatus.RUNNING:
                continue

            # 检查策略是否订阅了该交易对和时间周期
            config = strategy.config
            if (
                candle.symbol not in config.symbols
                or candle.timeframe not in config.timeframes
            ):
                continue

            # 获取策略上下文
            context = self.strategy_contexts.get(strategy_id)
            if not context:
                continue

            # 更新风险管理器上下文
            if strategy_id in self.risk_managers:
                risk_manager = self.risk_managers[strategy_id]
                # 更新市场数据
                ticker_context = {"ticker": {candle.symbol: {"last": candle.close}}}
                risk_manager.update_context(ticker_context)

            # 调用策略的on_candle方法
            try:
                result = strategy.on_candle(candle)
                if result:
                    self._process_strategy_result(strategy_id, result)
            except Exception as e:
                logger.error(f"策略 {strategy_id} 处理K线时发生错误: {e}")
                # 可以选择暂停策略
                # self.pause_strategy(strategy_id)

    def process_ticker(self, ticker: Ticker) -> None:
        """
        处理Ticker数据

        Args:
            ticker: Ticker数据
        """
        # 获取所有运行中的策略
        running_strategies = self.strategy_service.get_strategies_by_status(
            StrategyStatus.RUNNING
        )

        for strategy in running_strategies:
            # 检查策略是否关注该交易对
            if (
                ticker.symbol in strategy.config.symbols
                and strategy.id in self.strategy_instances
            ):

                try:
                    # 更新上下文
                    context = self.strategy_contexts[strategy.id]
                    context.update_ticker(ticker)
                    context.update_current_time(ticker.timestamp)

                    # 执行策略
                    strategy_instance = self.strategy_instances[strategy.id]
                    result = strategy_instance.on_ticker(ticker)

                    # 处理结果
                    self._process_strategy_result(strategy.id, result)

                except Exception as e:
                    logger.error(f"处理Ticker数据失败: 策略ID={strategy.id}, 错误: {e}")

    def process_orderbook(self, orderbook: OrderBook) -> None:
        """
        处理订单簿数据

        Args:
            orderbook: 订单簿数据
        """
        # 获取所有运行中的策略
        running_strategies = self.strategy_service.get_strategies_by_status(
            StrategyStatus.RUNNING
        )

        for strategy in running_strategies:
            # 检查策略是否关注该交易对
            if (
                orderbook.symbol in strategy.config.symbols
                and strategy.id in self.strategy_instances
            ):

                try:
                    # 更新上下文
                    context = self.strategy_contexts[strategy.id]
                    context.update_orderbook(orderbook)
                    context.update_current_time(orderbook.timestamp)

                    # 执行策略
                    strategy_instance = self.strategy_instances[strategy.id]
                    result = strategy_instance.on_orderbook(orderbook)

                    # 处理结果
                    self._process_strategy_result(strategy.id, result)

                except Exception as e:
                    logger.error(f"处理订单簿数据失败: 策略ID={strategy.id}, 错误: {e}")

    def process_order_update(self, order: Order) -> None:
        """
        处理订单更新

        Args:
            order: 订单对象
        """
        # 获取策略ID
        strategy_id = order.strategy_id

        if not strategy_id:
            return

        if strategy_id in self.strategy_instances:
            try:
                # 更新上下文
                context = self.strategy_contexts[strategy_id]
                context.update_order(order)

                # 通知策略
                strategy_instance = self.strategy_instances[strategy_id]
                strategy_instance.on_order_update(order)

                # 更新策略订单
                self.strategy_service.add_order_to_strategy(strategy_id, order.id)

            except Exception as e:
                logger.error(
                    f"处理订单更新失败: 策略ID={strategy_id}, 订单ID={order.id}, 错误: {e}"
                )

    def _process_strategy_result(
        self, strategy_id: str, result: StrategyResult
    ) -> None:
        """
        处理策略执行结果

        Args:
            strategy_id: 策略ID
            result: 策略执行结果
        """
        if not result:
            return

        # 获取账户和风险管理器
        context = self.strategy_contexts.get(strategy_id)
        if not context:
            logger.error(f"找不到策略上下文: {strategy_id}")
            return

        account = context.account
        risk_manager = self.risk_managers.get(strategy_id)

        # 处理订单
        for order in result.orders:
            # 进行风险检查
            if risk_manager and not risk_manager.check_order(order, account):
                logger.warning(
                    f"订单被风险管理器拒绝: 策略ID={strategy_id}, 订单ID={order.id}"
                )
                # 添加拒绝信息到结果日志
                result.add_log(f"订单被风险管理器拒绝: {order.id}")
                continue

            # 提交订单到订单服务
            try:
                # 确保订单有策略ID
                if not order.strategy_id:
                    logger.warning(f"订单没有策略ID，设置为当前策略: {strategy_id}")
                    # 这里可能需要创建新的订单对象，因为strategy_id可能是只读的

                # 提交订单
                submitted_order = self.order_service.submit_order(order)
                if submitted_order:
                    # 添加订单到策略
                    self.strategy_service.add_order_to_strategy(
                        strategy_id, submitted_order.id
                    )
                    logger.info(
                        f"订单已提交: 策略ID={strategy_id}, 订单ID={submitted_order.id}"
                    )
                else:
                    logger.error(
                        f"提交订单失败: 策略ID={strategy_id}, 订单ID={order.id}"
                    )
            except Exception as e:
                logger.error(
                    f"处理订单时发生错误: 策略ID={strategy_id}, 订单ID={order.id}, 错误: {e}"
                )

        # 处理取消的订单
        for order_id in result.canceled_order_ids:
            try:
                # 取消订单
                if self.order_service.cancel_order(order_id):
                    # 从策略中移除订单
                    self.strategy_service.remove_order_from_strategy(
                        strategy_id, order_id
                    )
                    logger.info(f"订单已取消: 策略ID={strategy_id}, 订单ID={order_id}")
                else:
                    logger.error(
                        f"取消订单失败: 策略ID={strategy_id}, 订单ID={order_id}"
                    )
            except Exception as e:
                logger.error(
                    f"取消订单时发生错误: 策略ID={strategy_id}, 订单ID={order_id}, 错误: {e}"
                )

        # 处理性能指标
        if result.metrics:
            self.strategy_service.update_strategy_performance(
                strategy_id, result.metrics
            )

            # 更新风险管理器上下文
            if risk_manager:
                risk_manager.update_context(result.metrics)

        # 处理日志
        for log in result.logs:
            logger.info(f"策略日志: 策略ID={strategy_id}, {log}")

        # 处理错误
        if result.has_error:
            logger.error(
                f"策略错误: 策略ID={strategy_id}, 错误: {result.error_message}"
            )

            # 设置策略错误状态
            self.strategy_service.update_strategy_status(
                strategy_id=strategy_id,
                status=StrategyStatus.ERROR,
                error_message=result.error_message,
            )

    def start(self) -> None:
        """
        启动策略引擎
        """
        if self.is_running:
            logger.warning("策略引擎已经在运行")
            return

        self.is_running = True
        logger.info("启动策略引擎")

        # 启动所有应该运行的策略
        running_strategies = self.strategy_service.get_strategies_by_status(
            StrategyStatus.RUNNING
        )
        for strategy in running_strategies:
            if strategy.id not in self.strategy_instances:
                logger.warning(f"策略 {strategy.id} 应该运行，但找不到实例")
                continue

            if not self.strategy_instances[strategy.id].is_initialized:
                self.initialize_strategy(strategy.id)

    def stop(self) -> None:
        """
        停止策略引擎
        """
        if not self.is_running:
            logger.warning("策略引擎已经停止")
            return

        self.is_running = False
        logger.info("停止策略引擎")

        # 停止所有运行中的策略
        running_strategies = self.strategy_service.get_strategies_by_status(
            StrategyStatus.RUNNING
        )
        for strategy in running_strategies:
            self.stop_strategy(strategy.id)
