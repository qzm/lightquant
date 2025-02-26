"""
数据库使用示例
"""

import os
from datetime import datetime, timedelta

from lightquant.domain.models.order import Order, OrderParams, OrderType, OrderSide
from lightquant.domain.models.account import Account, Balance
from lightquant.domain.models.strategy import Strategy, StrategyConfig, StrategyStatus
from lightquant.domain.models.market_data import (
    Ticker,
    Candle,
    OrderBook,
    OrderBookEntry,
)

from lightquant.infrastructure.database import (
    DatabaseManager,
    SQLOrderRepository,
    SQLAccountRepository,
    SQLStrategyRepository,
    SQLMarketDataRepository,
)
from lightquant.infrastructure.database.init_db import init_database


def main():
    # 初始化数据库
    connection_string = os.environ.get(
        "DATABASE_URL", "sqlite:///lightquant_example.db"
    )
    init_database(connection_string, drop_all=True)

    # 创建数据库管理器
    db_manager = DatabaseManager(connection_string)

    # 创建仓库
    order_repo = SQLOrderRepository(db_manager)
    account_repo = SQLAccountRepository(db_manager)
    strategy_repo = SQLStrategyRepository(db_manager)
    market_data_repo = SQLMarketDataRepository(db_manager)

    # 创建并保存订单
    print("\n创建订单...")
    order_params = OrderParams(
        symbol="BTC/USDT",
        order_type=OrderType.LIMIT,
        side=OrderSide.BUY,
        amount=0.01,
        price=20000.0,
    )
    order = Order(
        params=order_params, strategy_id="test_strategy", exchange_id="binance"
    )
    order_repo.save(order)
    print(f"订单已保存: {order.id}")

    # 查询订单
    retrieved_order = order_repo.find_by_id(order.id)
    print(
        f"查询订单: {retrieved_order.id}, 交易对: {retrieved_order.params.symbol}, 价格: {retrieved_order.params.price}"
    )

    # 创建并保存账户
    print("\n创建账户...")
    account = Account(
        exchange_id="binance",
        balances={
            "BTC": Balance(currency="BTC", free=1.0, used=0.0, total=1.0),
            "USDT": Balance(currency="USDT", free=10000.0, used=0.0, total=10000.0),
        },
    )
    account_repo.save(account)
    print(f"账户已保存: {account.id}")

    # 查询账户
    retrieved_account = account_repo.find_by_exchange_id("binance")
    print(f"查询账户: {retrieved_account.id}, 交易所: {retrieved_account.exchange_id}")
    for currency, balance in retrieved_account.balances.items():
        print(
            f"  {currency}: 可用: {balance.free}, 冻结: {balance.used}, 总计: {balance.total}"
        )

    # 创建并保存策略
    print("\n创建策略...")
    strategy_config = StrategyConfig(
        name="移动平均线策略",
        symbols=["BTC/USDT", "ETH/USDT"],
        exchange_ids=["binance"],
        timeframes=["1h", "4h"],
        params={"short_window": 5, "long_window": 20},
    )
    strategy = Strategy(config=strategy_config)
    strategy.start()  # 将状态设置为RUNNING
    strategy_repo.save(strategy)
    print(f"策略已保存: {strategy.id}")

    # 查询策略
    retrieved_strategy = strategy_repo.find_by_id(strategy.id)
    print(
        f"查询策略: {retrieved_strategy.id}, 名称: {retrieved_strategy.config.name}, 状态: {retrieved_strategy.status}"
    )
    print(f"  交易对: {retrieved_strategy.config.symbols}")
    print(f"  参数: {retrieved_strategy.config.params}")

    # 创建并保存市场数据
    print("\n创建市场数据...")

    # 行情
    ticker = Ticker(
        symbol="BTC/USDT",
        exchange_id="binance",
        bid=19990.0,
        ask=20010.0,
        last=20000.0,
        high=20100.0,
        low=19900.0,
        volume=100.0,
        quote_volume=2000000.0,
        timestamp=datetime.utcnow(),
    )
    market_data_repo.save_ticker(ticker)
    print(f"行情已保存: {ticker.symbol}, 最新价: {ticker.last}")

    # K线
    candles = []
    now = datetime.utcnow()
    for i in range(10):
        candle_time = now - timedelta(hours=i)
        candle = Candle(
            symbol="BTC/USDT",
            exchange_id="binance",
            timeframe="1h",
            timestamp=candle_time,
            open=20000.0 - i * 10,
            high=20050.0 - i * 10,
            low=19950.0 - i * 10,
            close=20000.0 - i * 10 + 5,
            volume=100.0 + i * 5,
        )
        candles.append(candle)
    market_data_repo.save_candles(candles)
    print(f"K线已保存: {len(candles)}根")

    # 订单簿
    bids = [
        OrderBookEntry(price=19990.0 - i * 10, amount=1.0 + i * 0.1) for i in range(10)
    ]
    asks = [
        OrderBookEntry(price=20010.0 + i * 10, amount=1.0 + i * 0.1) for i in range(10)
    ]
    order_book = OrderBook(
        symbol="BTC/USDT",
        exchange_id="binance",
        timestamp=datetime.utcnow(),
        bids=bids,
        asks=asks,
    )
    market_data_repo.save_order_book(order_book)
    print(
        f"订单簿已保存: {order_book.symbol}, 买一价: {order_book.bids[0].price}, 卖一价: {order_book.asks[0].price}"
    )

    # 查询市场数据
    print("\n查询市场数据...")

    # 查询行情
    retrieved_ticker = market_data_repo.get_ticker("BTC/USDT", "binance")
    print(
        f"查询行情: {retrieved_ticker.symbol}, 最新价: {retrieved_ticker.last}, 时间: {retrieved_ticker.timestamp}"
    )

    # 查询K线
    retrieved_candles = market_data_repo.get_candles(
        "BTC/USDT", "binance", "1h", limit=5
    )
    print(f"查询K线: {len(retrieved_candles)}根")
    for i, candle in enumerate(retrieved_candles):
        print(
            f"  {i+1}. 时间: {candle.timestamp}, 开: {candle.open}, 高: {candle.high}, 低: {candle.low}, 收: {candle.close}"
        )

    # 查询订单簿
    retrieved_order_book = market_data_repo.get_order_book("BTC/USDT", "binance")
    print(
        f"查询订单簿: {retrieved_order_book.symbol}, 买一价: {retrieved_order_book.bids[0].price}, 卖一价: {retrieved_order_book.asks[0].price}"
    )

    print("\n示例完成！")


if __name__ == "__main__":
    main()
