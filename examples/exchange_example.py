"""
交易所适配器使用示例
"""

import asyncio
import os
from datetime import datetime, timedelta

from lightquant.domain.models.order import Order, OrderSide, OrderType
from lightquant.infrastructure.exchanges import ExchangeFactory


async def main():
    # 从环境变量获取API密钥（实际使用时应该从配置文件或安全存储中获取）
    api_key = os.environ.get("BINANCE_API_KEY", "")
    api_secret = os.environ.get("BINANCE_API_SECRET", "")

    # 创建交易所适配器
    exchange = ExchangeFactory.create_adapter("binance", api_key, api_secret)
    if not exchange:
        print("创建交易所适配器失败")
        return

    # 获取支持的交易所列表
    supported_exchanges = ExchangeFactory.get_supported_exchanges()
    print(f"支持的交易所: {supported_exchanges}")

    # 获取行情
    symbol = "BTC/USDT"
    print(f"\n获取{symbol}行情...")
    ticker = await exchange.fetch_ticker(symbol)
    if ticker:
        print(f"最新价格: {ticker.last}")
        print(f"买一价: {ticker.bid}, 卖一价: {ticker.ask}")
        print(f"24小时成交量: {ticker.volume}")

    # 获取订单簿
    print(f"\n获取{symbol}订单簿...")
    order_book = await exchange.fetch_order_book(symbol, 5)
    if order_book:
        print("买单:")
        for i, bid in enumerate(order_book.bids[:5]):
            print(f"  {i+1}. 价格: {bid.price}, 数量: {bid.amount}")

        print("卖单:")
        for i, ask in enumerate(order_book.asks[:5]):
            print(f"  {i+1}. 价格: {ask.price}, 数量: {ask.amount}")

    # 获取K线数据
    print(f"\n获取{symbol}最近5根1小时K线...")
    since = datetime.now() - timedelta(hours=5)
    candles = await exchange.fetch_candles(symbol, "1h", since, 5)
    for i, candle in enumerate(candles):
        print(
            f"  {i+1}. 时间: {candle.timestamp}, 开: {candle.open}, 高: {candle.high}, 低: {candle.low}, 收: {candle.close}, 量: {candle.volume}"
        )

    # 如果有API密钥，则获取账户余额
    if api_key and api_secret:
        print("\n获取账户余额...")
        balances = await exchange.fetch_balance()
        for currency, balance in balances.items():
            if balance.total > 0:
                print(
                    f"  {currency}: 可用: {balance.free}, 冻结: {balance.used}, 总计: {balance.total}"
                )

        # 创建订单（注意：这里只是示例，不会真正下单）
        print("\n创建订单示例（不会真正下单）...")
        order = Order(
            symbol=symbol,
            type=OrderType.LIMIT,
            side=OrderSide.BUY,
            amount=0.001,
            price=ticker.last * 0.95 if ticker else 20000,
            client_order_id="test_order_123",
        )
        print(
            f"订单参数: 交易对={order.symbol}, 类型={order.type}, 方向={order.side}, 数量={order.amount}, 价格={order.price}"
        )

        # 实际使用时取消下面的注释
        # success, order_id, error = await exchange.create_order(order)
        # if success:
        #     print(f"下单成功，订单ID: {order_id}")
        #
        #     # 更新订单的交易所ID
        #     order.exchange_order_id = order_id
        #
        #     # 获取订单状态
        #     success, status, filled, avg_price, error = await exchange.fetch_order(order)
        #     if success:
        #         print(f"订单状态: {status}, 已成交: {filled}, 成交均价: {avg_price}")
        #
        #     # 取消订单
        #     success, error = await exchange.cancel_order(order)
        #     if success:
        #         print("取消订单成功")
        #     else:
        #         print(f"取消订单失败: {error}")
        # else:
        #     print(f"下单失败: {error}")

    # 关闭交易所连接
    if hasattr(exchange, "_exchange") and hasattr(exchange._exchange, "close"):
        await exchange._exchange.close()


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
