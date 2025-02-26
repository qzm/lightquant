"""
带风险管理的回测示例

本示例展示如何在回测中集成风险管理功能，控制交易风险。
"""

import logging
import time
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

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
from lightquant.domain.risk_management import (
    PositionSizeRule,
    MaxDrawdownRule,
    MaxTradesPerDayRule,
)
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


class RiskAwareMovingAverageStrategy(BaseStrategy):
    """
    带风险管理的移动平均线策略

    策略逻辑：
    1. 计算短期和长期移动平均线
    2. 当短期均线上穿长期均线时买入
    3. 当短期均线下穿长期均线时卖出
    4. 使用风险管理规则控制交易风险
    """

    def initialize(self) -> None:
        """初始化策略"""
        # 获取策略参数
        self.symbol = self.config.symbols[0]  # 交易对
        self.short_window = self.parameters.get("short_window", 5)  # 短期窗口
        self.long_window = self.parameters.get("long_window", 20)  # 长期窗口
        self.position_size = self.parameters.get("position_size", 0.01)  # 仓位大小

        # 获取历史数据
        self.candles = self.context.get_historical_candles(
            symbol=self.symbol, timeframe="1h", limit=self.long_window + 10
        )

        # 初始化指标
        self.short_ma = 0
        self.long_ma = 0
        self.position = 0  # 持仓状态：1表示多头，-1表示空头，0表示无持仓

        # 设置风险管理规则
        self._setup_risk_rules()

        logger.info(
            f"初始化策略: {self.config.name}, 交易对: {self.symbol}, "
            f"短期窗口: {self.short_window}, 长期窗口: {self.long_window}"
        )

    def _setup_risk_rules(self) -> None:
        """设置风险管理规则"""
        if not self.context or not self.context.risk_manager:
            logger.warning("风险管理器不可用")
            return

        # 添加仓位大小规则
        position_rule = PositionSizeRule(
            max_position_value=1000.0,  # 最大仓位价值1000 USDT
            max_position_percentage=5.0,  # 最大仓位占账户权益的5%
            max_position_amount=0.05,  # 最大仓位数量0.05 BTC
        )
        self.context.risk_manager.add_rule(position_rule)

        # 添加最大回撤规则
        drawdown_rule = MaxDrawdownRule(max_drawdown_percentage=10.0)  # 最大回撤10%
        self.context.risk_manager.add_rule(drawdown_rule)

        # 添加每日最大交易次数规则
        trades_rule = MaxTradesPerDayRule(max_trades=5)  # 每日最多5笔交易
        self.context.risk_manager.add_rule(trades_rule)

        logger.info("设置风险管理规则完成")

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

        # 计算当前回撤
        if len(self.candles) > 30:  # 至少需要30根K线才能计算回撤
            highest_close = max([c.close for c in self.candles[-30:]])
            current_close = candle.close
            if highest_close > 0:
                drawdown = (highest_close - current_close) / highest_close * 100
                result.add_metric("drawdown", drawdown)

                # 更新风险管理器上下文
                if self.context and self.context.risk_manager:
                    self.context.risk_manager.update_context({"drawdown": drawdown})

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
                    symbol=self.symbol, side=OrderSide.BUY, amount=self.position_size
                )

                if order:
                    result.add_order(order)
                    self.position = 1
                    result.add_log(f"创建买入订单: {order.id}")
                else:
                    result.add_log("创建买入订单失败，可能被风险管理规则拒绝")

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
                    symbol=self.symbol, side=OrderSide.SELL, amount=self.position_size
                )

                if order:
                    result.add_order(order)
                    self.position = -1
                    result.add_log(f"创建卖出订单: {order.id}")
                else:
                    result.add_log("创建卖出订单失败，可能被风险管理规则拒绝")

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

    # 生成随机价格序列
    np.random.seed(42)  # 固定随机种子，使结果可重现

    # 初始价格
    price = 10000.0

    # 价格波动参数
    volatility = 0.01  # 波动率
    trend = 0.0001  # 趋势

    while current_time <= end_time:
        # 生成随机价格变动
        price_change = np.random.normal(trend, volatility)
        price *= 1 + price_change

        # 生成高低价
        high = price * (1 + np.random.uniform(0, 0.005))
        low = price * (1 - np.random.uniform(0, 0.005))

        # 确保价格合理
        if high < price:
            high = price
        if low > price:
            low = price

        # 生成成交量
        volume = np.random.uniform(1, 10)

        # 创建K线
        candle = Candle(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=current_time,
            open=price * (1 - price_change),  # 开盘价
            high=high,
            low=low,
            close=price,  # 收盘价
            volume=volume,
        )

        candles.append(candle)

        # 更新时间
        current_time += timedelta(minutes=interval_minutes)

    return candles


class MockMarketDataService(MarketDataService):
    """模拟市场数据服务，用于回测"""

    def __init__(self, repository: MarketDataRepository):
        """初始化模拟市场数据服务"""
        super().__init__(repository)
        self.mock_candles: Dict[str, Dict[str, List[Candle]]] = (
            {}
        )  # symbol -> timeframe -> candles

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


def plot_backtest_results(
    backtest_results: Dict[str, Any], with_risk: bool = True
) -> None:
    """
    绘制回测结果

    Args:
        backtest_results: 回测结果
        with_risk: 是否使用风险管理
    """
    # 创建图表
    fig, axes = plt.subplots(
        3, 1, figsize=(12, 16), gridspec_kw={"height_ratios": [3, 1, 1]}
    )

    # 绘制权益曲线
    equity_curve = backtest_results["equity_curve"]
    dates = [ec[0] for ec in equity_curve]
    equity = [ec[1] for ec in equity_curve]

    axes[0].plot(dates, equity, label="账户权益")
    axes[0].set_title("账户权益曲线")
    axes[0].set_xlabel("日期")
    axes[0].set_ylabel("权益 (USDT)")
    axes[0].legend()
    axes[0].grid(True)

    # 绘制回撤
    drawdowns = backtest_results["drawdowns"]
    dd_dates = [dd[0] for dd in drawdowns]
    dd_values = [dd[1] for dd in drawdowns]

    axes[1].plot(dd_dates, dd_values, color="red", label="回撤 (%)")
    axes[1].set_title("回撤曲线")
    axes[1].set_xlabel("日期")
    axes[1].set_ylabel("回撤 (%)")
    axes[1].legend()
    axes[1].grid(True)

    # 绘制交易次数
    trades_per_day = backtest_results.get("trades_per_day", [])
    if trades_per_day:
        trade_dates = [t[0] for t in trades_per_day]
        trade_counts = [t[1] for t in trades_per_day]

        axes[2].bar(trade_dates, trade_counts, color="green", label="每日交易次数")
        axes[2].set_title("每日交易次数")
        axes[2].set_xlabel("日期")
        axes[2].set_ylabel("交易次数")
        axes[2].legend()
        axes[2].grid(True)

    # 添加性能指标文本
    metrics = backtest_results["metrics"]
    metrics_text = (
        f"总收益: {metrics['total_return']:.2f}%\n"
        f"年化收益: {metrics['annual_return']:.2f}%\n"
        f"最大回撤: {metrics['max_drawdown']:.2f}%\n"
        f"夏普比率: {metrics['sharpe_ratio']:.2f}\n"
        f"交易次数: {metrics['total_trades']}\n"
        f"胜率: {metrics['win_rate']:.2f}%\n"
        f"盈亏比: {metrics['profit_factor']:.2f}\n"
        f"风险管理: {'启用' if with_risk else '禁用'}"
    )

    plt.figtext(
        0.15, 0.01, metrics_text, fontsize=12, bbox=dict(facecolor="white", alpha=0.8)
    )

    # 调整布局
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    plt.subplots_adjust(hspace=0.3)

    # 设置标题
    strategy_name = (
        "带风险管理的移动平均线策略" if with_risk else "移动平均线策略（无风险管理）"
    )
    fig.suptitle(f"回测结果: {strategy_name}", fontsize=16)

    # 保存图表
    filename = f"backtest_results_{'with_risk' if with_risk else 'no_risk'}.png"
    plt.savefig(filename)
    logger.info(f"回测结果图表已保存到: {filename}")

    # 显示图表
    plt.show()


def run_backtest(with_risk: bool = True) -> Dict[str, Any]:
    """
    运行回测

    Args:
        with_risk: 是否使用风险管理

    Returns:
        回测结果
    """
    # 初始化数据库
    db_url = "sqlite:///lightquant.db"
    db_manager = DatabaseManager(db_url)
    init_db(db_manager.engine)

    # 创建仓库
    strategy_repo = SQLStrategyRepository(db_manager.session_factory)
    order_repo = SQLOrderRepository(db_manager.session_factory)
    account_repo = SQLAccountRepository(db_manager.session_factory)
    market_data_repo = SQLMarketDataRepository(db_manager.session_factory)

    # 创建模拟市场数据服务
    market_data_service = MockMarketDataService(market_data_repo)

    # 创建其他服务
    order_service = OrderService(order_repo)
    strategy_service = StrategyService(strategy_repo, order_repo)

    # 创建回测引擎
    backtest_engine = BacktestEngine(
        strategy_service=strategy_service,
        order_service=order_service,
        market_data_service=market_data_service,
        account_repository=account_repo,
    )

    # 设置回测参数
    backtest_engine.set_initial_capital(10000.0)  # 初始资金10000 USDT
    backtest_engine.set_commission_rate(0.001)  # 手续费率0.1%
    backtest_engine.set_slippage(0.0005)  # 滑点0.05%

    # 生成模拟数据
    start_time = datetime(2023, 1, 1)
    end_time = datetime(2023, 3, 31)
    symbol = "BTC/USDT"
    timeframe = "1h"

    candles = generate_mock_candles(
        symbol=symbol, timeframe=timeframe, start_time=start_time, end_time=end_time
    )

    # 添加模拟数据
    market_data_service.add_mock_candles(symbol, timeframe, candles)

    # 创建策略配置
    config = StrategyConfig(
        name=(
            "带风险管理的移动平均线策略"
            if with_risk
            else "移动平均线策略（无风险管理）"
        ),
        symbols=[symbol],
        exchange_ids=["binance"],
        timeframes=[timeframe],
        params={"short_window": 5, "long_window": 20, "position_size": 0.01},
    )

    # 创建策略
    strategy_id = backtest_engine.create_strategy(
        strategy_class=RiskAwareMovingAverageStrategy, config=config
    )

    if not strategy_id:
        logger.error("创建策略失败")
        return {}

    logger.info(f"创建策略成功: {strategy_id}")

    # 如果不使用风险管理，禁用风险管理器
    if not with_risk and backtest_engine.risk_manager:
        backtest_engine.risk_manager = None
        logger.info("已禁用风险管理")

    # 运行回测
    backtest_results = backtest_engine.run_backtest(
        strategy_id=strategy_id, start_time=start_time, end_time=end_time
    )

    # 计算每日交易次数
    orders = backtest_engine.get_orders()
    trades_per_day = {}

    for order in orders:
        if order.created_at:
            date_str = order.created_at.date().isoformat()
            trades_per_day[date_str] = trades_per_day.get(date_str, 0) + 1

    backtest_results["trades_per_day"] = [
        (datetime.fromisoformat(date), count) for date, count in trades_per_day.items()
    ]

    # 计算回撤序列
    equity_curve = backtest_results["equity_curve"]
    drawdowns = []

    peak = equity_curve[0][1]
    for date, equity in equity_curve:
        if equity > peak:
            peak = equity

        if peak > 0:
            drawdown = (peak - equity) / peak * 100
        else:
            drawdown = 0

        drawdowns.append((date, drawdown))

    backtest_results["drawdowns"] = drawdowns

    return backtest_results


def main():
    """主函数"""
    logger.info("开始带风险管理的回测示例")

    # 运行带风险管理的回测
    logger.info("运行带风险管理的回测...")
    with_risk_results = run_backtest(with_risk=True)

    # 运行不带风险管理的回测
    logger.info("运行不带风险管理的回测...")
    no_risk_results = run_backtest(with_risk=False)

    # 绘制回测结果
    if with_risk_results:
        logger.info("绘制带风险管理的回测结果...")
        plot_backtest_results(with_risk_results, with_risk=True)

    if no_risk_results:
        logger.info("绘制不带风险管理的回测结果...")
        plot_backtest_results(no_risk_results, with_risk=False)

    # 比较结果
    if with_risk_results and no_risk_results:
        with_risk_metrics = with_risk_results["metrics"]
        no_risk_metrics = no_risk_results["metrics"]

        logger.info("=== 回测结果比较 ===")
        logger.info(
            f"总收益: 带风险管理={with_risk_metrics['total_return']:.2f}%, 无风险管理={no_risk_metrics['total_return']:.2f}%"
        )
        logger.info(
            f"最大回撤: 带风险管理={with_risk_metrics['max_drawdown']:.2f}%, 无风险管理={no_risk_metrics['max_drawdown']:.2f}%"
        )
        logger.info(
            f"夏普比率: 带风险管理={with_risk_metrics['sharpe_ratio']:.2f}, 无风险管理={no_risk_metrics['sharpe_ratio']:.2f}"
        )
        logger.info(
            f"交易次数: 带风险管理={with_risk_metrics['total_trades']}, 无风险管理={no_risk_metrics['total_trades']}"
        )

    logger.info("回测示例完成")


if __name__ == "__main__":
    main()
