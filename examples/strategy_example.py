"""
策略示例，展示如何使用策略引擎
"""

import logging
import time
from datetime import datetime, timedelta

from lightquant.domain.models.market_data import Candle
from lightquant.domain.models.order import OrderSide
from lightquant.domain.models.strategy import StrategyConfig
from lightquant.domain.repositories.account_repository import AccountRepository
from lightquant.domain.repositories.market_data_repository import MarketDataRepository
from lightquant.domain.repositories.order_repository import OrderRepository
from lightquant.domain.repositories.strategy_repository import StrategyRepository
from lightquant.domain.services.market_data_service import MarketDataService
from lightquant.domain.services.order_service import OrderService
from lightquant.domain.services.strategy_service import StrategyService
from lightquant.domain.strategies import BaseStrategy, StrategyResult
from lightquant.domain.strategies.strategy_engine import StrategyEngine
from lightquant.infrastructure.database import DatabaseManager, init_db
from lightquant.infrastructure.database.repositories import (
    SQLAccountRepository,
    SQLMarketDataRepository,
    SQLOrderRepository,
    SQLStrategyRepository,
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
    market_data_service = MarketDataService(market_data_repo)
    order_service = OrderService(order_repo)
    strategy_service = StrategyService(strategy_repo, order_repo)

    # 创建策略引擎
    strategy_engine = StrategyEngine(
        strategy_service=strategy_service,
        order_service=order_service,
        market_data_service=market_data_service,
        account_repository=account_repo,
    )

    # 注册策略类
    strategy_engine.register_strategy_class(SimpleMovingAverageStrategy)

    # 创建策略配置
    config = StrategyConfig(
        name="简单移动平均线策略",
        symbols=["BTC/USDT"],
        exchange_ids=["binance"],
        timeframes=["1h"],
        params={"short_window": 5, "long_window": 20},
    )

    # 创建策略
    strategy_id = strategy_engine.create_strategy(
        strategy_class=SimpleMovingAverageStrategy, config=config
    )

    if not strategy_id:
        logger.error("创建策略失败")
        return

    logger.info(f"创建策略成功: {strategy_id}")

    # 启动策略引擎
    strategy_engine.start()

    # 启动策略
    if strategy_engine.start_strategy(strategy_id):
        logger.info(f"启动策略成功: {strategy_id}")
    else:
        logger.error(f"启动策略失败: {strategy_id}")
        return

    try:
        # 模拟接收市场数据
        start_time = datetime.utcnow() - timedelta(hours=24)

        for i in range(100):
            # 创建模拟K线
            candle = Candle(
                symbol="BTC/USDT",
                timeframe="1h",
                timestamp=start_time + timedelta(hours=i),
                open=10000 + i * 10,
                high=10100 + i * 10,
                low=9900 + i * 10,
                close=10050 + i * 10 * (1 if i % 3 == 0 else -1),  # 模拟价格波动
                volume=1.0 + i * 0.1,
            )

            # 处理K线
            strategy_engine.process_candle(candle)

            # 暂停一下，模拟实时数据
            time.sleep(0.1)

    except KeyboardInterrupt:
        logger.info("用户中断")

    finally:
        # 停止策略
        strategy_engine.stop_strategy(strategy_id)

        # 停止策略引擎
        strategy_engine.stop()

        logger.info("程序结束")


if __name__ == "__main__":
    main()
