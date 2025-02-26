"""
回测示例，展示如何使用回测引擎
"""

import logging
import time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd

from lightquant.domain.models.strategy import StrategyConfig
from lightquant.domain.models.order import OrderSide
from lightquant.domain.models.market_data import Candle
from lightquant.domain.strategies import BaseStrategy, StrategyResult
from lightquant.domain.services.strategy_service import StrategyService
from lightquant.domain.services.order_service import OrderService
from lightquant.domain.services.market_data_service import MarketDataService
from lightquant.domain.repositories.strategy_repository import StrategyRepository
from lightquant.domain.repositories.order_repository import OrderRepository
from lightquant.domain.repositories.account_repository import AccountRepository
from lightquant.domain.repositories.market_data_repository import MarketDataRepository
from lightquant.domain.strategies.backtest_engine import BacktestEngine
from lightquant.infrastructure.database import DatabaseManager, init_db
from lightquant.infrastructure.database.repositories import (
    SQLStrategyRepository,
    SQLOrderRepository,
    SQLAccountRepository,
    SQLMarketDataRepository,
)


# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SimpleMovingAverageStrategy(BaseStrategy):
    """
    简单移动平均线策略

    策略逻辑：
    1. 计算短期和长期移动平均线
    2. 当短期均线上穿长期均线时买入
    3. 当短期均线下穿长期均线时卖出
    """

    def initialize(self) -> None:
        """初始化策略"""
        # 获取策略参数
        self.symbol = self.config.symbols[0]  # 交易对
        self.short_window = self.parameters.get("short_window", 5)  # 短期窗口
        self.long_window = self.parameters.get("long_window", 20)  # 长期窗口

        # 获取历史数据
        self.candles = self.context.get_historical_candles(
            symbol=self.symbol, timeframe="1h", limit=self.long_window + 10
        )

        # 初始化指标
        self.short_ma = 0
        self.long_ma = 0
        self.position = 0  # 持仓状态：1表示多头，-1表示空头，0表示无持仓

        logger.info(
            f"初始化策略: {self.config.name}, 交易对: {self.symbol}, "
            f"短期窗口: {self.short_window}, 长期窗口: {self.long_window}"
        )

    def on_candle(self, candle: Candle) -> StrategyResult:
        """处理K线数据"""
        result = StrategyResult()

        # 添加新K线
        self.candles.append(candle)

        # 保持固定长度
        if len(self.candles) > self.long_window + 10:
            self.candles = self.candles[-(self.long_window + 10) :]

        # 如果数据不足，则返回
        if len(self.candles) < self.long_window:
            result.add_log(f"数据不足，当前数据长度: {len(self.candles)}")
            return result

        # 计算移动平均线
        closes = [c.close for c in self.candles]
        self.short_ma = sum(closes[-self.short_window :]) / self.short_window
        self.long_ma = sum(closes[-self.long_window :]) / self.long_window

        # 添加指标到结果
        result.add_metric("short_ma", self.short_ma)
        result.add_metric("long_ma", self.long_ma)

        # 获取前一个状态
        prev_short_ma = sum(closes[-(self.short_window + 1) : -1]) / self.short_window
        prev_long_ma = sum(closes[-(self.long_window + 1) : -1]) / self.long_window

        # 交易逻辑
        # 短期均线上穿长期均线
        if prev_short_ma <= prev_long_ma and self.short_ma > self.long_ma:
            if self.position <= 0:  # 如果没有多头持仓或者有空头持仓
                # 平空仓
                if self.position < 0:
                    result.add_log(
                        f"平空仓信号: 短期MA({self.short_ma:.2f}) 上穿 长期MA({self.long_ma:.2f})"
                    )

                # 开多仓
                result.add_log(
                    f"买入信号: 短期MA({self.short_ma:.2f}) 上穿 长期MA({self.long_ma:.2f})"
                )
                order = self.create_market_order(
                    symbol=self.symbol, side=OrderSide.BUY, amount=0.01  # 固定数量
                )

                if order:
                    result.add_order(order)
                    self.position = 1
                    result.add_log(f"创建买入订单: {order.id}")
                else:
                    result.set_error("创建买入订单失败")

        # 短期均线下穿长期均线
        elif prev_short_ma >= prev_long_ma and self.short_ma < self.long_ma:
            if self.position >= 0:  # 如果没有空头持仓或者有多头持仓
                # 平多仓
                if self.position > 0:
                    result.add_log(
                        f"平多仓信号: 短期MA({self.short_ma:.2f}) 下穿 长期MA({self.long_ma:.2f})"
                    )

                # 开空仓
                result.add_log(
                    f"卖出信号: 短期MA({self.short_ma:.2f}) 下穿 长期MA({self.long_ma:.2f})"
                )
                order = self.create_market_order(
                    symbol=self.symbol, side=OrderSide.SELL, amount=0.01  # 固定数量
                )

                if order:
                    result.add_order(order)
                    self.position = -1
                    result.add_log(f"创建卖出订单: {order.id}")
                else:
                    result.set_error("创建卖出订单失败")

        return result


def generate_mock_candles(
    symbol: str,
    timeframe: str,
    start_time: datetime,
    end_time: datetime,
    interval_minutes: int = 60,
) -> List[Candle]:
    """
    生成模拟K线数据

    Args:
        symbol: 交易对
        timeframe: 时间周期
        start_time: 开始时间
        end_time: 结束时间
        interval_minutes: 时间间隔（分钟）

    Returns:
        K线数据列表
    """
    candles = []
    current_time = start_time
    price = 10000.0

    while current_time <= end_time:
        # 生成随机价格波动
        price_change = price * 0.01 * (0.5 - 0.5 * (current_time.hour % 4 == 0))

        # 创建K线
        candle = Candle(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=current_time,
            open=price,
            high=price + price * 0.005,
            low=price - price * 0.005,
            close=price + price_change,
            volume=1.0 + 0.1 * (current_time.hour % 12),
        )

        candles.append(candle)

        # 更新价格和时间
        price += price_change
        current_time += timedelta(minutes=interval_minutes)

    return candles


class MockMarketDataService(MarketDataService):
    """
    模拟市场数据服务，用于回测
    """

    def __init__(self, repository: MarketDataRepository):
        super().__init__(repository)
        self.mock_candles = {}  # symbol -> timeframe -> candles

    def add_mock_candles(
        self, symbol: str, timeframe: str, candles: List[Candle]
    ) -> None:
        """
        添加模拟K线数据

        Args:
            symbol: 交易对
            timeframe: 时间周期
            candles: K线数据列表
        """
        if symbol not in self.mock_candles:
            self.mock_candles[symbol] = {}

        self.mock_candles[symbol][timeframe] = candles

    def get_historical_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Candle]:
        """
        获取历史K线数据

        Args:
            symbol: 交易对
            timeframe: 时间周期
            limit: 获取数量
            since: 开始时间
            until: 结束时间

        Returns:
            K线数据列表
        """
        if symbol in self.mock_candles and timeframe in self.mock_candles[symbol]:
            candles = self.mock_candles[symbol][timeframe]

            # 过滤时间范围
            if since:
                candles = [c for c in candles if c.timestamp >= since]

            if until:
                candles = [c for c in candles if c.timestamp <= until]

            # 限制数量
            if limit and len(candles) > limit:
                candles = candles[-limit:]

            return candles

        return []


def plot_backtest_results(backtest_results: Dict[str, Any]) -> None:
    """
    绘制回测结果

    Args:
        backtest_results: 回测结果
    """
    # 提取数据
    equity_curve = backtest_results["equity_curve"]
    orders = backtest_results["orders"]
    metrics = backtest_results["performance_metrics"]

    # 创建时间序列
    timestamps = [t for t, _ in equity_curve]
    equity_values = [e for _, e in equity_curve]

    # 创建DataFrame
    df = pd.DataFrame({"timestamp": timestamps, "equity": equity_values})
    df.set_index("timestamp", inplace=True)

    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 6))

    # 绘制权益曲线
    ax.plot(df.index, df["equity"], label="Equity Curve")

    # 绘制买入点和卖出点
    buy_times = [order.timestamp for order in orders if order.side == OrderSide.BUY]
    buy_prices = [order.price for order in orders if order.side == OrderSide.BUY]

    sell_times = [order.timestamp for order in orders if order.side == OrderSide.SELL]
    sell_prices = [order.price for order in orders if order.side == OrderSide.SELL]

    # 在权益曲线上标记买入点和卖出点
    for i, (time, price) in enumerate(zip(buy_times, buy_prices)):
        # 找到最接近的权益值
        idx = min(
            range(len(timestamps)),
            key=lambda j: abs((timestamps[j] - time).total_seconds()),
        )
        equity = equity_values[idx]
        ax.scatter(time, equity, color="green", marker="^", s=100)

    for i, (time, price) in enumerate(zip(sell_times, sell_prices)):
        # 找到最接近的权益值
        idx = min(
            range(len(timestamps)),
            key=lambda j: abs((timestamps[j] - time).total_seconds()),
        )
        equity = equity_values[idx]
        ax.scatter(time, equity, color="red", marker="v", s=100)

    # 添加性能指标
    info_text = (
        f"Initial Capital: ${metrics['initial_capital']:.2f}\n"
        f"Final Equity: ${metrics['final_equity']:.2f}\n"
        f"Total Return: {metrics['total_return']:.2%}\n"
        f"Annual Return: {metrics['annual_return']:.2%}\n"
        f"Max Drawdown: {metrics['max_drawdown']:.2%}\n"
        f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}\n"
        f"Win Rate: {metrics['win_rate']:.2%}\n"
        f"Total Trades: {metrics['total_trades']}"
    )

    # 在图表右上角添加文本框
    ax.text(
        0.02,
        0.98,
        info_text,
        transform=ax.transAxes,
        verticalalignment="top",
        horizontalalignment="left",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    # 设置图表标题和标签
    ax.set_title("Backtest Results: Simple Moving Average Strategy")
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity ($)")
    ax.grid(True)

    # 显示图表
    plt.tight_layout()
    plt.savefig("backtest_results.png")
    logger.info("回测结果图表已保存为 backtest_results.png")


def main():
    """主函数"""
    # 初始化数据库
    db_url = "sqlite:///lightquant.db"
    db_manager = DatabaseManager(db_url)
    init_db(db_manager.engine)

    # 创建仓库
    strategy_repo = SQLStrategyRepository(db_manager.session_factory)
    order_repo = SQLOrderRepository(db_manager.session_factory)
    account_repo = SQLAccountRepository(db_manager.session_factory)
    market_data_repo = SQLMarketDataRepository(db_manager.session_factory)

    # 创建服务
    market_data_service = MockMarketDataService(market_data_repo)
    order_service = OrderService(order_repo)
    strategy_service = StrategyService(strategy_repo, order_repo)

    # 生成模拟数据
    symbol = "BTC/USDT"
    timeframe = "1h"
    start_time = datetime(2023, 1, 1)
    end_time = datetime(2023, 3, 31)

    mock_candles = generate_mock_candles(
        symbol=symbol, timeframe=timeframe, start_time=start_time, end_time=end_time
    )

    # 添加模拟数据
    market_data_service.add_mock_candles(symbol, timeframe, mock_candles)

    # 创建回测引擎
    backtest_engine = BacktestEngine(
        strategy_service=strategy_service,
        order_service=order_service,
        market_data_service=market_data_service,
        account_repository=account_repo,
    )

    # 设置回测参数
    backtest_engine.set_initial_capital(10000.0)  # 初始资金
    backtest_engine.set_commission_rate(0.001)  # 手续费率
    backtest_engine.set_slippage(0.0005)  # 滑点

    # 注册策略类
    backtest_engine.register_strategy_class(SimpleMovingAverageStrategy)

    # 创建策略配置
    config = StrategyConfig(
        name="简单移动平均线策略",
        symbols=[symbol],
        exchange_ids=["binance"],
        timeframes=[timeframe],
        params={"short_window": 5, "long_window": 20},
    )

    # 创建策略
    strategy_id = backtest_engine.create_strategy(
        strategy_class=SimpleMovingAverageStrategy, config=config
    )

    if not strategy_id:
        logger.error("创建策略失败")
        return

    logger.info(f"创建策略成功: {strategy_id}")

    # 运行回测
    backtest_results = backtest_engine.run_backtest(
        strategy_id=strategy_id, start_time=start_time, end_time=end_time
    )

    # 打印回测结果
    metrics = backtest_results["performance_metrics"]
    logger.info("回测结果:")
    logger.info(f"初始资金: ${metrics['initial_capital']:.2f}")
    logger.info(f"最终权益: ${metrics['final_equity']:.2f}")
    logger.info(f"总收益率: {metrics['total_return']:.2%}")
    logger.info(f"年化收益率: {metrics['annual_return']:.2%}")
    logger.info(f"最大回撤: {metrics['max_drawdown']:.2%}")
    logger.info(f"夏普比率: {metrics['sharpe_ratio']:.2f}")
    logger.info(f"胜率: {metrics['win_rate']:.2%}")
    logger.info(f"总交易次数: {metrics['total_trades']}")
    logger.info(f"盈利交易次数: {metrics['winning_trades']}")
    logger.info(f"亏损交易次数: {metrics['losing_trades']}")

    # 绘制回测结果
    plot_backtest_results(backtest_results)


if __name__ == "__main__":
    main()
