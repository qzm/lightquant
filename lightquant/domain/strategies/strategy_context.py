"""
策略上下文，提供策略运行时的环境和服务
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.account import Account
from ..models.market_data import Candle, OrderBook, Ticker
from ..models.order import Order, OrderSide, OrderType
from ..risk_management import RiskManager
from ..services.market_data_service import MarketDataService
from ..services.order_service import OrderService


class StrategyContext:
    """
    策略上下文，提供策略运行时的环境和服务

    策略上下文包含：
    1. 订单服务：用于创建、取消订单
    2. 市场数据服务：用于获取历史数据
    3. 账户信息：用于获取账户余额
    4. 市场数据缓存：用于缓存最新的市场数据
    5. 运行时信息：如当前时间、运行模式等
    6. 风险管理器：用于控制交易风险
    """

    def __init__(
        self,
        strategy_id: str,
        order_service: OrderService,
        market_data_service: MarketDataService,
        account: Account,
        risk_manager: Optional[RiskManager] = None,
        is_backtest: bool = False,
    ):
        """
        初始化策略上下文

        Args:
            strategy_id: 策略ID
            order_service: 订单服务
            market_data_service: 市场数据服务
            account: 账户对象
            risk_manager: 风险管理器
            is_backtest: 是否为回测模式
        """
        self.strategy_id = strategy_id
        self.order_service = order_service
        self.market_data_service = market_data_service
        self.account = account
        self.risk_manager = risk_manager
        self.is_backtest = is_backtest

        # 市场数据缓存
        self.candles: Dict[str, Dict[str, List[Candle]]] = (
            {}
        )  # symbol -> timeframe -> candles
        self.tickers: Dict[str, Ticker] = {}  # symbol -> ticker
        self.orderbooks: Dict[str, OrderBook] = {}  # symbol -> orderbook

        # 运行时信息
        self.current_time: datetime = datetime.utcnow()
        self.orders: Dict[str, Order] = {}  # order_id -> order

        # 性能指标
        self.performance_metrics: Dict[str, Any] = {}

    def create_order(
        self,
        symbol: str,
        order_type: OrderType,
        side: OrderSide,
        amount: float,
        price: Optional[float] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Order]:
        """
        创建订单

        Args:
            symbol: 交易对
            order_type: 订单类型
            side: 订单方向
            amount: 数量
            price: 价格，市价单可为None
            params: 额外参数

        Returns:
            创建的订单，如果创建失败则返回None
        """
        import logging

        logger = logging.getLogger(__name__)

        order = self.order_service.create_order(
            strategy_id=self.strategy_id,
            symbol=symbol,
            order_type=order_type,
            side=side,
            amount=amount,
            price=price,
            params=params or {},
        )

        if order:
            # 进行风险检查
            if self.risk_manager and not self.risk_manager.check_order(
                order, self.account
            ):
                logger.warning(
                    f"订单被风险管理器拒绝: 策略ID={self.strategy_id}, 订单ID={order.id}, 交易对={symbol}, 方向={side}, 数量={amount}"
                )
                return None

            self.orders[order.id] = order
            logger.info(
                f"订单已创建: 策略ID={self.strategy_id}, 订单ID={order.id}, 交易对={symbol}, 方向={side}, 数量={amount}"
            )
        else:
            logger.error(
                f"创建订单失败: 策略ID={self.strategy_id}, 交易对={symbol}, 方向={side}, 数量={amount}"
            )

        return order

    def cancel_order(self, order_id: str) -> bool:
        """
        取消订单

        Args:
            order_id: 订单ID

        Returns:
            是否成功取消
        """
        result = self.order_service.cancel_order(order_id)

        if result and order_id in self.orders:
            # 更新本地订单状态
            self.orders[order_id].cancel()

        return result

    def get_historical_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[Candle]:
        """
        获取历史K线数据

        Args:
            symbol: 交易对
            timeframe: 时间周期
            limit: 获取数量
            since: 开始时间

        Returns:
            K线数据列表
        """
        return self.market_data_service.get_historical_candles(
            symbol=symbol, timeframe=timeframe, limit=limit, since=since
        )

    def get_ticker(self, symbol: str) -> Optional[Ticker]:
        """
        获取最新Ticker

        Args:
            symbol: 交易对

        Returns:
            Ticker对象，如果不存在则返回None
        """
        if symbol in self.tickers:
            return self.tickers[symbol]

        return self.market_data_service.get_ticker(symbol)

    def get_orderbook(self, symbol: str, limit: int = 20) -> Optional[OrderBook]:
        """
        获取最新订单簿

        Args:
            symbol: 交易对
            limit: 获取深度

        Returns:
            订单簿对象，如果不存在则返回None
        """
        if symbol in self.orderbooks:
            return self.orderbooks[symbol]

        return self.market_data_service.get_orderbook(symbol, limit)

    def update_candle(self, candle: Candle) -> None:
        """
        更新K线缓存

        Args:
            candle: K线数据
        """
        symbol = candle.symbol
        timeframe = candle.timeframe

        if symbol not in self.candles:
            self.candles[symbol] = {}

        if timeframe not in self.candles[symbol]:
            self.candles[symbol][timeframe] = []

        # 添加或更新K线
        candles = self.candles[symbol][timeframe]

        # 如果是最新K线的更新，则替换
        if candles and candles[-1].timestamp == candle.timestamp:
            candles[-1] = candle
        else:
            candles.append(candle)

            # 限制缓存大小
            if len(candles) > 1000:
                self.candles[symbol][timeframe] = candles[-1000:]

    def update_ticker(self, ticker: Ticker) -> None:
        """
        更新Ticker缓存

        Args:
            ticker: Ticker数据
        """
        self.tickers[ticker.symbol] = ticker

    def update_orderbook(self, orderbook: OrderBook) -> None:
        """
        更新订单簿缓存

        Args:
            orderbook: 订单簿数据
        """
        self.orderbooks[orderbook.symbol] = orderbook

    def update_order(self, order: Order) -> None:
        """
        更新订单缓存

        Args:
            order: 订单对象
        """
        self.orders[order.id] = order

    def update_current_time(self, time: datetime) -> None:
        """
        更新当前时间

        Args:
            time: 当前时间
        """
        self.current_time = time

    def update_performance_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        更新性能指标

        Args:
            metrics: 性能指标
        """
        self.performance_metrics.update(metrics)
