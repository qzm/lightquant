"""
回测引擎，用于在历史数据上测试策略
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Type, Any, Tuple

from ..models.strategy import Strategy, StrategyConfig, StrategyStatus
from ..models.market_data import Candle, Ticker, OrderBook
from ..models.order import Order, OrderType, OrderSide, OrderStatus
from ..models.account import Account, Balance
from ..services.strategy_service import StrategyService
from ..services.order_service import OrderService
from ..services.market_data_service import MarketDataService
from ..repositories.account_repository import AccountRepository
from ..risk_management import RiskManager
from .base_strategy import BaseStrategy
from .strategy_context import StrategyContext
from .strategy_result import StrategyResult


logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    回测引擎，用于在历史数据上测试策略

    回测引擎功能：
    1. 加载历史数据
    2. 模拟策略执行
    3. 模拟订单执行
    4. 计算回测结果
    5. 生成回测报告
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
        初始化回测引擎

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

        # 策略实例
        self.strategy_instance: Optional[BaseStrategy] = None
        self.strategy_context: Optional[StrategyContext] = None
        self.strategy_id: Optional[str] = None

        # 回测参数
        self.initial_capital = 100000.0  # 初始资金
        self.commission_rate = 0.001  # 手续费率
        self.slippage = 0.0  # 滑点

        # 策略实例映射表：策略ID -> 策略实例
        self.strategy_instances: Dict[str, BaseStrategy] = {}

        # 策略上下文映射表：策略ID -> 策略上下文
        self.strategy_contexts: Dict[str, StrategyContext] = {}

        # 策略类映射表：策略类名 -> 策略类
        self.strategy_classes: Dict[str, Type[BaseStrategy]] = {}

        # 回测数据
        self.account: Optional[Account] = None
        self.orders: List[Order] = []
        self.candles: Dict[str, Dict[str, List[Candle]]] = (
            {}
        )  # symbol -> timeframe -> candles
        self.tickers: Dict[str, List[Ticker]] = {}  # symbol -> tickers
        self.orderbooks: Dict[str, List[OrderBook]] = {}  # symbol -> orderbooks

        # 回测结果
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.account_snapshots: List[Tuple[datetime, Dict[str, float]]] = (
            []
        )  # (timestamp, balances)
        self.performance_metrics: Dict[str, Any] = {}

        # 回测状态
        self.is_running = False
        self.current_time: datetime = datetime.utcnow()

        # 风险管理器
        self.risk_manager: Optional[RiskManager] = None

    def register_strategy_class(self, strategy_class: Type[BaseStrategy]) -> None:
        """
        注册策略类

        Args:
            strategy_class: 策略类
        """
        class_name = strategy_class.__name__
        self.strategy_classes[class_name] = strategy_class
        logger.info(f"注册策略类: {class_name}")

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

            # 创建回测账户
            self.account = self._create_backtest_account(
                config.exchange_ids[0] if config.exchange_ids else "backtest"
            )

            # 创建风险管理器
            self.risk_manager = RiskManager()

            # 创建策略上下文
            self.strategy_context = StrategyContext(
                strategy_id=strategy.id,
                order_service=self.order_service,
                market_data_service=self.market_data_service,
                account=self.account,
                risk_manager=self.risk_manager,
                is_backtest=True,
            )

            # 创建策略实例
            self.strategy_instance = strategy_class(config)
            self.strategy_instance.set_context(self.strategy_context)

            # 保存策略ID
            self.strategy_id = strategy.id

            logger.info(f"创建回测策略: {strategy.id}, 名称: {config.name}")
            return strategy.id

        except Exception as e:
            logger.error(f"创建回测策略失败: {e}")
            return None

    def _create_backtest_account(self, exchange_id: str) -> Account:
        """
        创建回测账户

        Args:
            exchange_id: 交易所ID

        Returns:
            账户对象
        """
        # 创建初始余额
        balances = {
            "USDT": Balance(
                currency="USDT",
                free=self.initial_capital,
                used=0.0,
                total=self.initial_capital,
            )
        }

        # 创建账户
        account = Account(exchange_id=exchange_id, balances=balances)

        return account

    def load_candles(
        self, symbol: str, timeframe: str, start_time: datetime, end_time: datetime
    ) -> List[Candle]:
        """
        加载K线数据

        Args:
            symbol: 交易对
            timeframe: 时间周期
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            K线数据列表
        """
        candles = self.market_data_service.get_historical_candles(
            symbol=symbol, timeframe=timeframe, since=start_time, until=end_time
        )

        if symbol not in self.candles:
            self.candles[symbol] = {}

        self.candles[symbol][timeframe] = candles

        logger.info(f"加载K线数据: {symbol} {timeframe}, 数量: {len(candles)}")
        return candles

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
            return False

    def _process_order(self, order: Order, candle: Candle) -> None:
        """
        处理订单（模拟成交）

        Args:
            order: 订单对象
            candle: 当前K线
        """
        if not self.account:
            return

        # 进行风险检查
        if self.risk_manager and not self.risk_manager.check_order(order, self.account):
            logger.warning(f"订单被风险管理器拒绝: 订单ID={order.id}")
            order.reject("风险控制规则拒绝")
            return

        # 只处理未成交的订单
        if (
            order.status != OrderStatus.OPEN
            and order.status != OrderStatus.PARTIALLY_FILLED
        ):
            return

        # 获取策略上下文
        context = self.strategy_contexts.get(order.strategy_id)
        if not context:
            return

        # 获取账户
        account = context.account

        # 计算执行价格（考虑滑点）
        execution_price = candle.close
        if order.side == OrderSide.BUY:
            execution_price *= 1 + self.slippage
        else:
            execution_price *= 1 - self.slippage

        # 计算手续费
        fee = order.amount * execution_price * self.commission_rate

        # 更新订单状态
        order.fill(
            price=execution_price, filled=order.amount, fee=fee, fee_currency="USDT"
        )

        # 更新账户余额
        base_currency, quote_currency = order.symbol.split("/")

        if order.side == OrderSide.BUY:
            # 买入：减少计价货币，增加基础货币
            if quote_currency in account.balances:
                account.balances[quote_currency].free -= (
                    order.amount * execution_price + fee
                )
                account.balances[quote_currency].total -= (
                    order.amount * execution_price + fee
                )

            if base_currency not in account.balances:
                account.balances[base_currency] = Balance(
                    currency=base_currency, free=0.0, used=0.0, total=0.0
                )

            account.balances[base_currency].free += order.amount
            account.balances[base_currency].total += order.amount

        else:
            # 卖出：减少基础货币，增加计价货币
            if base_currency in account.balances:
                account.balances[base_currency].free -= order.amount
                account.balances[base_currency].total -= order.amount

            if quote_currency not in account.balances:
                account.balances[quote_currency] = Balance(
                    currency=quote_currency, free=0.0, used=0.0, total=0.0
                )

            account.balances[quote_currency].free += (
                order.amount * execution_price - fee
            )
            account.balances[quote_currency].total += (
                order.amount * execution_price - fee
            )

        # 添加到订单列表
        self.orders.append(order)

        logger.info(
            f"执行订单: {order.id}, 价格: {execution_price}, 数量: {order.amount}, 手续费: {fee}"
        )

    def _update_account_snapshot(self, timestamp: datetime) -> None:
        """
        更新账户快照

        Args:
            timestamp: 时间戳
        """
        # 获取第一个策略的上下文
        if not self.strategy_contexts:
            return

        context = next(iter(self.strategy_contexts.values()))
        account = context.account

        # 创建余额快照
        balances = {}
        for currency, balance in account.balances.items():
            balances[currency] = balance.total

        # 添加到快照列表
        self.account_snapshots.append((timestamp, balances))

        # 计算总权益
        equity = 0.0
        for currency, amount in balances.items():
            if currency == "USDT":
                equity += amount
            else:
                # 获取最新价格
                symbol = f"{currency}/USDT"
                if symbol in self.candles and "1h" in self.candles[symbol]:
                    candles = self.candles[symbol]["1h"]
                    if candles:
                        latest_price = candles[-1].close
                        equity += amount * latest_price

        # 添加到权益曲线
        self.equity_curve.append((timestamp, equity))

    def run_backtest(
        self, strategy_id: str, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """
        运行回测

        Args:
            strategy_id: 策略ID
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            回测结果
        """
        if strategy_id not in self.strategy_instances:
            logger.error(f"找不到策略实例: {strategy_id}")
            return {}

        # 获取策略
        strategy = self.strategy_service.get_strategy(strategy_id)
        if not strategy:
            logger.error(f"找不到策略: {strategy_id}")
            return {}

        # 获取策略实例和上下文
        strategy_instance = self.strategy_instances[strategy_id]
        context = self.strategy_contexts[strategy_id]

        # 初始化策略
        if not strategy_instance.is_initialized:
            if not self.initialize_strategy(strategy_id):
                return {}

        # 设置回测状态
        self.is_running = True
        self.current_time = start_time

        # 清空回测结果
        self.orders = []
        self.account_snapshots = []
        self.equity_curve = []

        # 获取所有交易对和时间周期
        symbols = strategy.config.symbols
        timeframes = strategy.config.timeframes

        # 加载所有K线数据
        for symbol in symbols:
            for timeframe in timeframes:
                if symbol not in self.candles or timeframe not in self.candles[symbol]:
                    self.load_candles(symbol, timeframe, start_time, end_time)

        # 按时间排序所有K线
        all_candles = []
        for symbol in symbols:
            for timeframe in timeframes:
                if symbol in self.candles and timeframe in self.candles[symbol]:
                    for candle in self.candles[symbol][timeframe]:
                        all_candles.append(candle)

        all_candles.sort(key=lambda c: c.timestamp)

        # 初始化账户快照
        self._update_account_snapshot(start_time)

        # 遍历所有K线
        for candle in all_candles:
            # 更新当前时间
            self.current_time = candle.timestamp
            context.update_current_time(self.current_time)

            # 更新风险管理器上下文
            if self.risk_manager:
                ticker_context = {"ticker": {candle.symbol: {"last": candle.close}}}
                self.risk_manager.update_context(ticker_context)

            # 处理未完成的订单
            for order_id, order in list(context.orders.items()):
                if order.status == OrderStatus.OPEN:
                    self._process_order(order, candle)

            # 处理K线
            try:
                # 更新上下文
                context.update_candle(candle)

                # 执行策略
                result = strategy_instance.on_candle(candle)

                # 处理新订单
                for order in result.orders:
                    self._process_order(order, candle)

                # 更新账户快照
                self._update_account_snapshot(candle.timestamp)

            except Exception as e:
                logger.error(f"处理K线数据失败: 策略ID={strategy_id}, 错误: {e}")
                break

        # 计算性能指标
        performance_metrics = self._calculate_performance_metrics()

        # 更新策略性能指标
        self.strategy_service.update_strategy_performance(
            strategy_id, performance_metrics
        )

        # 设置回测状态
        self.is_running = False

        logger.info(
            f"回测完成: 策略ID={strategy_id}, 开始时间={start_time}, 结束时间={end_time}"
        )

        # 返回回测结果
        return {
            "strategy_id": strategy_id,
            "start_time": start_time,
            "end_time": end_time,
            "orders": self.orders,
            "equity_curve": self.equity_curve,
            "performance_metrics": performance_metrics,
        }

    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """
        计算性能指标

        Returns:
            性能指标字典
        """
        if not self.equity_curve:
            return {}

        # 提取权益数据
        timestamps = [t for t, _ in self.equity_curve]
        equity_values = [e for _, e in self.equity_curve]

        # 计算收益率
        initial_equity = equity_values[0]
        final_equity = equity_values[-1]
        total_return = (final_equity - initial_equity) / initial_equity

        # 计算年化收益率
        days = (timestamps[-1] - timestamps[0]).days
        if days > 0:
            annual_return = (1 + total_return) ** (365 / days) - 1
        else:
            annual_return = 0.0

        # 计算最大回撤
        max_drawdown = 0.0
        peak_value = equity_values[0]

        for equity in equity_values:
            if equity > peak_value:
                peak_value = equity
            else:
                drawdown = (peak_value - equity) / peak_value
                max_drawdown = max(max_drawdown, drawdown)

        # 计算夏普比率
        if len(equity_values) > 1:
            # 计算日收益率
            daily_returns = []
            for i in range(1, len(equity_values)):
                daily_return = (
                    equity_values[i] - equity_values[i - 1]
                ) / equity_values[i - 1]
                daily_returns.append(daily_return)

            # 计算平均收益率和标准差
            avg_return = sum(daily_returns) / len(daily_returns)
            std_return = (
                sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns)
            ) ** 0.5

            # 计算夏普比率（假设无风险利率为0）
            if std_return > 0:
                sharpe_ratio = (avg_return / std_return) * (
                    252**0.5
                )  # 假设一年252个交易日
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0

        # 计算交易统计
        total_trades = len(self.orders)
        winning_trades = sum(1 for order in self.orders if order.realized_pnl > 0)
        losing_trades = sum(1 for order in self.orders if order.realized_pnl < 0)

        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0

        # 计算平均盈亏比
        avg_profit = (
            sum(order.realized_pnl for order in self.orders if order.realized_pnl > 0)
            / winning_trades
            if winning_trades > 0
            else 0.0
        )
        avg_loss = (
            sum(
                abs(order.realized_pnl)
                for order in self.orders
                if order.realized_pnl < 0
            )
            / losing_trades
            if losing_trades > 0
            else 0.0
        )

        profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else 0.0

        return {
            "initial_capital": initial_equity,
            "final_equity": final_equity,
            "total_return": total_return,
            "annual_return": annual_return,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "profit_loss_ratio": profit_loss_ratio,
        }

    def get_equity_curve(self) -> List[Tuple[datetime, float]]:
        """
        获取权益曲线

        Returns:
            权益曲线数据
        """
        return self.equity_curve

    def get_orders(self) -> List[Order]:
        """
        获取所有订单

        Returns:
            订单列表
        """
        return self.orders

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标

        Returns:
            性能指标字典
        """
        return self._calculate_performance_metrics()

    def set_initial_capital(self, capital: float) -> None:
        """
        设置初始资金

        Args:
            capital: 初始资金
        """
        self.initial_capital = capital

    def set_commission_rate(self, rate: float) -> None:
        """
        设置手续费率

        Args:
            rate: 手续费率
        """
        self.commission_rate = rate

    def set_slippage(self, slippage: float) -> None:
        """
        设置滑点

        Args:
            slippage: 滑点
        """
        self.slippage = slippage
