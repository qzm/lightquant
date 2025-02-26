# 交易所适配器模块

本模块提供了与各大数字货币交易所交互的统一接口，基于CCXT库实现。

## 主要组件

- `ExchangeAdapter`: 交易所适配器基类，定义了与交易所交互的统一接口
- `BinanceAdapter`: 币安交易所适配器实现
- `ExchangeFactory`: 交易所适配器工厂，负责创建和管理交易所适配器实例

## 使用示例

```python
import asyncio
from lightquant.infrastructure.exchanges import ExchangeFactory

async def main():
    # 创建交易所适配器
    exchange = ExchangeFactory.create_adapter(
        "binance",
        api_key="你的API密钥",
        api_secret="你的API密钥"
    )

    # 获取行情
    ticker = await exchange.fetch_ticker("BTC/USDT")
    print(f"BTC/USDT 最新价格: {ticker.last}")

    # 获取订单簿
    order_book = await exchange.fetch_order_book("BTC/USDT", 5)
    print(f"买一价: {order_book.bids[0].price}, 卖一价: {order_book.asks[0].price}")

    # 关闭交易所连接
    await exchange._exchange.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## 支持的交易所

目前支持以下交易所：

- Binance (币安)

计划支持的交易所：

- OKEx
- Huobi (火币)

## 扩展支持的交易所

要添加新的交易所支持，需要：

1. 创建一个继承自`ExchangeAdapter`的新适配器类
2. 实现所有抽象方法
3. 在`ExchangeFactory`中注册新的适配器

示例：

```python
from lightquant.infrastructure.exchanges import ExchangeAdapter, ExchangeFactory

class MyExchangeAdapter(ExchangeAdapter):
    # 实现所有抽象方法
    ...

# 注册新的适配器
ExchangeFactory.register_adapter("myexchange", MyExchangeAdapter)

# 使用新的适配器
exchange = ExchangeFactory.create_adapter("myexchange", api_key, api_secret)
```
